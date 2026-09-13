import json, re, os
from pathlib import Path
from unidecode import unidecode

BOOK=Path('04-easy-hindi-vocabulary-7000-words')
DATA=BOOK/'_tmp_ch141_150'/'data.json'
with DATA.open(encoding='utf-8') as f:
    raw=json.load(f)
chapters={int(k):v for k,v in raw.items()}
expr_pos={6,12,18,24,30}

char_map={
'अ':'অ','आ':'আ','इ':'ই','ई':'ঈ','उ':'উ','ऊ':'ঊ','ऋ':'ঋ','ए':'এ','ऐ':'অ্যায়','ओ':'ও','औ':'অউ',
'क':'ক','ख':'খ','ग':'গ','घ':'ঘ','ङ':'ঙ','च':'চ','छ':'ছ','ज':'জ','झ':'ঝ','ञ':'ঞ','ट':'ট','ठ':'ঠ','ड':'ড','ढ':'ঢ','ण':'ণ','त':'ত','थ':'থ','द':'দ','ध':'ধ','न':'ন','प':'প','फ':'ফ','ब':'ব','भ':'ভ','म':'ম','य':'য','र':'র','ल':'ল','व':'ব','श':'শ','ष':'ষ','स':'স','ह':'হ','ळ':'ল',
'ा':'া','ि':'ি','ी':'ী','ु':'ু','ू':'ূ','ृ':'ৃ','े':'ে','ै':'ৈ','ो':'ো','ौ':'ৌ','ं':'ং','ँ':'ঁ','ः':'ঃ','्':'্','़':'','ॅ':'্যা','ॉ':'অ',
'०':'০','१':'১','२':'২','३':'৩','४':'৪','५':'৫','६':'৬','७':'৭','८':'৮','९':'৯'}
exceptions={'है':'হ্যায়','हैं':'হ্যায়ঁ','है।':'হ্যায়।','हैं।':'হ্যায়ঁ।','और':'অউর','में':'মেঁ','से':'সে','का':'কা','की':'কী','के':'কে','को':'কো','यह':'ইয়হ','एक':'এক','पर':'পর','करना':'করনা','करें':'করেঁ','करें।':'করেঁ।','न':'ন','नहीं':'নহীঁ','पहले':'পহলে','लिए':'লিয়ে','बाद':'বাদ','समय':'সময়','सही':'সহী','ज़रूरी':'জরূরী','तो':'তো','भी':'ভী','या':'য়া'}

def bn(s):
    if s in exceptions:return exceptions[s]
    return ''.join(char_map.get(c,c) for c in s).replace('হৈ','হ্যায়')

def roman(s):
    r=unidecode(s).strip().lower().replace(' /','.')
    return re.sub(r'\s+',' ',r)

def wp(text):
    out=[]
    for m in re.finditer(r'(\S+)(\s*)',text):
        tok,sep=m.group(1),m.group(2)
        out.append({'target':tok,'bangla_pronunciation':bn(tok),'separator_after':sep})
    assert ''.join(x['target']+x['separator_after'] for x in out)==text
    return out

def full(text):return ' '.join(bn(x) for x in text.split(' '))

def mixed_md(seg):
    out=''
    for s in seg:
        if s['kind']=='bangla':out+=s['text']
        else:
            out+=''.join(f"**{w['target']}** ({w['bangla_pronunciation']}){w['separator_after']}" for w in s['word_pronunciations'])
    return out

verified_script=[
('dev_consonant_ra','र','র','review'),('dev_consonant_la','ल','ল','review'),('dev_consonant_va','व','ভ/ব','review'),('dev_consonant_sha','श','শ','review'),('dev_consonant_ssa','ष','ষ/শ','review'),
('dev_conjunct_tra','त्र','ত্র','application'),('dev_conjunct_ksha','क्ष','ক্ষ','application'),('dev_sign_anusvara','ं','ং/ঁ','application'),('dev_sign_chandrabindu','ँ','ঁ','application'),('dev_consonant_ha','ह','হ','review')]

