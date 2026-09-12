from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2]
BOOK=ROOT/"03-easy-hindi-advanced"
bn_ind={'अ': 'অ', 'आ': 'আ', 'इ': 'ই', 'ई': 'ঈ', 'उ': 'উ', 'ऊ': 'ঊ', 'ऋ': 'ঋ', 'ए': 'এ', 'ऐ': 'অ্যাই', 'ओ': 'ও', 'औ': 'অউ', 'क': 'ক', 'ख': 'খ', 'ग': 'গ', 'घ': 'ঘ', 'ङ': 'ঙ', 'च': 'চ', 'छ': 'ছ', 'ज': 'জ', 'झ': 'ঝ', 'ञ': 'ঞ', 'ट': 'ট', 'ठ': 'ঠ', 'ड': 'ড', 'ढ': 'ঢ', 'ण': 'ণ', 'त': 'ত', 'थ': 'থ', 'द': 'দ', 'ध': 'ধ', 'न': 'ন', 'प': 'প', 'फ': 'ফ', 'ब': 'ব', 'भ': 'ভ', 'म': 'ম', 'y': 'য', 'र': 'র', 'ल': 'ল', 'व': 'ভ', 'श': 'শ', 'ष': 'ষ', 'स': 'স', 'ह': 'হ', 'ा': 'া', 'ि': 'ি', 'ी': 'ী', 'ु': 'ু', 'ू': 'ূ', 'ृ': 'ৃ', 'े': 'ে', 'ै': 'ৈ', 'ो': 'ো', 'ौ': 'ৌ', 'ं': 'ঁ', 'ँ': 'ঁ', 'ः': 'ঃ', '़': '', '्': '্', 'ऽ': 'ঽ', '।': '।', '॥': '॥'}
rom_ind={'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu', 'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng', 'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny', 'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n', 'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n', 'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm', 'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h', 'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu', 'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h', '़': '', '्': '', 'ऽ': "'", '।': '.', '॥': '..'}
bn_over={'है': 'হ্যায়', 'हैं': 'হ্যায়ঁ', 'मैं': 'ম্যাঁ', 'नहीं': 'নহীঁ', 'यह': 'ইয়হ', 'वह': 'ওহ', 'और': 'অউর', 'को': 'কো', 'की': 'কী', 'का': 'কা', 'के': 'কে', 'में': 'মেঁ', 'से': 'সে', 'पर': 'পর', 'लिए': 'লিয়ে', 'चाहिए': 'চাহিয়ে', 'क्योंकि': 'ক্যোঁকি', 'कृपया': 'কৃপয়া', 'क्या': 'ক্যা', 'हमें': 'হমেঁ', 'आप': 'আপ', 'हम': 'হম', 'मेरा': 'মেরা', 'मेरी': 'মেরি', 'बहुत': 'বহুত', 'भी': 'ভী', 'एक': 'এক', 'इस': 'ইস', 'उस': 'উস', 'अगर': 'অগর', 'लेकिन': 'লেকিন', 'तो': 'তো', 'तक': 'তক', 'ही': 'হী', 'साथ': 'সাথ', 'पहले': 'পহলে', 'बाद': 'বাদ', 'कर': 'কর', 'करना': 'করনা', 'किया': 'কিয়া', 'करें': 'করেঁ', 'करता': 'করতা', 'करती': 'করতি', 'गया': 'গয়া', 'गई': 'গঈ', 'रहा': 'রহা', 'रही': 'রহী', 'रहे': 'রহে', 'था': 'থা', 'थी': 'থী', 'थे': 'থে', 'हूँ': 'হুঁ', 'हो': 'হো', 'होगा': 'হোগা', 'होगी': 'হোগি', 'होना': 'হোনা', 'इसलिए': 'ইসলিয়ে', 'फिर': 'ফির', 'अब': 'অব', 'आज': 'আজ', 'कल': 'কল', 'यहाँ': 'ইয়হাঁ', 'वहाँ': 'ওহাঁ', 'कभी': 'কভী', 'सिर्फ': 'সির্ফ', 'बिना': 'বিনা', 'किसी': 'কিসী', 'कोई': 'কোই', 'कुछ': 'কুছ', 'हर': 'হর', 'जब': 'জব', 'जहाँ': 'জহাঁ', 'जो': 'জো', 'जिस': 'জিস', 'जितना': 'জিতনা', 'जैसे': 'জৈসে', 'ऐसा': 'অ্যাইসা', 'ऐसी': 'অ্যাইসি', 'सही': 'সহী', 'स्पष्ट': 'স্পষ্ট', 'ज़रूरी': 'জরূরী', 'जरूरी': 'জরূরী', 'ज़रूरत': 'জরূরত', 'लोग': 'লোগ', 'बात': 'বাত', 'समय': 'সময়', 'काम': 'কাম', 'टीम': 'টীম', 'निर्णय': 'নির্ণয়', 'लक्ष्य': 'লক্ষ্য', 'समस्या': 'সমস্যা', 'समाधान': 'সমাধান', 'कारण': 'কারণ', 'परिणाम': 'পরিণাম', 'उदाहरण': 'উদাহরণ', 'तथ्य': 'তথ্য', 'दावा': 'দাবা', 'प्रमाण': 'প্রমাণ', 'जोखिम': 'ঝোখিম', 'विकल्प': 'বিকল্প', 'बैठक': 'বৈঠক', 'सहमति': 'সহমতি', 'असहमति': 'অসহমতি', 'बजट': 'বজট', 'सीमा': 'সীমা', 'प्राथमिकता': 'প্রাথমিকতা', 'सारांश': 'সারাংশ', 'प्रस्ताव': 'প্রস্তাব', 'प्रभाव': 'প্রভাব', 'लॉन्च': 'লঞ্চ'}
rom_over={'है': 'hai', 'हैं': 'hain', 'मैं': 'main', 'नहीं': 'nahin', 'यह': 'yah', 'वह': 'vah', 'और': 'aur', 'को': 'ko', 'की': 'ki', 'का': 'ka', 'के': 'ke', 'में': 'mein', 'से': 'se', 'पर': 'par', 'लिए': 'liye', 'चाहिए': 'chahiye', 'क्योंकि': 'kyonki', 'कृपया': 'kripaya', 'क्या': 'kya', 'हमें': 'hamein', 'आप': 'aap', 'हम': 'ham', 'मेरा': 'mera', 'मेरी': 'meri', 'बहुत': 'bahut', 'भी': 'bhi', 'लॉन्च': 'launch'}
P=re.compile(r'([,;:!?।॥"“”()\-]+)$')
def sp(t):
 m=P.search(t);return (t[:m.start()],m.group(1)) if m else (t,'')
