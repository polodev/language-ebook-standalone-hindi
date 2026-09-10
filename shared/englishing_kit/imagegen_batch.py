"""OpenAI Batch API for image generation — 50% cheaper, and you can walk away.

Mirrors the push/pull flow already proven in ~/sites/image-management:

    push  →  build JSONL  →  upload to Files API  →  create batch  →  record batch_id
    ( wait ~20 min. The session can end. Nothing needs to stay running. )
    pull  →  poll batch   →  download output JSONL →  decode base64 → write PNGs + manifest

The whole point is the **tracking file**, `assets/image-batch.json`. It holds the batch id,
the file ids, and the full spec of every request. A completely different session — a
different model, days later — can run `--pull` and finish the job, because everything
needed to reconstruct the images is on disk. Nothing lives only in memory.

Batch is used automatically when a course needs more than `BATCH_THRESHOLD` images.
Below that, the wait is not worth it and the synchronous path runs.

Verified: `gpt-image-2` IS accepted on `/v1/images/generations` batches.
"""
from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from . import config
from .imagegen import ImageSpec, build_prompt, check_required_roles, image_dir_for

# More images than this and the 50% saving is worth a 20-minute wait.
BATCH_THRESHOLD = 20
ENDPOINT = "/v1/images/generations"
TRACKING_FILE = "assets/image-batch.json"

# Practical wait. The API window is 24h, but image batches usually land far sooner.
TYPICAL_WAIT_MINUTES = 20


def tracking_path(course_dir: Path) -> Path:
    return course_dir / TRACKING_FILE


def load_tracking(course_dir: Path) -> dict[str, Any] | None:
    p = tracking_path(course_dir)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _client():
    from openai import OpenAI
    return OpenAI(api_key=config.require_openai_key())


# ────────────────────────────────────────────────────────────── push

def push(specs: list[ImageSpec], course_dir: Path, *, force: bool = False) -> dict[str, Any]:
    """Submit a batch and write the tracking file. Returns immediately — does NOT wait."""
    check_required_roles(specs, source="batch push")
    for s in specs:
        s.validate()

    # Skip anything already on disk, exactly like the sync path.
    pending = []
    for s in specs:
        path = image_dir_for(course_dir, s.role) / s.resolved_filename()
        if path.is_file() and not force:
            continue
        pending.append(s)

    if not pending:
        print("Nothing to do — every image is already on disk.")
        return {}

    existing = load_tracking(course_dir)
    if existing and existing.get("status") in ("validating", "in_progress", "finalizing"):
        raise SystemExit(
            f"A batch is already in flight: {existing['batch_id']} ({existing['status']}).\n"
            f"Run with --pull to collect it, or --cancel to abandon it."
        )

    client = _client()
    model, quality = config.image_model(), config.image_quality()

    requests: dict[str, Any] = {}
    lines = []
    for s in pending:
        prompt = build_prompt(s)
        requests[s.key] = {
            "key": s.key, "role": s.role, "size": s.size,
            "quality": s.resolved_quality(), "filename": s.resolved_filename(),
            "path": f"{image_dir_for(course_dir, s.role).relative_to(course_dir)}/{s.resolved_filename()}",
            "prompt": prompt, "subject": s.subject, "style": s.style, "context": s.context,
        }
        lines.append(json.dumps({
            "custom_id": s.key,                    # the manifest key IS the join key
            "method": "POST", "url": ENDPOINT,
            "body": {"model": model, "prompt": prompt, "size": s.size,
                     "quality": s.resolved_quality(), "n": 1},
        }, ensure_ascii=False))

    buf = io.BytesIO("\n".join(lines).encode("utf-8"))
    buf.name = f"{course_dir.name}-images.jsonl"

    print(f"Uploading {len(lines)} requests to the Files API…")
    input_file = client.files.create(file=buf, purpose="batch")
    print(f"  file  {input_file.id}")

    batch = client.batches.create(
        input_file_id=input_file.id, endpoint=ENDPOINT, completion_window="24h",
        metadata={"course": course_dir.name},
    )
    print(f"  batch {batch.id}  status={batch.status}")

    now = datetime.now(timezone.utc)
    tracking = {
        "schema_version": "1.0",
        "purpose": ("Resume record for an in-flight image batch. A DIFFERENT SESSION can finish "
                    "this job: run `python3 generate_images.py --pull`. Everything needed to write "
                    "the images and the manifest is in this file."),
        "batch_id": batch.id,
        "input_file_id": input_file.id,
        "output_file_id": None,
        "endpoint": ENDPOINT,
        "model": model,
        "default_quality": quality,
        "status": batch.status,
        "image_count": len(pending),
        "saved_count": 0,
        "submitted_at": now.isoformat(),
        "check_after": (now + timedelta(minutes=TYPICAL_WAIT_MINUTES)).isoformat(),
        "typical_wait_minutes": TYPICAL_WAIT_MINUTES,
        "next_step": "python3 generate_images.py --pull",
        "requests": requests,
    }
    tracking_path(course_dir).parent.mkdir(parents=True, exist_ok=True)
    tracking_path(course_dir).write_text(json.dumps(tracking, ensure_ascii=False, indent=2), encoding="utf-8")

    est = len(pending) * 0.011 / 2
    print(f"\nSubmitted {len(pending)} images. ~50% cheaper than sync (~${est:.2f}).")
    print(f"Tracking file: {TRACKING_FILE}")
    print(f"Check back in ~{TYPICAL_WAIT_MINUTES} minutes:  python3 generate_images.py --pull")
    print("You can close this session. Nothing needs to keep running.")
    return tracking