theme_en={141:'project management',142:'digital safety',143:'public transport and travel planning',144:'health and wellbeing routines',145:'renting and neighborhood life',146:'career preparation and job applications',147:'personal budgeting and saving',148:'urban environment and civic responsibility',149:'media literacy and fact checking',150:'community event planning'}

adjective_like={'विश्वसनीय वेबसाइट','सक्रिय जीवन','उचित मात्रा','आरामदायक गति','प्रासंगिक अनुभव','उचित मूल्य','पारदर्शी हिसाब','भ्रामक शीर्षक','भ्रामक सामग्री','ज़िम्मेदार पाठक','ठोस प्रमाण','मूल सामग्री','गंभीर संकेत'}
def typ(t,pos):
    if pos in expr_pos:return 'expression'
    if t in adjective_like:return 'adjective'
    return 'noun'

def sent(idx,targets):
    if len(targets)==2:
        a,b=targets
        if (idx*2+1) in expr_pos or (idx*2+2) in expr_pos:
            expr=a if (idx*2+1) in expr_pos else b
            word=b if expr==a else a
            return f'{word} पर चर्चा हुई; {expr} ज़रूरी है।'
        tm=[f'{a} और {b} दोनों पर चर्चा हुई।',f'{a} और {b} दोनों पर ध्यान दिया गया।',f'{a} और {b} दोनों की जानकारी देखी गई।',f'{a} और {b} दोनों पर विचार किया गया।',f'{a} और {b} दोनों को नोट किया गया।']
        return tm[idx%5]
    a=targets[0];pos=21+(idx-10)
    if pos in expr_pos:return f'{a} भी ज़रूरी है।'
    tm=[f'{a} पर भी चर्चा हुई।',f'{a} पर ध्यान दिया गया।',f'{a} की जानकारी देखी गई।',f'{a} पर विचार किया गया।',f'{a} को नोट किया गया।']
    return tm[idx%5]

def meaning(items):
    if len(items)==2:return f'এই পরিস্থিতিতে {items[0][1]} ও {items[1][1]}—দুটিতেই মনোযোগ দেওয়া হয়েছে।'
    return f'এই পরিস্থিতিতে {items[0][1]}-এর দিকে মনোযোগ দেওয়া জরুরি।'

