"""Reproducible Greenhouse snapshot for the AI Career Compass Greenhouse slice."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

OUT = Path(__file__).with_name("greenhouse.json")
CHECKED = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def job(board, source_id, company, title, location, role_family, tags, degree, years,
        experience_type, graduation, summary, newgrad, ai, skills=(), salary=(),
        workplace="On-site", sponsorship="Not stated", sponsorship_note="Not stated",
        qualification_note="", remote=False):
    url = f"https://job-boards.greenhouse.io/{board}/jobs/{source_id}"
    city, state = location
    return {
        "id": f"{company.lower().replace(' ', '-')}-greenhouse-{source_id}",
        "company": company, "title": title, "url": url, "applyUrl": url,
        "source": "Greenhouse", "sourceId": str(source_id), "verifiedAt": CHECKED,
        "publishedAt": None, "deadline": None, "roleFamily": role_family,
        "tags": list(tags), "locations": [{"city": city, "state": state, "country": "US"}],
        "remote": remote, "workplace": workplace,
        "locationText": location[0] + (", " + location[1] if location[1] else ""),
        "newgradStatus": "explicit", "qualificationPaths": [{
            "degrees": list(degree), "minYears": years, "experienceType": experience_type,
            "graduation": graduation, "graduationYears": [], "evidence": qualification_note
        }], "startYears": [], "startWindow": graduation,
        "skills": [{"name": x, "level": "mentioned", "alternativeGroup": None} for x in skills],
        "salary": [{"min": a, "max": b, "currency": "USD", "period": "year", "scope": "US base salary"} for a,b in salary],
        "sponsorship": sponsorship, "sponsorshipNote": sponsorship_note,
        "summary": summary, "newgradEvidence": newgrad, "aiEvidence": ai,
        "qualificationNote": qualification_note,
        "reviewNote": "Official Greenhouse board API returned this ID with the exact title, US location, full JD, and an Apply button at verification time."
    }

JOBS = [
job("newsbreak", 4700278006, "NewsBreak", "Applied AI Engineer, Advertising Agents (New Grad)", ("Mountain View", "CA"), "AI Applications", ["LLM", "evaluation"], ["Bachelor", "Master"], 0, "not stated", "2026", "Build LLM and agent technology for an AI-driven advertising account hosting and optimization platform.", "The JD asks for a recent graduate and a degree completed recently or within six months; it says no professional experience is required.", "Responsibilities include building LLM/agent systems and an AI advertising platform.", ("Python", "LLM", "agents", "PyTorch"), ((125000,175000),), qualification_note="Degree path is Bachelor's/Master's in CS, AI, Data Science or related; no professional experience required; projects/research are considered."),
job("newsbreak", 4694899006, "NewsBreak", "NewsBreak Venture, AI Growth Intelligence Engineer (New Grad）", ("Mountain View", "CA"), "AI Applications", ["LLM", "evaluation"], ["Bachelor", "Master"], 0, "not stated", "Not stated", "Develop AI growth intelligence systems and software for NewsBreak Venture.", "Title explicitly identifies New Grad; the JD accepts a recent graduate or up to about two years of experience.", "The role builds AI growth intelligence products and applies software/ML techniques to growth systems.", ("Python", "SQL", "machine learning"), (), qualification_note="Bachelor's or Master's in CS, Software Engineering or related; recent graduate or up to ~2 years experience path."),
job("newsbreak", 4615879006, "NewsBreak", "Software Engineer, ML Infra (Junior & New Grad)", ("Mountain View", "CA"), "ML Infrastructure", ["inference", "distributed training", "recommendation/search"], ["Master", "PhD"], 0, "not stated", "Not stated", "Build infrastructure for offline/online training, model serving, feature serving, and ML pipeline monitoring.", "Title explicitly says Junior & New Grad; the JD provides a Master's/PhD alternative to the Bachelor's plus 2+ years path.", "The role trains, serves, monitors, and supports recommendation and advertising models.", ("Python", "PyTorch", "TensorFlow", "AWS", "GCP"), ((125000,175000),), qualification_note="Bachelor's plus 2+ years OR Master's/PhD; do not collapse these alternatives into a zero-experience Bachelor's path."),
job("idmeuniversityrecruiting", 7986505003, "ID.me", "Summer 2027 - Data Scientist (New Grad)", ("Mountain View", "CA"), "Applied Data Science", ["recommendation/search", "evaluation"], ["Master"], 0, "research", "May/June 2027", "Use experiments, fraud analytics, and ML models to detect identity fraud and account takeover.", "Title says New Grad; the JD requires graduation in May/June 2027 from a Master's program.", "Core work designs ML solutions, builds detection models, and evaluates fraud patterns.", ("Python", "SQL", "scikit-learn", "TensorFlow", "PyTorch"), (), qualification_note="Master's in Data Science, Applied Mathematics, Statistics, CS, or related; coursework, research projects, or internships count as data experience."),
job("togetherai", 5211582007, "Together AI", "Software Engineer, New Grad (2027)", ("San Francisco", "CA"), "ML Infrastructure", ["inference", "distributed training"], ["Bachelor", "Master"], 0, "not stated", "2027", "Join ML, platform, infrastructure, or inference teams building scalable systems and performance-critical code.", "The JD calls the role early-career, says it is ideal for recent graduates, and targets the 2027 class.", "The placement teams include Machine Learning, Infrastructure, and Inference; the role contributes to Together's model platform.", ("Python", "C++", "Kubernetes", "CUDA"), ((150000,160000),), qualification_note="Recent-graduate language is explicit; team placement is determined among ML/platform/infrastructure/inference."),
job("scaleai", 4730836005, "Scale AI", "Software Engineer - New Grad", ("San Francisco", "CA"), "ML Infrastructure", ["LLM", "evaluation", "inference"], ["Bachelor"], 0, "not stated", "Not stated", "Ship customer-facing software and AI infrastructure products for visualizing, querying, and exploring data used to build and deploy AI systems.", "Title and opening paragraph explicitly identify a New Grad Software Engineer opportunity.", "The JD describes Scale's AI data/full-stack products and specifically lists new AI infrastructure products.", ("Python", "TypeScript", "React", "SQL"), ((124000,162000),), qualification_note="Bachelor's degree or equivalent in CS, EECS, Computer Engineering, or Statistics; product engineering experience may be coursework/project based."),
job("nuro", 7351066, "Nuro", "Software Engineer, AI Platform - New Grad", ("Mountain View", "CA"), "ML Infrastructure", ["inference", "robotics", "distributed training"], ["Bachelor", "Master"], 0, "not stated", "Before July 2026", "Build software for Nuro's AI platform supporting Level 4 autonomy, model development, and deployment.", "Title explicitly says New Grad; the JD requires a degree candidate graduating before July 2026.", "The AI Platform role supports a physical-AI autonomy stack and model platform.", ("Python", "C++", "Kubernetes", "Docker"), ((145000,170000),), qualification_note="Bachelor's or Master's in CS, EE, Robotics or related; graduation before July 2026 required."),
job("waymo", 7488508, "Waymo", "Machine Learning Engineer Perception LLM/VLM (PhD, New Grad)", ("Mountain View", "CA"), "Research Engineer", ["LLM", "CV", "evaluation", "inference"], ["PhD"], 0, "research", "Not stated", "Research and deploy perception models using LLM/VLM techniques for autonomous driving.", "Title explicitly identifies a PhD New Grad role; the JD accepts a relevant Master's or equivalent and prefers PhD-level model experience.", "Perception work covers spatial-temporal representations, multimodal models, fine-tuning, and evaluation for the Waymo Driver.", ("Python", "PyTorch", "TensorFlow", "C++"), (), qualification_note="PhD new-grad title is explicit; JD still lists Master's/equivalent as minimum and research/model experience as preferred."),
job("trueanomalyinc", 5221970007, "True Anomaly", "Software Engineer I, Perception (New Grad)", ("Denver", "CO"), "Machine Learning Engineering", ["CV", "robotics", "inference"], ["Bachelor", "Master"], 0, "research", "Not stated", "Develop perception software for autonomous spacecraft, including computer vision and estimation systems.", "Title explicitly identifies New Grad; requirements are degree plus coursework in computer vision and estimation theory.", "The role develops perception algorithms for autonomous spacecraft and mission systems.", ("C++", "Python", "computer vision", "estimation"), (), qualification_note="Bachelor's or Master's in CS, EE, Robotics, Aerospace or related; coursework in CV and estimation required."),
job("trueanomalyinc", 5221560007, "True Anomaly", "Software Engineer I, Data Science (New Grad)", ("Denver", "CO"), "Applied Data Science", ["evaluation", "anomaly detection"], ["Bachelor", "Master"], 0, "research", "Not stated", "Build predictive models and anomaly detection analyses over spacecraft manufacturing and telemetry data.", "Title explicitly identifies New Grad and the requirements center on degree/coursework rather than prior full-time experience.", "The JD requires predictive modeling and anomaly detection for spacecraft health and mission telemetry.", ("Python", "SQL", "scikit-learn", "time series"), ((75000,80000),), qualification_note="Bachelor's or Master's in data science, statistics, industrial engineering, applied mathematics, operations research, or related; internship/project experience is preferred."),
job("machindustries", 4390274009, "Mach Industries", "December 2026 New Graduate Engineer, Software / GNC", ("Huntington Beach", "CA"), "AI Applications", ["robotics", "evaluation"], ["Bachelor", "Master", "PhD"], 0, "not stated", "December 2026", "Develop software for autonomous defense platforms, including higher-level autonomy applications and simulation/testing infrastructure.", "Title explicitly says New Graduate and the JD requires graduating by end of December 2026.", "The JD specifically assigns autonomy applications for autonomous defense platforms and simulation/testing infrastructure used to validate autonomous-system performance; it does not claim ML model development.", ("C++", "Python", "Rust", "simulation"), (), qualification_note="Bachelor's, Master's, or PhD in CS, CE, EE, or related; capstone, research, internship, student-team, or personal software project accepted."),
job("machindustries", 4401441009, "Mach Industries", "May 2027 New Graduate Engineer, GNC & Modeling and Simulation", ("Huntington Beach", "CA"), "AI Applications", ["robotics", "evaluation"], ["Bachelor", "Master", "PhD"], 0, "not stated", "May 2027", "Develop and test guidance, navigation, and control algorithms, filters, and state-estimation methods for autonomous aircraft and missile systems.", "Title explicitly says New Graduate and the job targets May 2027 graduates.", "The JD directly assigns autonomous-vehicle GNC algorithms, navigation filters, state estimation, Monte Carlo simulation, and hardware/flight testing; it does not claim ML model development.", ("Python", "C++", "MATLAB", "simulation"), (), qualification_note="Bachelor's, Master's, or doctoral degree in aerospace, mechanical, electrical, or computer engineering or related; coursework/projects in controls, estimation, navigation, robotics, or flight mechanics."),
job("freeformfuturecorp", 7826634003, "Freeform", "Software Engineer (New Grad December 2026)", ("Los Angeles", "CA"), "ML Infrastructure", ["inference", "robotics"], ["Bachelor"], 0, "not stated", "December 2026", "Develop software systems, GPU/FPGA compute, controls, and geometry pipelines that power autonomous metal-printing factories.", "Title explicitly says New Grad December 2026; the JD is a full-time on-site role for a new graduate.", "The software supports autonomous manufacturing and AI-native factory systems, including GPU/HPC pipelines.", ("C++", "Python", "GPU", "FPGA"), ((125000,150000),), qualification_note="Bachelor's in CS or computer engineering from an ABET-accredited program; AI responsibility is embedded in autonomous factory systems."),
job("freeformfuturecorp", 7895902003, "Freeform", "Software Engineer (New Grad Summer 2027)", ("Los Angeles", "CA"), "ML Infrastructure", ["inference", "robotics"], ["Bachelor"], 0, "not stated", "Summer 2027", "Develop software systems, GPU/FPGA compute, controls, and geometry pipelines that power autonomous metal-printing factories.", "Title explicitly says New Grad Summer 2027; the JD is a full-time on-site role for a new graduate.", "The software supports autonomous manufacturing and AI-native factory systems, including GPU/HPC pipelines.", ("C++", "Python", "GPU", "FPGA"), ((125000,150000),), qualification_note="Bachelor's in CS or computer engineering from an ABET-accredited program; AI responsibility is embedded in autonomous factory systems."),
]

# Final evidence gate and qualification-path corrections. Freeform's postings
# mention an AI-native company and autonomous factory, but the duties are
# controls, data acquisition, geometry, and general factory software rather
# than model work or AI infrastructure; keep them in coverage only.
JOBS = [j for j in JOBS if j["company"] != "Freeform"]
# Both True Anomaly new-grad postings are explicitly three-month temporary
# engagements with possible conversion, so they are outside the full-time
# contract despite their strong perception/data-science duties.
JOBS = [j for j in JOBS if j["company"] != "True Anomaly"]
for j in JOBS:
    if j["id"] == "newsbreak-greenhouse-4700278006":
        j["startWindow"] = "Not stated"
        j["qualificationPaths"][0]["graduation"] = "Recently completed or within the next 6 months (year not stated)"
    if j["id"] == "newsbreak-greenhouse-4615879006":
        j["qualificationPaths"] = [
            {"degrees": ["Bachelor"], "minYears": 2, "experienceType": "industry", "graduation": "Not stated", "graduationYears": [], "evidence": "Bachelor's degree plus 2+ years of relevant work experience."},
            {"degrees": ["Master", "PhD"], "minYears": 0, "experienceType": "not stated", "graduation": "Not stated", "graduationYears": [], "evidence": "The JD gives a Master's/PhD alternative without a stated experience minimum; projects and research are recorded separately."},
        ]
        j["qualificationNote"] = "Two explicit alternatives: Bachelor's plus 2+ years industry experience OR Master's/PhD with no stated minimum; do not flatten these paths."
    if j["id"] == "waymo-greenhouse-7488508":
        j["qualificationPaths"] = [
            {"degrees": ["Master"], "minYears": 5, "experienceType": "industry", "graduation": "Not stated", "graduationYears": [], "evidence": "Body requires 5+ years of machine-learning experience and lists a Master's degree as minimum."},
            {"degrees": ["PhD"], "minYears": 5, "experienceType": "industry", "graduation": "Not stated", "graduationYears": [], "evidence": "Title says PhD, New Grad, but body lists PhD as preferred while retaining the 5+ years requirement; eligibility is unclear."},
        ]
        j["qualificationNote"] = "Title says PhD, New Grad, but the body requires 5+ years of ML experience, lists Master's as minimum, and PhD as preferred; no Master's new-grad inference made."
    if j["id"] == "id.me-greenhouse-7986505003":
        j["qualificationPaths"][0]["graduationYears"] = [2027]
    if j["id"] == "nuro-greenhouse-7351066":
        j["qualificationPaths"][0]["graduationYears"] = [2026]
    if j["id"] == "scale-ai-greenhouse-4730836005":
        j["qualificationPaths"][0]["graduationYears"] = [2026, 2027]
        j["qualificationPaths"][0]["graduation"] = "Fall 2026 or Spring 2027"
        j["startWindow"] = "Fall 2026 or Spring 2027"
    if j["id"] == "together-ai-greenhouse-5211582007":
        j["qualificationPaths"][0]["graduationYears"] = [2027]
    if j["id"] == "mach-industries-greenhouse-4390274009":
        j["qualificationPaths"][0]["graduationYears"] = [2026, 2027]
        j["qualificationPaths"][0]["graduation"] = "By end of December 2026 or January 2027"
    if j["id"] == "mach-industries-greenhouse-4401441009":
        j["qualificationPaths"][0]["graduationYears"] = [2027]
    # A zero minimum records the explicit new-grad/no-stated-industry path;
    # coursework, research, internships, and projects remain in evidence.
    for p in j["qualificationPaths"]:
        if p["minYears"] == 0:
            p["experienceType"] = "not stated"

COVERAGE = [
    {"company": c, "url": f"https://job-boards.greenhouse.io/{b}", "checkedAt": CHECKED, "status": status, "note": note, "qualifyingCount": n}
    for c,b,status,n,note in [
        ("NewsBreak","newsbreak","verified roles",3,"Three active US AI/new-grad postings verified."),
        ("ID.me","idmeuniversityrecruiting","verified roles",1,"Data Scientist qualifies; SDE new-grad posting was reviewed but not included because AI duties were not core."),
        ("Together AI","togetherai","verified roles",1,"One active US new-grad role with ML/inference placement."),
        ("Scale AI","scaleai","verified roles",1,"One active US new-grad software role with explicit AI infrastructure duties."),
        ("Nuro","nuro","verified roles",1,"One active US AI Platform new-grad role."),
        ("Waymo","waymo","verified roles",1,"One active US PhD new-grad perception LLM/VLM role."),
        ("True Anomaly","trueanomalyinc","no qualifying roles",0,"Two new-grad perception/data-science postings were reviewed but both state they are 3-month temporary engagements with possible conversion."),
        ("Mach Industries","machindustries","verified roles",2,"Two active US new-graduate autonomy/GNC roles."),
        ("Freeform","freeformfuturecorp","no qualifying roles",0,"Two new-grad software postings were reviewed; duties focus on controls, data acquisition, geometry, and factory software without a core model/AI-infrastructure responsibility."),
        ("Databricks","databricks","no qualifying roles",0,"AI FDE US posting explicitly says it is not intended for new-graduate or entry-level applicants; APM is not an AI technical role."),
        ("Datadog","datadog","no qualifying roles",0,"No active US full-time AI/new-grad role with explicit eligibility found in the board snapshot."),
        ("Figure","figure","no qualifying roles",0,"No active US full-time AI/new-grad role with explicit eligibility found in the board snapshot."),
        ("Anthropic","anthropic","no qualifying roles",0,"US research/engineering roles reviewed were experienced hires; Fellows postings were program listings rather than a qualifying full-time job."),
        ("Applied Intuition","appliedintuition","inaccessible",0,"Greenhouse board slug returned HTTP 404; no inference about job availability."),
    ]
]

OUT.write_text(json.dumps({"jobs": JOBS, "coverage": COVERAGE}, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {len(JOBS)} jobs and {len(COVERAGE)} coverage rows to {OUT}")