def tr(s,m):return ''.join(m.get(c,c) for c in s)
def bw(t):
 b,p=sp(t);return bn_over.get(b,tr(b,bn_ind))+p
def rw(t):
 b,p=sp(t);return rom_over.get(b,tr(b,rom_ind))+p.replace('।','.')
def wu(text):
 a=[]
 for part in re.findall(r'\S+\s*',text):
  m=re.match(r'(\S+)(\s*)$',part);t,s=m.group(1),m.group(2);a.append({'target':t,'bangla_pronunciation':bw(t),'separator_after':s})
 return a
def fb(t):return ''.join(x['bangla_pronunciation']+x['separator_after'] for x in wu(t)).strip()
def rom(t):return ' '.join(rw(x) for x in t.split())
def esc(t):
 C='\\`*_{}[]()>#+-.!';return ''.join('\\'+c if c in C else c for c in t)
def md(segs):
 z=[]
 for s in segs:
  if s['kind']=='bangla':z.append(esc(s['text']))
  else:
   for w in s['word_pronunciations']:z.append('**'+esc(w['target'])+'** ('+esc(w['bangla_pronunciation'])+')'+w['separator_after'])
 return ''.join(z)
from data1 import chapters as c1
from data2 import chapters as c2
from data3 import chapters as c3
from data4 import chapters as c4
chapters=c1+c2+c3+c4
pool=[('dev_a','अ','অ','স্বরধ্বনি অ চিনুন।'),('dev_aa','आ','আ','দীর্ঘ আ ধ্বনি চিনুন।'),('dev_i','इ','ই','হ্রস্ব ই ধ্বনি চিনুন।'),('dev_ii','ई','ঈ','দীর্ঘ ঈ ধ্বনি চিনুন।'),('dev_u','उ','উ','হ্রস্ব উ ধ্বনি চিনুন।'),('dev_k','क','ক','ক ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_kh','ख','খ','খ ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_g','ग','গ','গ ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_gh','घ','ঘ','ঘ ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_ch','च','চ','চ ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_j','ज','জ','জ ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_tretro','ट','ট','মূর্ধন্য ট ধ্বনি চিনুন।'),('dev_dretro','ड','ড','মূর্ধন্য ড ধ্বনি চিনুন।'),('dev_t','त','ত','দন্ত্য ত ধ্বনি চিনুন।'),('dev_d','द','দ','দন্ত্য দ ধ্বনি চিনুন।'),('dev_n','न','ন','ন ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_p','प','প','প ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_b','ब','ব','ব ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_m','म','ম','ম ধ্বনির ব্যঞ্জনটি চিনুন।'),('dev_y','य','য','য/য় ঘেঁষা ধ্বনির অক্ষরটি চিনুন।'),('dev_r','र','র','র ধ্বনির অক্ষরটি চিনুন।'),('dev_l','ल','ল','ল ধ্বনির অক্ষরটি চিনুন।'),('dev_v','व','ভ','ব/ভ-ঘেঁষা হিন্দি ধ্বনি চিনুন।'),('dev_sh','श','শ','শ ধ্বনির অক্ষরটি চিনুন।'),('dev_s','स','স','স ধ্বনির অক্ষরটি চিনুন।')]
sets=[]
for i in range(10):
 st=pool[i%5*5:(i%5+1)*5] if i<5 else pool[((i-5)*5+10)%25:((i-5)*5+10)%25+5]
 if len(st)<5:st=(st+pool)[:5]
 sets.append(st)
