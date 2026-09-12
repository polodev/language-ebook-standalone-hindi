"""Offline EPUB container, XML, manifest, spine and resource-reference checks."""
from __future__ import annotations
import argparse
import json
import posixpath
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

OPF = "{http://www.idpf.org/2007/opf}"
XHTML = "{http://www.w3.org/1999/xhtml}"


def check_epub(path: Path) -> dict:
    def need(condition, message):
        if not condition:
            raise ValueError(f"{path.name}: {message}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        need(len(names) == len(set(names)), "duplicate ZIP members")
        need(bool(names) and names[0] == "mimetype", "mimetype must be first")
        need(archive.getinfo("mimetype").compress_type == zipfile.ZIP_STORED, "mimetype must be uncompressed")
        need(archive.read("mimetype") == b"application/epub+zip", "invalid mimetype")
        need(archive.testzip() is None, "ZIP CRC failure")
        for name in names:
            need(not name.startswith("/") and ".." not in name.split("/"), f"unsafe member: {name}")
        container = ET.fromstring(archive.read("META-INF/container.xml"))
        rootfile = container.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
        need(rootfile is not None, "missing package rootfile")
        package_name = rootfile.get("full-path")
        package = ET.fromstring(archive.read(package_name))
        need(package.tag == OPF + "package" and package.get("version") == "3.0", "expected EPUB 3 package")
        metadata = package.find(OPF + "metadata")
        for key in ("title", "language", "identifier"):
            node = metadata.find("{http://purl.org/dc/elements/1.1/}" + key)
            need(node is not None and bool(node.text), f"missing {key}")
        identifiers = {node.get("id") for node in metadata.findall("{http://purl.org/dc/elements/1.1/}identifier")}
        need(package.get("unique-identifier") in identifiers, "invalid unique identifier")
        modified = metadata.find(OPF + "meta[@property='dcterms:modified']")
        need(modified is not None and bool(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", modified.text or "")), "missing modified UTC timestamp")
        items = list(package.find(OPF + "manifest"))
        ids = [item.get("id") for item in items]
        need(len(ids) == len(set(ids)), "duplicate manifest IDs")
        def resolve(source, reference):
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                need(parsed.scheme in {"https", "http", "mailto", "data"}, f"unsupported external reference: {reference}")
                return None, None
            target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parsed.path))) if parsed.path else source
            need(target in names, f"missing reference from {source}: {reference}")
            return target, unquote(parsed.fragment)
        resources = {}
        for item in items:
            target, fragment = resolve(package_name, item.get("href", ""))
            need(target is not None and not fragment, "manifest must reference local resources")
            need(target not in resources, f"duplicate manifest resource: {target}")
            resources[target] = item
        navs = [name for name, item in resources.items() if "nav" in item.get("properties", "").split()]
        need(len(navs) == 1, "exactly one navigation document required")
        spine = list(package.find(OPF + "spine"))
        need(bool(spine), "empty spine")
        by_id = {item.get("id"): item for item in items}
        for ref in spine:
            need(ref.get("idref") in by_id, "spine references missing item")
            need(by_id[ref.get("idref")].get("media-type") == "application/xhtml+xml", "spine item is not XHTML")
        documents = {}
        for name, item in resources.items():
            if item.get("media-type") == "application/xhtml+xml":
                root = ET.fromstring(archive.read(name))
                need(root.tag == XHTML + "html", f"invalid XHTML root: {name}")
                need(bool(root.get("lang") or root.get("{http://www.w3.org/XML/1998/namespace}lang")), f"missing language: {name}")
                need(root.find(XHTML + "head/" + XHTML + "title") is not None, f"missing title: {name}")
                documents[name] = root
        for name, root in documents.items():
            for element in root.iter():
                for attr in ("href", "src"):
                    reference = element.get(attr)
                    if reference is not None:
                        target, fragment = resolve(name, reference)
                        if target:
                            need(target in resources, f"resource not in manifest: {target}")
                        if fragment and target in documents:
                            need(any(node.get("id") == fragment for node in documents[target].iter()), f"missing fragment: {reference}")
        for name, item in resources.items():
            if item.get("media-type") == "text/css":
                css = archive.read(name).decode("utf-8")
                for match in re.finditer(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", css):
                    target, _ = resolve(name, match.group(1).strip())
                    need(target is None or target in resources, f"CSS resource not manifested: {target}")
        allowed = {"mimetype", "META-INF/container.xml", package_name} | set(resources)
        need(set(names) <= allowed, "unmanifested archive resources")
        return {"file": str(path), "status": "passed", "spine_items": len(spine), "xhtml_documents": len(documents), "images": sum(i.get("media-type", "").startswith("image/") for i in items), "fonts": sum(i.get("media-type", "").startswith("font/") for i in items)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=Path, nargs="+")
    args = parser.parse_args()
    print(json.dumps([check_epub(path) for path in args.files], ensure_ascii=False, indent=2))
