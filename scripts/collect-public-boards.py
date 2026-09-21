#!/usr/bin/env python3
"""Collect a broad discovery layer, conservatively screened from official APIs.

This layer deliberately leaves graduate eligibility and compound qualification
paths unverified. It is separate from the curated graduate records. No size cap
or per-employer quota is applied. The public output contains brief analytical
paraphrases, not full job descriptions. Raw responses stay in ignored qa/.
"""
import concurrent.futures
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'qa/source-cache'
CACHE.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()
STATE_CODES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
CITIES = {'San Francisco':'CA','San Francisco Bay Area':'CA','Mountain View':'CA','San Mateo':'CA','Redwood City':'CA','Palo Alto':'CA','Menlo Park':'CA','Santa Clara':'CA','San Jose':'CA','Sunnyvale':'CA','Foster City':'CA','San Diego':'CA','Los Angeles':'CA','Irvine':'CA','Seattle':'WA','Bellevue':'WA','Kirkland':'WA','New York':'NY','Brooklyn':'NY','Boston':'MA','Cambridge':'MA','Pittsburgh':'PA','Philadelphia':'PA','Washington, DC':'DC','Austin':'TX','Dallas':'TX','Houston':'TX','Atlanta':'GA','Chicago':'IL','Denver':'CO','Boulder':'CO','Raleigh':'NC','Durham':'NC','Madison':'WI','Ann Arbor':'MI','Detroit':'MI','Minneapolis':'MN','Salt Lake City':'UT','Phoenix':'AZ','Miami':'FL','Orlando':'FL','Nashville':'TN','Portland, OR':'OR','Arlington, VA':'VA','Reston':'VA'}
CORE_TITLE = re.compile(r'\b(machine learning|ML|AI|artificial intelligence|deep learning|LLM|NLP|computer vision|perception|applied scientist|data scient(?:ist|ce)|research (?:scientist|engineer)|inference|reinforcement learning|post[- ]training|training/inference|AI/ML)\b', re.I)
DISALLOWED = re.compile(r'\b(senior|sr\.?|staff|principal|lead|director|manager|head|VP|vice president|chief|founding|distinguished|intern(?:ship)?|co[- ]op|contractor|contract|temporary|freelance|fellow(?:s|ship)?|consultant|economist|postdoc|postdoctoral|residency|part[- ]time|talent pool|designer|sales|solutions (?:architect|engineer)|vendor|operations|technical writer|recruiter|account executive|AI trainer|policy trainer|policy evaluator|red teamer)\b', re.I)
MODEL_WORDS = re.compile(r'\b(machine learning|deep learning|neural|language models?|LLMs?|reinforcement learning|computer vision|NLP|model training|model inference)\b', re.I)
EXPERIENCE = re.compile(r'(?<![\d.])(\d{1,2})\s*(?:\+|[-–—]\s*\d{1,2}\s*\+?)?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:[A-Za-z/ -]{0,65})?experience\b',re.I)
SKILLS = ['Python','C++','Java','Go','SQL','PyTorch','TensorFlow','JAX','LLM','NLP','computer vision','deep learning','machine learning','Kubernetes','Docker','CUDA','Spark','Ray','AWS','GCP','RAG','reinforcement learning']

def clean(value):
    # Greenhouse often HTML-escapes an entire HTML description.
    for _ in range(2):
        value = html.unescape(value or '')
    value = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>',' ',value,flags=re.S|re.I)
    value = re.sub(r'</(?:p|li|h\d|div)>|<br\s*/?>', '\n', value, flags=re.I)
    return '\n'.join(re.sub(r'\s+',' ',re.sub(r'<[^>]*>',' ',line)).strip() for line in value.splitlines() if line.strip())

def get_board(item):
    endpoint = f"https://boards-api.greenhouse.io/v1/boards/{item['board']}/jobs?content=true"
    try:
        req = Request(endpoint,headers={'User-Agent':'AI-Career-Compass student research/2.0'})
        with urlopen(req,timeout=25) as response:
            payload = json.loads(response.read())
        (CACHE / f"{item['board']}.json").write_text(json.dumps(payload))
        return item, endpoint, payload, None
    except Exception as error:
        return item, endpoint, None, type(error).__name__

def locations(text):
    text = '; '.join(part for part in re.split(r'[;|•]',text) if not re.search(r'United Kingdom|\bUK\b|\bLondon\b|Canada|\bCAN\b|Poland|Germany|France|India|Singapore',part,re.I))
    rows = []
    for city, state in CITIES.items():
        if re.search(r'\b'+re.escape(city)+r'\b',text,re.I):
            rows.append({'city':city,'state':state,'country':'US'})
    # Uppercase abbreviations only: "or" is not Oregon.
    for city, state in re.findall(r'([A-Za-z .\'-]+),\s*([A-Z]{2})\b', text):
        if state in STATE_CODES and not any(r['state']==state and r['city'].lower() in city.lower() for r in rows):
            rows.append({'city':city.strip(),'state':state,'country':'US'})
    country = bool(re.search(r'\bUnited States\b|\bUSA\b|\bUS\b|\bU\.S\.',text))
    if not rows and country:
        rows=[{'city':'US location not specified','state':'','country':'US'}]
    return rows

def classify(title):
    if re.search(r'research (engineer|scientist)',title,re.I): return 'Research'
    if re.search(r'data scient|applied scientist',title,re.I): return 'Applied Data Science'
    if re.search(r'infrastructure|inference|systems|platform|compiler|kernel',title,re.I): return 'ML Infrastructure'
    if re.search(r'AI (?:engineer|applications|agents)|applied AI|agent builder',title,re.I): return 'AI Applications'
    return 'ML Engineering'