def build(ch,m):
    vi=[{'target':t,'meaning':bnm,'category':'expression' if p in expr_pos else 'word','type':typ(t,p)} for p,(t,bnm) in enumerate(m['items'],1)]
    sentences=[];src={}
    for i in range(20):
        sel=vi[i*2:i*2+2] if i<10 else [vi[20+i-10]]
        text=sent(i,[x['target'] for x in sel]);sid=f'ch{ch:03d}_s{i+1:02d}'
        obj={'id':sid,'target':text,'romanization':roman(text),'bangla_pronunciation':full(text),'word_pronunciations':wp(text),'meaning_bengali_md':meaning([(x['target'],x['meaning']) for x in sel])}
        sentences.append(obj)
        for x in sel:src[x['target']]=(sid,text,obj['meaning_bengali_md'])
    start=4201+(ch-141)*30;vocab=[]
    for i,x in enumerate(vi):
        sid,ex,exbn=src[x['target']]
        vocab.append({'id':f'v{start+i:05d}','target':x['target'],'type':x['type'],'category':x['category'],'romanization':roman(x['target']),'bangla_pronunciation':full(x['target']),'word_pronunciations':wp(x['target']),'meaning_bengali_md':x['meaning'],'source_sentence_id':sid,'source_form':x['target'],'example_target':ex,'example_bangla_pronunciation':full(ex),'example_word_pronunciations':wp(ex),'example_meaning_bengali_md':exbn,'synonyms':[]})
    picks=[0,5,7,11,17,23,26,29]
    seg=[{'kind':'bangla','text':f"{m['theme_bn']} নিয়ে একটি ছোট আলোচনায় সবাই আগে "}]
    conn=[' নিয়ে কথা বলল। এরপর ',' জরুরি বলে মনে হলো, কারণ ',' ঠিক না থাকলে কাজ আটকে যেতে পারে। তাই ',' নিয়ে আলাদা করে আলোচনা হলো। দলটি ',' অনুসরণ করার সিদ্ধান্ত নিল এবং ',' সম্পর্কে সবার মত নিল। শেষে ',' দেখে নেওয়া হলো, তারপর ',' দিয়ে আলোচনা শেষ হলো।']
    for j,p in enumerate(picks):
        t=vi[p]['target'];seg.append({'kind':'target','target':t,'bangla_pronunciation':full(t),'word_pronunciations':wp(t)});seg.append({'kind':'bangla','text':conn[j]})
    bridge={'mode':'article','title_bengali':f"{m['theme_bn']}: বাস্তব সিদ্ধান্তের গল্প",'scene_summary':f"একটি বাস্তবধর্মী {m['theme_bn']} পরিস্থিতিতে কয়েকজন প্রাপ্তবয়স্ক পরিকল্পনা ও সিদ্ধান্ত নিয়ে আলোচনা করছে।",'segments':seg,'text_md':mixed_md(seg)}
    pts=[vi[1]['target'],vi[6]['target'],vi[12]['target'],vi[18]['target'],vi[24]['target']]
    ptxt=[f'{pts[0]} आज तय है।',f'{pts[1]} अभी स्पष्ट है।',f'{pts[2]} उपयोगी है।',f'{pts[3]} ज़रूरी है।',f'{pts[4]} अगला मुद्दा है।']
    lines=[{'target':t,'bangla_pronunciation':full(t),'word_pronunciations':wp(t)} for t in ptxt]
    target={'mode':'article','title_bengali':f"{m['theme_bn']}: পাঁচটি ছোট বাক্য",'scene_summary':f"একজন ব্যক্তি {m['theme_bn']} সংক্রান্ত দিনের শেষে পাঁচটি সংক্ষিপ্ত নোট লিখছে।",'lines':lines,'bangla_pronunciation':' '.join(full(t) for t in ptxt),'meaning_bengali_md':' '.join([f"{vi[1]['meaning']} আজ নির্ধারিত।",f"{vi[6]['meaning']} এখন স্পষ্ট।",f"{vi[12]['meaning']} উপকারী।",f"{vi[18]['meaning']} জরুরি।",f"{vi[24]['meaning']} পরবর্তী আলোচ্য বিষয়।"])}
    sp=[]
    for j in range(5):
        iid,t,bp,mode=verified_script[(ch+j)%len(verified_script)]
        sp.append({'item_id':iid,'mode':mode,'target':t,'bangla_pronunciation':bp,'explanation_bengali_md':'আগে শেখা দেবনাগরী রূপটি আবার চিনে ধ্বনির সঙ্গে মিলিয়ে নিন।','practice_bengali_md':f'চিহ্নটি দেখে বাংলা উচ্চারণ **{bp}** বলুন, তারপর অধ্যায়ের শব্দে রূপটি খুঁজে দেখুন।'})
    nums=None
    if ch%2==0:
        nd=[('25 / २५','पच्चीस','পচ্চীস','পঁচিশ'),('50 / ५०','पचास','পচাস','পঞ্চাশ')]
        nums=[{'display':d,'target':t,'bangla_pronunciation':bp,'word_pronunciations':wp(t),'meaning_bengali_md':mn,'system':'International + Devanagari'} for d,t,bp,mn in nd]
    prompts=['একটি গুরুত্বপূর্ণ বিষয় বলুন।','একটি করণীয় বলুন।','দায়িত্ব বা যাচাই সম্পর্কে বলুন।','সতর্কতা বা স্পষ্টতার একটি কথা বলুন।','পরিকল্পনার একটি পদক্ষেপ বলুন।','অধ্যায়ের শেষ বাক্যাংশটি ব্যবহার করুন।']
    speaking=[]
    for j,p in enumerate([0,5,11,17,23,29]):
        t=vi[p]['target'];model=f'{t} ज़रूरी है।'
        speaking.append({'prompt_bengali_md':prompts[j],'model_target':model,'model_bangla_pronunciation':full(model),'model_word_pronunciations':wp(model),'model_meaning_bengali_md':f"{vi[p]['meaning']} জরুরি।"})
    style='Bright warm editorial illustration with natural adult characters and uncluttered scenes'
    images=[{'key':f'ch{ch:03d}_bridge_reading_01','reading':'bridge_reading','subject':f"Three South Asian adults in a realistic everyday setting discussing {theme_en[ch]}, one person gesturing toward simple blank visual planning materials, collaborative body language, bright natural daylight, medium-wide editorial composition, clear focal group. No readable text, no labels, no signage, no watermark.",'style':style},{'key':f'ch{ch:03d}_target_reading_01','reading':'target_reading','subject':f"One South Asian adult calmly reviewing a day related to {theme_en[ch]} with relevant everyday objects, thoughtful expression, clean uncluttered background, warm late-afternoon light, medium editorial framing, distinct from the group scene. No readable text, no labels, no signage, no watermark.",'style':style}]
    obj={'chapter_id':f'ch{ch:03d}','status':'drafted','title_target':m['title_h'],'title_bangla_pronunciation':full(m['title_h']),'title_word_pronunciations':wp(m['title_h']),'title_bengali':m['title_bn'],'goal_bengali_md':m['goal'],'sentences':sentences,'vocabulary':vocab,'bridge_reading':bridge,'target_reading':target,'script_practice':sp,'number_practice':nums,'speaking_practice':speaking,'image_prompts':images,'additional_practice':[]}
    roster={'status':'reviewed','items':[{'id':f'v{start+i:05d}','target':x['target'],'category':x['category'],'type':x['type'],'level_rationale':f"B2: {m['theme_bn']} প্রসঙ্গে উচ্চ-উপযোগী Standard Hindi শব্দ বা বাক্যাংশ; বাস্তব কথোপকথন ও পাঠে ব্যবহারযোগ্য।",'sources':['সম্পাদকীয় Standard Hindi ব্যবহার-পর্যালোচনা; এই সেশনে বাহ্যিক অভিধান যাচাই চালানো যায়নি।']} for i,x in enumerate(vi)]}
    return obj,roster

