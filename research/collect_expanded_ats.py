"""Collect a broad, source-backed early-career US AI/ML slice from public ATS APIs."""
import concurrent.futures, json, re, html
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent
OUT = ROOT / "expanded_ats.json"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

# These are discovery boards, not claims that every board has a qualifying role.
GREENHOUSE = {
    "Motional":"motional", "Roblox":"roblox", "Glean":"gleanwork", "xAI":"xai",
    "AI2":"thealleninstitute", "DoorDash":"doordashusa", "Reddit":"reddit",
    "Stripe":"stripe", "Airbnb":"airbnb", "Instacart":"instacart", "Lyft":"lyft",
    "Uber":"uber", "Pinterest":"pinterest", "Datadog":"datadog", "Databricks":"databricks",
    "Figma":"figma", "Discord":"discord", "Brex":"brex", "Cloudflare":"cloudflare",
    "MongoDB":"mongodb", "Asana":"asana", "Okta":"okta", "Twilio":"twilio",
    "Affirm":"affirm", "Block":"block", "Toast":"toast", "Duolingo":"duolingo",
    "Faire":"faire", "Flexport":"flexport", "Samsara":"samsara", "Chime":"chime",
    "Epic Games":"epicgames", "Komodo Health":"komodohealth", "Anthropic":"anthropic",
    "Scale AI":"scaleai", "Snorkel AI":"snorkelai", "Nextdoor":"nextdoor",
}
ASHBY = {
    "Anyscale":"anyscale", "Character.AI":"character", "Cerebras":"cerebras", "Cognition":"cognition",
    "Cursor":"cursor", "Decagon":"decagon", "Embedding VC":"embedding-vc", "Fireworks AI":"fireworks",
    "Genmo":"genmo", "Handshake":"handshake", "Harvey":"harvey", "Koah Labs":"koahlabs",
    "Liquid AI":"liquid-ai", "Luma":"lumaai", "Mistral":"mistral.ai", "Netic":"netic",
    "Perplexity":"perplexity", "Physical Intelligence":"physicalintelligence", "Plenful":"plenful",
    "Poolside":"poolside", "Prime Intellect":"primeintellect", "Reflection AI":"reflectionai",
    "Replit":"replit", "Sierra":"sierra", "Thinking Machines Lab":"thinkingmachines",
    "Tavus":"tavus", "Writer":"writer", "Epsilon Health":"epsilon-health", "OpenAI":"openai",
}
LEVER = {"Agtonomy":"agtonomy", "Hive":"hive", "Tahoe Therapeutics":"tahoebio-ai", "PlusAI":"plus-2", "Labelbox":"labelbox", "Benchling":"benchling", "Samsara Lever":"samsara"}