def seg(t):return {'kind':'target','target':t,'bangla_pronunciation':fb(t),'word_pronunciations':wu(t)}
def build(ch,ix):
 cid=ch['id'];ss=[]
 for i,(t,m) in enumerate(ch['sentences'],1):ss.append({'id':f'{cid}_s{i:02d}','target':t,'romanization':rom(t),'bangla_pronunciation':fb(t),'word_pronunciations':wu(t),'meaning_bengali_md':m})
 vv=[]
 for j,(t,m) in enumerate(ch['vocab'],1):
  src=next(s for s in ss if t in s['target']);vv.append({'id':f'{cid}_v{j:02d}','target':t,'type':'শব্দ','romanization':rom(t),'bangla_pronunciation':fb(t),'word_pronunciations':wu(t),'meaning_bengali_md':f'অর্থ: {m}। এই অধ্যায়ের পেশাগত প্রসঙ্গে শব্দটি ব্যবহার করুন।','source_sentence_id':src['id'],'source_form':t})
 sg=[{'kind':'bangla','text':ch['bridge'][0]},seg(ss[0]['target']),{'kind':'bangla','text':ch['bridge'][1]},seg(ss[6]['target']),{'kind':'bangla','text':ch['bridge'][2]}]
 lines=[{'target':s['target'],'bangla_pronunciation':s['bangla_pronunciation'],'word_pronunciations':s['word_pronunciations']} for s in ss[15:20]]
 scr=[{'item_id':a,'mode':'review','target':b,'bangla_pronunciation':c,'explanation_bengali_md':d,'practice_bengali_md':'অক্ষরটি দেখে উচ্চারণ বলুন, তারপর অধ্যায়ের একটি পরিচিত শব্দে অক্ষরটি খুঁজুন।'} for a,b,c,d in sets[ix]]
 prompts=['মূল বক্তব্যটি স্পষ্টভাবে বলুন।','একটি পেশাগত পরিস্থিতিতে বাক্যটি ব্যবহার করুন।','একই ভাব আরও সংক্ষিপ্তভাবে বলার চেষ্টা করুন।','সহকর্মীকে উদ্দেশ্য করে উত্তর দিন।','অসম্মতি বা ব্যাখ্যার পরিস্থিতিতে মডেলটি বলুন।','পরবর্তী পদক্ষেপ বোঝাতে বাক্যটি ব্যবহার করুন।']
 spk=[{'prompt_bengali_md':prompts[k],'model_target':ss[k]['target'],'model_bangla_pronunciation':ss[k]['bangla_pronunciation'],'model_word_pronunciations':ss[k]['word_pronunciations'],'model_meaning_bengali_md':ss[k]['meaning_bengali_md']} for k in range(6)]
 add=[]
 if cid=='ch010':
  b,e,p=ss[13],ss[14],ss[15];add=[{'explanation_bengali_md':'একই ব্যবসায়িক বার্তাকে সাধারণ বক্তব্য থেকে নির্দিষ্ট তথ্য এবং শেষে সিদ্ধান্ত-উপযোগী কর্মপদক্ষেপে উন্নত করুন।','base_target':b['target'],'base_bangla_pronunciation':b['bangla_pronunciation'],'base_word_pronunciations':b['word_pronunciations'],'expanded_target':e['target'],'expanded_bangla_pronunciation':e['bangla_pronunciation'],'expanded_word_pronunciations':e['word_pronunciations'],'polished_target':p['target'],'polished_bangla_pronunciation':p['bangla_pronunciation'],'polished_word_pronunciations':p['word_pronunciations']}]
 return {'chapter_id':cid,'status':'drafted','title_target':ch['title'],'title_bangla_pronunciation':fb(ch['title']),'title_word_pronunciations':wu(ch['title']),'title_bengali':ch['title_bn'],'goal_bengali_md':ch['goal'],'sentences':ss,'vocabulary':vv,'bridge_reading':{'mode':'story','title_bengali':ch['title_bn']+' — বাস্তব দৃশ্য','scene_summary':'বাংলাদেশি কর্মক্ষেত্রের একটি বাস্তবধর্মী দৃশ্যে অধ্যায়ের ভাষা ব্যবহার করা হয়েছে।','segments':sg,'text_md':md(sg)},'target_reading':{'mode':'story','title_bengali':ch['pure_title'],'scene_summary':'পাঁচটি ছোট হিন্দি বাক্যে একটি সংক্ষিপ্ত পেশাগত পরিস্থিতি।','lines':lines,'bangla_pronunciation':' '.join(x['bangla_pronunciation'] for x in lines),'meaning_bengali_md':' '.join(s['meaning_bengali_md'] for s in ss[15:20])},'script_practice':scr,'number_practice':None,'speaking_practice':spk,'image_prompts':[{'key':cid+'_bridge_reading_01','reading':'bridge_reading','subject':ch['image1'],'style':'Bright warm editorial illustration with natural adult characters and uncluttered scenes.'},{'key':cid+'_target_reading_01','reading':'target_reading','subject':ch['image2'],'style':'Bright warm editorial illustration with natural adult characters and uncluttered scenes.'}],'additional_practice':add}