def screen(item, job, already):
    title = job.get('title','').strip()
    sid = str(job.get('id',''))
    if sid in already or DISALLOWED.search(title) or not CORE_TITLE.search(title): return None
    # Traditional game "AI" may refer to scripted behavior, not ML.
    if item['company']=='Epic Games' and not re.search(r'machine learning|ML|neural',title,re.I): return None
    source_location = (job.get('location') or {}).get('name','')
    loc = locations(source_location)
    if not loc: return None
    body = clean(job.get('content',''))
    if not MODEL_WORDS.search(body): return None
    lines = [line for line in body.splitlines() if line.strip()]
    # Positive experience floors are screened across the complete description.
    # Excluding even preferred 3+ floors is conservative and documented.
    years = []
    for line in lines:
        if re.search(r'company|founded|customers|over the past|for over',line,re.I) and len(line)>350: continue
        years += [int(m.group(1)) for m in EXPERIENCE.finditer(line)]
        years += [int(x) for x in re.findall(r'(?<!\d)(\d{1,2})\s*\+\s*(?:years?|yrs?)\b',line,re.I)]
        if re.search(r'\b(?:three|four|five|six|seven|eight|nine|ten)\s*\+?\s+years?\b',line,re.I) and re.search(r'experience',line,re.I): return None
    if any(y>2 for y in years): return None
    skills=[]
    for skill in SKILLS:
        if re.search(r'(?<!\w)'+re.escape(skill)+r'(?!\w)',body,re.I): skills.append({'name':skill,'level':'mentioned','alternativeGroup':None})
    # Complex education/experience alternatives are not guessed from a regex.
    # The discovery tier remains unclear until source-by-source pathway review.
    requirement_note = ('The source contains a '+str(min(years))+'-year experience reference; its required/preferred status and degree-specific alternatives need confirmation.' if years else 'No numeric experience floor was recognized by the automated screen. This does not establish a zero-experience pathway.')
    family=classify(title)
    summary={'Research':'Research and experimentation on machine-learning methods or model behavior.','Applied Data Science':'Data analysis, statistical modeling or applied machine learning for organizational decisions.','ML Infrastructure':'Engineering systems for machine-learning training, deployment or inference.','AI Applications':'Engineering applications or workflows that use AI models.','ML Engineering':'Engineering and evaluating machine-learning models or model-powered systems.'}[family]
    remote=bool(re.search(r'\bremote\b',source_location,re.I))
    url=job.get('absolute_url')
    if not url or not url.startswith('https://'): return None
    return {'id':f"{item['board']}-greenhouse-{sid}",'company':item['company'],'title':title,'url':url,'applyUrl':url,'source':'Greenhouse','sourceId':sid,'verifiedAt':NOW,'publishedAt':None,'deadline':None,'roleFamily':family,'tags':[],'locations':loc,'locationText':source_location,'remote':remote,'remoteScope':'unspecified','workplace':'Remote' if remote else 'Not stated','newgradStatus':'unclear','qualificationPaths':[{'degrees':[],'minYears':None,'experienceType':'not stated','graduation':'Not stated','graduationYears':[],'evidence':requirement_note}],'startYears':[],'startWindow':'Not stated','skills':skills,'salary':[],'sponsorship':'Not stated','sponsorshipNote':'Not reviewed in this discovery layer.','summary':summary,'newgradEvidence':'Graduate eligibility has not been established. This role is a broader discovery lead, separately selectable from reviewed graduate pathways.','aiEvidence':f'The official title identifies {family} work and the description contains model-specific terminology. Technical responsibilities must be checked in the linked source.','qualificationNote':requirement_note,'reviewLevel':'automated-discovery','reviewNote':'Listed with a role-specific URL in the current official Greenhouse public board. Automatically screened for US locations, AI titles and experience references; compound qualification paths, salary, employment terms and graduate eligibility have not been individually reviewed.','experienceReferences':sorted(set(years))}

def main():
    boards=json.loads((ROOT/'research/public-boards.json').read_text())
    already=set()
    for name in ['greenhouse','large_employers','other_employers','expanded_enterprise','expanded_ats']:
        for j in json.loads((ROOT/'research'/f'{name}.json').read_text())['jobs']:
            already.add(str(j['sourceId']))
    jobs=[];coverage=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for item, endpoint, payload, error in executor.map(get_board,boards):
            candidates=[]
            if payload:
                candidates=[j for raw in payload.get('jobs',[]) if (j:=screen(item,raw,already))]
                jobs.extend(candidates)
            coverage.append({'company':item['company'],'url':endpoint,'checkedAt':NOW,'status':'inaccessible' if error else 'verified roles' if candidates else 'no qualifying roles','qualifyingCount':len(candidates),'note':f'Official board retrieval failed ({error}); no conclusion about hiring.' if error else f"Automated screen of {len(payload.get('jobs',[]))} current board postings produced {len(candidates)} additional discovery leads. Zero means none passed this conservative screen, not no graduate hiring. No per-employer quota; curated IDs excluded from this layer."})
    out={'jobs':jobs,'coverage':coverage,'methodNotes':{'review':'Automated discovery, not verified graduate eligibility. No senior titles, internships or recognized 3+ year experience references. Strict AI titles and explicit US locations. Complex qualification paths remain unparsed; every lead is unclear. No salary or sponsorship inference.','coverage':'All returned board titles/descriptions screened by the published script. No per-company cap. Conservative gates can exclude viable jobs and do not make the sample a census.'}}
    (ROOT/'research/broad_greenhouse.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'discoveryLeads':len(jobs),'employers':len(set(j['company'] for j in jobs)),'boards':len(coverage),'unavailable':sum(c['status']=='inaccessible' for c in coverage)}))

if __name__=='__main__':main()