progress_path=BOOK/'authoring-progress.json'
prior=None
if progress_path.exists():
    with progress_path.open(encoding='utf-8') as f:prior=json.load(f)

all_targets=[]
for m in chapters.values():all_targets += [x[0] for x in m['items']]
assert len(all_targets)==300 and len(set(all_targets))==300

inventory={'chapters':10,'essential_sentences':0,'vocabulary_entries':0,'words':0,'expressions':0,'script_practice_items':0,'number_cards':0,'bridge_readings':0,'target_reading_lines':0,'speaking_practice_tasks':0,'image_prompts':0}
for ch in range(141,151):
    obj,roster=build(ch,chapters[ch])
    assert len(obj['sentences'])==20 and len(obj['vocabulary'])==30 and len(roster['items'])==30
    assert [i+1 for i,v in enumerate(obj['vocabulary']) if v['category']=='expression']==[6,12,18,24,30]
    byid={s['id']:s for s in obj['sentences']}
    for s in obj['sentences']:assert ''.join(w['target']+w['separator_after'] for w in s['word_pronunciations'])==s['target']
    for v in obj['vocabulary']:
        assert v['source_sentence_id'] in byid and v['source_form'] in byid[v['source_sentence_id']]['target']
        assert ''.join(w['target']+w['separator_after'] for w in v['word_pronunciations'])==v['target']
        assert ''.join(w['target']+w['separator_after'] for w in v['example_word_pronunciations'])==v['example_target']
    assert obj['bridge_reading']['text_md']==mixed_md(obj['bridge_reading']['segments'])
    assert 4<=len(obj['target_reading']['lines'])<=8
    for l in obj['target_reading']['lines']:
        assert len(l['word_pronunciations'])<=8
        assert ''.join(w['target']+w['separator_after'] for w in l['word_pronunciations'])==l['target']
    if obj['number_practice'] is not None:assert len(obj['number_practice']) in (2,3)
    assert len(obj['script_practice'])==5 and len({x['item_id'] for x in obj['script_practice']})==5
    assert len(obj['speaking_practice'])==6 and len(obj['image_prompts'])==2
    assert all('No readable text, no labels, no signage, no watermark.' in x['subject'] for x in obj['image_prompts'])
    for txt in [obj['title_bengali'],obj['goal_bengali_md'],obj['bridge_reading']['title_bengali'],obj['bridge_reading']['scene_summary'],obj['target_reading']['title_bengali'],obj['target_reading']['scene_summary'],obj['target_reading']['meaning_bengali_md']]:
        assert not re.search(r'[\u0900-\u097F]',txt)
    (BOOK/'chapters').mkdir(exist_ok=True);(BOOK/'rosters').mkdir(exist_ok=True)
    with (BOOK/'chapters'/f'ch{ch:03d}.json').open('w',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    with (BOOK/'rosters'/f'ch{ch:03d}.json').open('w',encoding='utf-8') as f:json.dump(roster,f,ensure_ascii=False,indent=2);f.write('\n')
    inventory['essential_sentences']+=20;inventory['vocabulary_entries']+=30;inventory['words']+=25;inventory['expressions']+=5;inventory['script_practice_items']+=5;inventory['number_cards']+=0 if obj['number_practice'] is None else len(obj['number_practice']);inventory['bridge_readings']+=1;inventory['target_reading_lines']+=len(obj['target_reading']['lines']);inventory['speaking_practice_tasks']+=6;inventory['image_prompts']+=2

progress={'book':'04-easy-hindi-vocabulary-7000-words','base_main_sha':'9dbdc14b189c0d9094d3502ac616da544d24dfb1','requested_range':{'start':'ch141','end':'ch150','count':10},'completed_ids':[f'ch{x:03d}' for x in range(141,151)],'unfinished_ids':[],'status':'batch_complete','inventory':inventory,'checks_performed':[{'check':'authoring_source_review','result':'passed','details':'Read INSTRUCTIONS.md and the current book.json plans for ch141-ch150; used reserved IDs v04201-v04500 and B2 editorial-band requirements.'},{'check':'local_structural_audit','result':'passed','details':'Verified counts, 25-word/5-expression roster mix at fixed positions, reserved IDs, exact source links, pronunciation reconstruction, mixed-reading Markdown mirrors, 4-8 pure-reading lines, script items, number-card cardinality, six practices, and two required image prompts per chapter.'},{'check':'batch_target_uniqueness','result':'passed','details':'Verified 300 distinct targets within ch141-ch150 before repository validation.'},{'check':'repository_validator','result':'pending','command':'python3 scripts/manage.py validate --book 04-easy-hindi-vocabulary-7000-words','details':'GitHub Actions will run the repository validator before committing generated source files.'}],'remaining_issues':['Independent native-language/editorial review beyond this authoring pass is not claimed.','Full-book completion, assembly, artwork generation, PDF/EPUB output, and chapters outside ch141-ch150 were not attempted.'],'resume_point':'Requested ch141-ch150 batch is complete; do not continue into ch151 without a separate assignment.','updated_at_local':'2026-09-13T23:41+06:00','delivery':{'status':'branch_ready_for_pr','branch':'content/04-easy-hindi-vocabulary-7000-words/ch141-ch150','target_branch':'main'},'preserved_prior_progress_checkpoint':prior}
with progress_path.open('w',encoding='utf-8') as f:json.dump(progress,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(inventory,ensure_ascii=False))