# ────────────────────────────────────────────────────────────── pull

def pull(course_dir: Path) -> dict[str, Any]:
    """Poll the batch. If it is done, write the PNGs and the manifest. Safe to re-run."""
    tracking = load_tracking(course_dir)
    if not tracking:
        raise SystemExit(f"No {TRACKING_FILE} — nothing to pull. Submit one with --push.")

    client = _client()
    batch = client.batches.retrieve(tracking["batch_id"])
    counts = batch.request_counts
    tracking["status"] = batch.status

    print(f"── batch {batch.id}")
    print(f"   status: {batch.status}  |  total: {counts.total}  "
          f"|  completed: {counts.completed}  |  failed: {counts.failed}")

    if batch.status in ("validating", "in_progress", "finalizing"):
        tracking_path(course_dir).write_text(json.dumps(tracking, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   Not ready yet. Run --pull again in a few minutes.")
        return tracking

    if batch.status in ("failed", "expired", "cancelled"):
        tracking_path(course_dir).write_text(json.dumps(tracking, ensure_ascii=False, indent=2), encoding="utf-8")
        raise SystemExit(f"Batch {batch.status}. Delete {TRACKING_FILE} and re-run --push to try again.")

    # completed
    tracking["output_file_id"] = batch.output_file_id
    print(f"   Downloading {batch.output_file_id}…")
    body = client.files.content(batch.output_file_id).read().decode("utf-8")

    from .imagegen import NO_TEXT_CLAUSE
    saved, errors = 0, []
    records: dict[str, Any] = {}

    for line in body.splitlines():
        if not line.strip():
            continue
        result = json.loads(line)
        key = result["custom_id"]
        spec = tracking["requests"].get(key)
        if not spec:
            errors.append(f"{key}: not in the tracking file"); continue
        if result.get("error") or result["response"]["status_code"] != 200:
            errors.append(f"{key}: {result.get('error') or result['response']['status_code']}"); continue

        b64 = result["response"]["body"]["data"][0]["b64_json"]
        path = course_dir / spec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(b64))
        saved += 1

        records[key] = {**spec, "model": tracking["model"], "via": "batch",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "bytes": path.stat().st_size, "reused": False}
        print(f"   saved  {key}  ({path.stat().st_size/1024:.0f} KB)")

    tracking["saved_count"] = saved
    tracking_path(course_dir).write_text(json.dumps(tracking, ensure_ascii=False, indent=2), encoding="utf-8")

    # Merge into the manifest, keeping anything generated earlier by the sync path.
    manifest_path = course_dir / "assets" / "images.json"
    manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest_path.is_file()
                else {"schema_version": "1.0", "images": {}})
    manifest.update({
        "purpose": ("Recovery record of every image generated for this course. Content JSON refers "
                    "to an image by its `key`. `prompt` is the full composed prompt, so the art is "
                    "reproducible from this file alone."),
        "no_text_policy": NO_TEXT_CLAUSE,
        "model": tracking["model"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })
    manifest["images"] = dict(sorted({**manifest.get("images", {}), **records}.items()))
    manifest["image_count"] = len(manifest["images"])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n   Saved {saved}  |  errors {len(errors)}")
    for e in errors:
        print(f"     ! {e}")
    print(f"   Manifest: assets/images.json ({manifest['image_count']} images)")
    return tracking


def status(course_dir: Path) -> None:
    t = load_tracking(course_dir)
    if not t:
        print("No batch in flight."); return
    print(f"batch      : {t['batch_id']}")
    print(f"status     : {t['status']}")
    print(f"images     : {t['image_count']} (saved {t['saved_count']})")
    print(f"submitted  : {t['submitted_at']}")
    print(f"check after: {t['check_after']}")
    print(f"next step  : {t['next_step']}")


def cancel(course_dir: Path) -> None:
    t = load_tracking(course_dir)
    if not t:
        print("No batch to cancel."); return
    _client().batches.cancel(t["batch_id"])
    tracking_path(course_dir).unlink(missing_ok=True)
    print(f"Cancelled {t['batch_id']} and removed {TRACKING_FILE}.")