# IDs were selected after reading complete public posting descriptions. A job is
# admitted only when this table supplies an early-career/new-grad rationale.
S = {
    # Ashby
    ("Ashby","anyscale","1cf38233-8aa0-47f8-9d85-65ce27bc3047"):("unclear","ML Infrastructure",["LLM","inference"],["Bachelor","Master","PhD"],None,"not stated","Not stated","Distributed LLM inference on Ray/vLLM with no numeric minimum stated; verify experience level.","Role designs and optimizes batch/online LLM inference and distributed systems at scale."),
    ("Ashby","character","449bf7c1-41d7-47a4-89a7-0ee0b31f5918"):("unclear","Research Engineer",["LLM","post-training","inference"],["PhD"],None,"research","Not stated","Posting labels the role All Industry Levels and requires PhD/equivalent; no numeric industry minimum is stated.","Post-training research covers reinforcement learning, transformers, GPU training/serving, and large generative models."),
    ("Ashby","cerebras","987d7f64-c957-4c8f-b89d-2f9d64738507"):("explicit","ML Infrastructure",["inference","distributed training"],["Bachelor","Master"],0,"not stated","Not stated","Title says New College Grad; full-time in-office CoDesign/NextGen role requires BS/MS and CPU/GPU simulation exposure.","Co-design work targets AI-chip training/inference performance and CPU/GPU simulation."),
    ("Ashby","cerebras","9c7da4b8-446b-4bf2-8d07-23241590bf2e"):("explicit","ML Infrastructure",["inference","distributed training"],["Bachelor","Master","PhD"],0,"not stated","Not stated","Title says Kernel Engineer - New Grad; JD accepts BS/MS/PhD and coursework, research, or projects.","Duties implement and validate machine-learning and linear-algebra kernels for the wafer-scale AI engine."),
    ("Ashby","cursor","d0e5b41d-84ab-4887-bd3a-55589b11dd7b"):("explicit","AI Applications",["LLM","agents"],["Bachelor","Master"],0,"not stated","2027","Title says Software Engineer, New Grad 2027; internships or equivalent experience welcome.","JD assigns product and infrastructure work on AI agents, Cursor, and related developer tools."),
    ("Ashby","decagon","a8ff946f-d6b1-4059-bc9f-fe6b11504f2f"):("explicit","AI Applications",["LLM","agents","evaluation"],["Bachelor","Master"],0,"not stated","2027","Title says New Grad (2027 Start); coursework, internships, or personal projects accepted.","New-grad teams build customer-facing AI agents, agent engineering, and multimodal/distributed systems."),
    ("Ashby","embedding-vc","5c8433ea-c7e6-4350-bbd5-2889e7fdb2b1"):("early-career","AI Applications",["LLM","agents"],["Bachelor","Master"],None,"not stated","Not stated","Title says AI Engineer (Early Career); JD asks for limited professional experience and project/open-source evidence.","Role builds AI product systems; the early-career posting specifically calls for a builder portfolio."),
    ("Ashby","fireworks","ad58a098-ef75-4a4b-8475-55c2653213ef"):("explicit","ML Infrastructure",["inference","distributed training"],["PhD"],0,"research","2026","Title says 2026 PhD New Grad; PhD completion within six months or by December 2026.","Systems role builds schedulers, storage, networks, GPU clusters, and low-latency inference infrastructure."),
    ("Ashby","fireworks","82b41f4a-a945-4aee-a1fd-1ef9ab513e58"):("explicit","Research Engineer",["LLM","inference","distributed training"],["PhD"],0,"research","2026","Title says 2026 PhD New Grad; PhD completion within six months or by December 2026.","Research advances LLM and multimodal systems, model efficiency, accuracy, and scalability."),
    ("Ashby","fireworks","0c78aede-7c21-4d1e-88f1-f309deb9819e"):("explicit","ML Infrastructure",["inference","distributed training","LLM"],["Bachelor","Master"],0,"not stated","2027","Title says New Grad (BS/MS); degree completed within six months or before end of 2026, with Summer 2027 path.","Engineering placement spans inference, training/fine-tuning, distributed systems, cloud, APIs, and AI applications."),
    ("Ashby","genmo","9b5477f4-97af-4aaa-b855-910c982ce191"):("early-career","Research Engineer",["CV","LLM","inference"],["Bachelor","Master"],2,"research","Not stated","Title says New Grad, but minimum qualifications also require 2+ years ML experience; recent graduates are welcome.","Research develops and trains generative models with PyTorch/TensorFlow, computer vision, and deployment."),
    ("Ashby","liquid-ai","c7251e1b-d7bf-4d03-8b9e-1382743bef2c"):("early-career","Research Engineer",["LLM","evaluation"],["PhD"],1,"research","Not stated","JD gives a PhD path with 1+ year relevant experience; MS path requires 3+ years and BS 5+.","ML research engineer trains, evaluates, and iterates models with PyTorch and synthetic data/evaluation work."),
    ("Ashby","netic","f2d170eb-c4c3-4715-9d2e-84dd4fe857c8"):("explicit","AI Applications",["LLM","agents","evaluation"],["Bachelor","Master"],0,"not stated","2026","Title says FDE New Grad 2026-2027; JD targets graduates starting winter 2026 through summer 2027.","Build and deploy multimodal AI agents using LLM/TTS APIs, fine-tuning, RAG, vector databases, and evaluations."),
    ("Ashby","netic","bab5d1e5-e31b-42f0-9cef-334b1f17fed3"):("explicit","AI Applications",["LLM","agents"],["Bachelor","Master"],0,"not stated","2026","Title says Full-Stack Software Engineer, Product - New Grad 2026-2027.","Build agentic product features for Netic's AI platform across APIs, data models, front end, and monitoring."),
    ("Ashby","netic","d9bcb6a2-0e54-4cb3-baec-43f2d74db18f"):("explicit","ML Infrastructure",["LLM","agents","evaluation"],["Bachelor","Master"],0,"not stated","2026","Title says Software Engineer, Agent Platform - New Grad 2026-2027; projects/coursework accepted.","Build orchestration, routing, supervision, sandboxes, and evaluation tooling for multi-agent workflows."),
    ("Ashby","replit","b5e81ae0-06f9-4798-8988-2d06ca936dbc"):("explicit","AI Applications",["LLM","agents"],["Bachelor","Master"],0,"not stated","2027","Title says Software Engineer - New Grad (2027); full-time Foster City role.","Role contributes to Replit's AI coding and agent product surfaces; source title and product context are AI-specific."),
    ("Ashby","sierra","149f368c-52d5-408f-ba26-ad888f318a00"):("explicit","AI Applications",["LLM","agents"],["Bachelor","Master"],0,"not stated","2027","Title says Software Engineer, Agent (New Grad 2027).", "Build production AI agents and agent infrastructure for customer workflows."),
    ("Ashby","sierra","d9c445da-c7b4-43a3-8d71-d367681c3015"):("explicit","AI Applications",["LLM","agents"],["Bachelor","Master"],0,"not stated","2027","APX title and program are explicitly New Grad 2027; undergraduate/Master's completion by June 2027.","Rotational program builds and ships AI agents with customers and Sierra's platform."),
    ("Ashby","thinkingmachines","9d863c78-80c0-44cd-a574-d1330e125398"):("early-career","ML Infrastructure",["LLM","evaluation"],["Bachelor"],2,"industry","Not stated","Minimum is Bachelor's and two years post-grad software/ML experience, exclusive of internships.","Build evaluation, benchmark, grader, and model-quality infrastructure for language/multimodal models."),
    ("Ashby","thinkingmachines","72fe46e4-a772-4ebb-a413-53e4f1a8273e"):("early-career","ML Infrastructure",["LLM","distributed training"],["Bachelor"],2,"industry","Not stated","Minimum is Bachelor's and two years post-grad software/ML experience, exclusive of internships.","Build research tools, experiment systems, model-training workflows, and observability."),
    ("Ashby","cognition","439404bb-3185-4d22-b6df-4a5e39a510d6"):("unclear","AI Applications",["LLM","agents"],["Bachelor","Master"],None,"not stated","Not stated","Full-time Product Engineer posting has no numeric minimum in the captured text; industry experience is described as a strong plus.","Build AI-agent product surfaces, agent harnesses, and developer experiences for Devin."),
    ("Ashby","mistral.ai","cce4be06-ac42-4c69-9bcd-7f5dca6f5e3c"):("early-career","AI Applications",["LLM","agents"],["Bachelor","Master"],2,"industry","Not stated","JD requires a CS/software degree and 2+ years as a technical individual contributor.","Research Engineer integrates AI models into customer software and improves product/model capabilities."),
    ("Ashby","mistral.ai","2ec2dacd-1117-479b-a4c1-efa9df530798"):("early-career","AI Applications",["LLM","agents","inference"],["Master","PhD"],2,"industry","Not stated","JD requires a Master's/PhD in AI/data science and 2+ years as an AI technical contributor.","Forward-deployed ML role implements fine-tuning, RAG, agents, LLM deployment, and inference integrations."),
    # Greenhouse
    ("Greenhouse","roblox","8027588"):("explicit","ML Infrastructure",["robotics","inference","distributed training"],["PhD"],0,"research","2026","Title says PhD Early Career and JD seeks exceptional PhD new graduates for 2026.","Embodied-AI/NPCs and ML-platform tracks cover serving, model registry, orchestration, and training/inference control planes."),
    ("Greenhouse","roblox","8027587"):("explicit","ML Infrastructure",["robotics","inference","distributed training"],["PhD"],0,"research","2026","Title says PhD Early Career and JD seeks exceptional PhD new graduates for 2026.","Embodied-AI/NPCs and ML-platform tracks cover serving, model registry, orchestration, and training/inference control planes."),
    ("Greenhouse","gleanwork","4711484005"):("early-career","Machine Learning Engineering",["LLM","recommendation/search","evaluation"],["Bachelor"],2,"industry","Not stated","JD requires 2+ years and production systems experience; no new-grad claim.","ML role works on LLM applications, NLP, search, retrieval, recommendations, evaluation, and agent systems."),
    ("Greenhouse","gleanwork","4006735005"):("early-career","Machine Learning Engineering",["LLM","recommendation/search"],["Bachelor"],2,"industry","Not stated","JD requires 2+ years plus a BA/BS; retained as a clearly bounded early-career adjacent role.","ML search-quality role works on search, recommendation, NLP, and large ML systems."),
    ("Greenhouse","xai","5193037007"):("early-career","ML Infrastructure",["inference","distributed training"],["Bachelor","Master","PhD"],2,"industry","Not stated","JD requires 2+ years in production/distributed/GPU/ML infrastructure; no new-grad claim.","Build ML platforms and training infrastructure for large-scale deep-learning applications."),
    ("Greenhouse","thealleninstitute","7899565"):("early-career","ML Infrastructure",["LLM","agents","evaluation"],["Bachelor"],2,"industry","Not stated","JD requires 2+ years in agentic and ML training/evaluation/inference infrastructure.","Build infrastructure for AI research assistants, agents, model training, evaluation, inference, and deployment."),
}

