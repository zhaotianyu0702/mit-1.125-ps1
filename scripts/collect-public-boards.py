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
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from experience import classify_experience
CACHE = ROOT / 'qa/source-cache'
CACHE.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat()
STATE_CODES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
STATE_NAMES = dict(pair.split(':') for pair in 'Alabama:AL|Alaska:AK|Arizona:AZ|Arkansas:AR|California:CA|Colorado:CO|Connecticut:CT|Delaware:DE|District of Columbia:DC|Florida:FL|Georgia:GA|Hawaii:HI|Idaho:ID|Illinois:IL|Indiana:IN|Iowa:IA|Kansas:KS|Kentucky:KY|Louisiana:LA|Maine:ME|Maryland:MD|Massachusetts:MA|Michigan:MI|Minnesota:MN|Mississippi:MS|Missouri:MO|Montana:MT|Nebraska:NE|Nevada:NV|New Hampshire:NH|New Jersey:NJ|New Mexico:NM|New York:NY|North Carolina:NC|North Dakota:ND|Ohio:OH|Oklahoma:OK|Oregon:OR|Pennsylvania:PA|Rhode Island:RI|South Carolina:SC|South Dakota:SD|Tennessee:TN|Texas:TX|Utah:UT|Vermont:VT|Virginia:VA|Washington:WA|West Virginia:WV|Wisconsin:WI|Wyoming:WY'.split('|'))
CITIES = {'San Francisco':'CA','San Francisco Bay Area':'CA','Mountain View':'CA','San Mateo':'CA','Redwood City':'CA','Palo Alto':'CA','Menlo Park':'CA','Santa Clara':'CA','San Jose':'CA','Sunnyvale':'CA','Foster City':'CA','San Diego':'CA','Los Angeles':'CA','Irvine':'CA','Seattle':'WA','Bellevue':'WA','Kirkland':'WA','New York':'NY','Brooklyn':'NY','Boston':'MA','Cambridge':'MA','Pittsburgh':'PA','Philadelphia':'PA','Washington, DC':'DC','Austin':'TX','Dallas':'TX','Houston':'TX','Atlanta':'GA','Chicago':'IL','Denver':'CO','Boulder':'CO','Raleigh':'NC','Durham':'NC','Madison':'WI','Ann Arbor':'MI','Detroit':'MI','Minneapolis':'MN','Salt Lake City':'UT','Phoenix':'AZ','Miami':'FL','Orlando':'FL','Nashville':'TN','Portland, OR':'OR','Arlington, VA':'VA','Reston':'VA'}
CORE_TITLE = re.compile(r'\b(machine learning|MLOps|ML Ops|GenAI|ML|AI|artificial intelligence|deep learning|LLM|NLP|computer vision|perception|applied scientist|data scient(?:ist|ce)|research (?:scientist|engineer)|inference|reinforcement learning|post[- ]training|training/inference|AI/ML)\b', re.I)
NONTECH_AI_TITLE = re.compile(r'(?:\b(?:AI|ML|GenAI)\b.*\b(?:product|program|project)\s+manager\b|\b(?:product|program|project)\s+manager\b.*\b(?:AI|ML|GenAI)\b)', re.I)
DISALLOWED = re.compile(r'\b(intern(?:ship)?|co[- ]op|contractor|contract|temporary|part[- ]time|freelance|fellow(?:s|ship)?|postdoc(?:toral)?|residency|talent pool|designer|technical writer|solutions (?:architect|engineer)|vendor|economist|recruiter|account executive|sales|trainer|policy|human rating|human rater|red teamer|people research(?:er)?)\b', re.I)
MODEL_WORDS = re.compile(r'\b(machine learning|deep learning|neural|language models?|LLMs?|reinforcement learning|computer vision|NLP|model training|model inference)\b', re.I)
EXPERIENCE = re.compile(r'(?<![\d.])(\d{1,2})(?:\s*(?:[-–—]|to)\s*(\d{1,2}))?\s*(?:\+\s*)?(?:years?|yrs?)(?:\s+of)?\s+(?:[A-Za-z/ -]{0,65})?experience\b', re.I)
WORD_YEARS = re.compile(r'\b(one|two|three|four|five|six|seven|eight|nine|ten)(?:\s*\+)?\s+years?(?:\s+of)?\s+(?:[A-Za-z/ -]{0,65})?experience\b', re.I)
WORD_NUMBERS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10}
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
    # Parse each location atom independently. A foreign atom must never cause
    # a same-named US city (notably Cambridge) to be emitted.
    foreign = re.compile(r'\b(?:United Kingdom|UK|London|Canada|Poland|Germany|France|India|Singapore|Australia|Ireland|Israel|Japan|China|Brazil|Mexico)\b', re.I)
    parts = [part.strip() for part in re.split(r'[;|•]', str(text or '')) if part.strip()]
    parts = [part for part in parts if not foreign.search(part)]
    text = '; '.join(parts)
    rows = []
    for city, state in CITIES.items():
        if re.search(r'\b'+re.escape(city)+r'\b',text,re.I):
            rows.append({'city':city,'state':state,'country':'US'})
    # Uppercase abbreviations only: "or" is not Oregon.
    for city, state in re.findall(r'([A-Za-z .\'-]+),\s*([A-Z]{2})\b', text):
        if state in STATE_CODES and not any(r['state'] == state and r['city'].lower() in city.lower() for r in rows):
            rows.append({'city':city.strip(),'state':state,'country':'US'})
    # Full state names support postings outside the better-known city list.
    # Keep the city unknown rather than manufacture a metro from free text.
    for part in parts:
        state_text = re.sub(r'Washington,?\s*(?:DC|D\.C\.)\b', '', part, flags=re.I)
        for name, code in sorted(STATE_NAMES.items(), key=lambda pair: -len(pair[0])):
            if re.search((r'(?<!West )' if name=='Virginia' else '')+r'\b'+re.escape(name)+r'\b', state_text, re.I) and not any(row['state']==code for row in rows):
                rows.append({'city':'City not specified','state':code,'country':'US'})
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