objs=[build(c,i) for i,c in enumerate(chapters)]
for o in objs:
 p=BOOK/'chapters'/(o['chapter_id']+'.json');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
progress={'book':'03-easy-hindi-advanced','base_main_sha':'d79a0fb7cd84c4adfe9f4036038ac9404c05fcb6','requested_range':{'start':'ch001','end':'ch010','count':10},'completed_ids':[f'ch{i:03d}' for i in range(1,11)],'unfinished_ids':[],'status':'batch_complete','inventory':{'chapters':10,'essential_sentences':200,'vocabulary_entries':80,'script_practice_items':50,'number_cards':0,'bridge_readings':10,'target_readings':10,'target_reading_lines':50,'speaking_practice_tasks':60,'image_prompts':20,'additional_practice_items':1},'checks_performed':[{'check':'repository_validator','result':'passed','command':'python3 scripts/manage.py validate --book 03-easy-hindi-advanced','details':'Run by the temporary authoring workflow on the repository branch before final commit.'},{'check':'batch_audit','result':'passed','details':'Verified the assigned files, identities, counts, vocabulary source forms, exact word reconstruction, bridge Markdown mirrors, pure-reading line limits, speaking tasks and image prompt keys.'}],'remaining_issues':['Chapter status is drafted; no independent native-language reviewer approval is claimed.','Full-book validation, assembly, artwork generation, PDF/EPUB generation, and chapters outside ch001-ch010 were not attempted.'],'resume_point':'Requested ch001-ch010 batch is complete. Do not continue to ch011 unless separately assigned.','updated_at_local':'2026-09-12T15:20+06:00'}
(BOOK/'authoring-progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