def fetch(kind, slug):
    if kind == "Greenhouse": url=f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    elif kind == "Ashby": url=f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    else: url=f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        req=Request(url,headers={"User-Agent":"Mozilla/5.0 AI-Career-Compass/1.0"})
        with urlopen(req,timeout=12) as r: return (r.status, json.loads(r.read()), url)
    except Exception as e: return (None, str(e), url)

def clean(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()
def locations(j):
    if "location" in j and isinstance(j["location"],dict): return j["location"].get("name","")
    if "location" in j: return str(j.get("location") or "") + ("; " + "; ".join(x.get("location","") for x in j.get("secondaryLocations",[])) if j.get("secondaryLocations") else "")
    return j.get("locationText","") or "; ".join(j.get("categories",{}).get("location",[]) if isinstance(j.get("categories"),dict) else [])
def usloc(s): return bool(re.search(r"(?i)(united states|usa|remote|\bCA\b|\bNY\b|\bWA\b|\bTX\b|\bMA\b|\bIL\b|\bCO\b|\bPA\b|\bVA\b|\bMD\b|san francisco|new york|seattle|boston|palo alto|sunnyvale|san mateo|foster city|redwood city|mountain view)",s))
def salary(c):
    m=re.search(r"\$\s*([0-9][0-9,]{3,})\s*(?:-|–|to)\s*\$?\s*([0-9][0-9,]{3,})",c)
    return [{"min":int(m.group(1).replace(',','')),"max":int(m.group(2).replace(',','')),"currency":"USD","period":"year","scope":"US base salary"}] if m else []
def cities(loc):
    out=[]
    known={"San Francisco":"CA","San Mateo":"CA","Sunnyvale":"CA","Palo Alto":"CA","Redwood City":"CA","Foster City":"CA","Mountain View":"CA","Seattle":"WA","New York":"NY","Boston":"MA","Pittsburgh":"PA","Las Vegas":"NV","Chicago":"IL","Austin":"TX","Washington":"DC"}
    for part in re.split(r";|\|",loc):
        m=re.search(r"([A-Za-z .'-]+),\s*([A-Z]{2})",part)
        if m: out.append({"city":m.group(1).strip(),"state":m.group(2),"country":"US"})
        else:
            for city,state in known.items():
                if city.lower() in part.lower(): out.append({"city":city,"state":state,"country":"US"}); break
    return out or [{"city":"United States","state":"US","country":"US"}]

def main():
    boards=[("Greenhouse",c,b) for c,b in GREENHOUSE.items()]+[("Ashby",c,b) for c,b in ASHBY.items()]+[("Lever",c,b) for c,b in LEVER.items()]
    results={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        fut={ex.submit(fetch,k,b):(k,c,b) for k,c,b in boards}
        for f in concurrent.futures.as_completed(fut): results[fut[f]]=f.result()
    jobs=[]; coverage=[]
    for (kind,company,slug),(status,payload,source_url) in results.items():
        arr=(payload.get("jobs",[]) if kind in ("Greenhouse","Ashby") and isinstance(payload,dict) else payload if isinstance(payload,list) else [])
        byid={str(j.get("id")):j for j in arr}
        selected=[(key,spec) for key,spec in S.items() if key[0]==kind and key[1]==slug]
        count=0
        for _,spec in selected:
            key=next(k for k in S if k[0]==kind and k[1]==slug and k[2] not in {j["sourceId"] for j in jobs}) if False else None
        for (k_kind,k_slug,sid), spec in S.items():
            if k_kind!=kind or k_slug!=slug or str(sid) not in byid: continue
            j=byid[str(sid)]; title=j.get("title",""); desc=clean(j.get("descriptionPlain") or j.get("description") or j.get("content") or ""); loc=locations(j)
            if not usloc(loc) or str(j.get("employmentType", "FullTime")).lower() not in ("fulltime","full-time","") or re.search(r"(?i)intern|co-op|contract",title): continue
            st,rf,tags,degrees,miny,exptype,grad,ng,ai=spec
            url=j.get("jobUrl") or j.get("absolute_url") or j.get("hostedUrl") or (f"https://jobs.lever.co/{slug}/{sid}")
            apply=j.get("applyUrl") or j.get("apply_url") or url
            q={"degrees":degrees,"minYears":miny,"experienceType":exptype,"graduation":grad,"graduationYears":[int(y) for y in re.findall(r"20(?:26|27)",grad)],"evidence":ng}
            jobs.append({"id":f"{company.lower().replace(' ','-')}-{kind.lower()}-{sid}","company":company,"title":title,"url":url,"applyUrl":apply,"source":kind,"sourceId":str(sid),"verifiedAt":NOW,"publishedAt":j.get("publishedAt"),"deadline":None,"roleFamily":rf,"tags":tags,"locations":cities(loc),"remote":bool(j.get("isRemote")) or "remote" in loc.lower(),"workplace":"Remote" if "remote" in loc.lower() else ("On-site" if "on-site" in desc.lower() or "in-office" in desc.lower() else "Not stated"),"locationText":loc,"newgradStatus":st,"qualificationPaths":[q],"startYears":[],"startWindow":"Not stated","skills":[{"name":t,"level":"mentioned","alternativeGroup":None} for t in tags],"salary":salary(desc),"sponsorship":"Not stated","sponsorshipNote":"Not stated","summary":ai,"newgradEvidence":ng,"aiEvidence":ai,"qualificationNote":ng,"reviewNote":f"Official {kind} public posting API returned the role ID, full-time posting, US location, full description, and application URL at {NOW}."})
            count+=1
        cov_status="inaccessible" if status is None else ("verified roles" if count else "no qualifying roles")
        note=("API request failed; availability unknown." if status is None else f"Queried official {kind} board; {len(arr)} listed postings inspected and {count} selected after US/full-time/AI/early-career evidence checks.")
        coverage.append({"company":company,"url":source_url,"checkedAt":NOW,"status":cov_status,"note":note,"qualifyingCount":count})
    OUT.write_text(json.dumps({"jobs":jobs,"coverage":coverage,"methodNotes":{"newgradStatus":{"explicit":"title/program explicitly targets new graduates","zero-experience":"explicit 0-2 or equivalent early path","early-career":"explicit bounded 1-2 year path without new-grad label","unclear":"AI role has no stated numeric minimum but early-career eligibility is not explicit"},"selection":"Only listed full-time US AI/ML roles in S were emitted; all other queried boards remain in coverage."}},indent=2,ensure_ascii=False)+"\n")
    print(f"wrote {len(jobs)} jobs and {len(coverage)} coverage rows to {OUT}")
if __name__ == "__main__": main()