def nontechnical_title(title):
    """Reject business/product/program titles while retaining technical roles.

    Context words such as AI, inference, or infrastructure do not turn a
    product, partnerships, customer-success, or program role into engineering.
    Conversely, an engineering/science title may mention marketing, operations,
    or enablement as its product area and remains eligible.
    """
    technical = re.search(r'\b(?:engineer(?:ing)?|scient(?:ist|ific)|research(?:er)|research\s+(?:scientist|engineer)|developer|architect)\b', title, re.I)
    hard = re.search(r'\b(?:product\s+manager|product\s+management|program\s+manager|program\s+management|technical\s+account\s+manager|account\s+manager|commodity\s+sourcing)\b', title, re.I)
    if hard or re.search(r'\bresearch\s+lab\s+strategy\s*&\s*operations\b', title, re.I):
        return True
    if re.search(r'\b(?:partnerships?|customer\s+success|success\s+manager|product\s+marketing|customer\s+enablement)\b', title, re.I) and not technical:
        return True
    if re.search(r'\b(?:marketing|enablement|operations|revenue|strategy|strategist|finance|accounting|adoption|transformation)\b', title, re.I) and not technical:
        return True
    if re.search(r'\bplatform\s+manager\b', title, re.I) and not technical:
        return True
    return False

def screen(item, job, already):
    title = job.get('title','').strip()
    sid = str(job.get('id',''))
    if sid in already or DISALLOWED.search(title) or NONTECH_AI_TITLE.search(title) or nontechnical_title(title) or not CORE_TITLE.search(title): return None
    # Traditional game "AI" may refer to scripted behavior, not ML.
    if item['company']=='Epic Games' and not re.search(r'machine learning|ML|neural',title,re.I): return None
    source_location = (job.get('location') or {}).get('name','')
    loc = locations(source_location)
    if not loc: return None
    body = clean(job.get('content',''))
    if not MODEL_WORDS.search(body): return None
    lines = [line for line in body.splitlines() if line.strip()]
    # Numeric experience references are retained as evidence across the complete
    # description. They do not establish a required floor or exclude a role.
    years = []
    for line in lines:
        if re.search(r'\b(?:company|founded|customers)\b', line, re.I) and re.search(r'\b(?:years?|yrs?)\b.*\bexperience\b', line, re.I): continue
        for match in EXPERIENCE.finditer(line):
            years.append(int(match.group(1)))
            if match.group(2):
                years.append(int(match.group(2)))
        years.extend(WORD_NUMBERS[m.group(1).lower()] for m in WORD_YEARS.finditer(line))
    years = sorted(set(years))
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
    return {'id':f"{item['board']}-greenhouse-{sid}",'company':item['company'],'title':title,'url':url,'applyUrl':url,'source':'Greenhouse','sourceId':sid,'verifiedAt':NOW,'publishedAt':None,'deadline':None,'roleFamily':family,'tags':[],'locations':loc,'locationText':source_location,'remote':remote,'remoteScope':'unspecified','workplace':'Remote' if remote else 'Not stated','newgradStatus':'unclear','qualificationPaths':[{'degrees':[],'minYears':None,'experienceType':'not stated','graduation':'Not stated','graduationYears':[],'evidence':requirement_note}],'startYears':[],'startWindow':'Not stated','skills':skills,'salary':[],'sponsorship':'Not stated','sponsorshipNote':'Not reviewed in this discovery layer.','summary':summary,'newgradEvidence':'Graduate eligibility has not been established. This role is a broader discovery lead, separately selectable from reviewed graduate pathways.','aiEvidence':f'The official title identifies {family} work and the description contains model-specific terminology. Technical responsibilities must be checked in the linked source.','qualificationNote':requirement_note,'reviewLevel':'automated-discovery','reviewNote':'Listed with a role-specific URL in the current official Greenhouse public board. Automatically screened for US locations, AI titles and experience references; compound qualification paths, salary, employment terms and graduate eligibility have not been individually reviewed.','experienceReferences':years, **classify_experience(title, 'unclear', years)}

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
    out={'jobs':jobs,'coverage':coverage,'methodNotes':{'review':'Automated discovery, not verified graduate eligibility. Senior, staff, lead and management titles are retained; internships, contracts and nontechnical categories are excluded. Numeric experience references are evidence only and do not establish a minimum. Strict AI titles and explicit US locations. Complex qualification paths remain unparsed; every lead is unclear. No salary or sponsorship inference.','coverage':'All returned board titles/descriptions screened by the published script. No per-company cap. Conservative gates can exclude viable jobs and do not make the sample a census.'}}
    (ROOT/'research/broad_greenhouse.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'discoveryLeads':len(jobs),'employers':len(set(j['company'] for j in jobs)),'boards':len(coverage),'unavailable':sum(c['status']=='inaccessible' for c in coverage)}))

if __name__=='__main__':main()
