#!/usr/bin/env python3
"""Collect Ashby public boards through the shared conservative screen."""
import concurrent.futures
import importlib.util
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/broad_ashby.json"
NOW = datetime.now(timezone.utc).isoformat()

# Fixed public board registry makes this collection reproducible on any machine.
BOARDS = {item['company']: item['slug'] for item in json.loads((ROOT / 'research/ashby-boards.json').read_text())}
EXCLUDE = re.compile(r'recruit(?:er|ing)|account executive|sales|policy|red team|human rating|human rater|trainer|annotation|solutions architect|applied ai architect|people research', re.I)

SCREEN_PATH = ROOT / "scripts/collect-public-boards.py"
spec = importlib.util.spec_from_file_location("public_boards_screen", SCREEN_PATH)
screen_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen_mod)

def fetch(company, board):
    endpoint = f"https://api.ashbyhq.com/posting-api/job-board/{board}"
    try:
        req = Request(endpoint, headers={"User-Agent": "AI-Career-Compass research/1.0"})
        with urlopen(req, timeout=25) as response:
            payload = json.loads(response.read())
            cache = ROOT / 'qa/ashby-cache'
            cache.mkdir(parents=True, exist_ok=True)
            (cache / f'{board}.json').write_text(json.dumps(payload))
            return company, board, endpoint, payload, None
    except Exception as error:
        return company, board, endpoint, None, type(error).__name__

def location_text(job):
    vals = [str(job.get("location") or "")]
    vals.extend(str(x.get("location") or "") for x in job.get("secondaryLocations") or [])
    return "; ".join(x for x in vals if x)

def adapt(job):
    # The shared screen intentionally consumes the Greenhouse-shaped subset.
    desc = job.get("descriptionHtml") or job.get("descriptionPlain") or ""
    return {
        "id": str(job.get("id", "")),
        "title": job.get("title", ""),
        "content": desc,
        "location": {"name": location_text(job)},
        "absolute_url": job.get("jobUrl", ""),
    }

def existing_ids():
    old = set()
    for path in ROOT.joinpath("research").glob("*.json"):
        if path.name == "broad_ashby.json":
            continue
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for job in data.get("jobs", []):
            if not isinstance(job, dict):
                continue
            if job.get("sourceId") is not None:
                old.add(str(job["sourceId"]))
            if job.get("url"):
                old.add(str(job["url"]))
    return old

def main():
    already = existing_ids()
    jobs, coverage = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda x: fetch(*x), BOARDS.items()))
    for company, board, endpoint, payload, error in results:
        raw = payload.get("jobs", []) if isinstance(payload, dict) else []
        selected = []
        if not error:
            for source in raw:
                if EXCLUDE.search(source.get("title", "")):
                    continue
                if source.get("isListed") is False:
                    continue
                if str(source.get("employmentType", "")).lower() != "fulltime":
                    continue
                item = {"company": company, "board": board}
                candidate = screen_mod.screen(item, adapt(source), already)
                if not candidate:
                    continue
                candidate["source"] = "Ashby"
                candidate["id"] = f"{board}-ashby-{source['id']}"
                candidate["sourceId"] = str(source["id"])
                candidate["url"] = source.get("jobUrl")
                candidate["applyUrl"] = source.get("jobUrl")
                candidate["reviewNote"] = candidate["reviewNote"].replace("Greenhouse", "Ashby")
                selected.append(candidate)
            jobs.extend(selected)
        coverage.append({
            "company": company,
            "url": endpoint,
            "checkedAt": NOW,
            "status": "inaccessible" if error else ("verified roles" if selected else "no qualifying roles"),
            "note": (f"Official Ashby API request failed ({error}); availability unknown." if error else
                      f"Automated shared screen inspected {len(raw)} live postings; {len(selected)} passed listed/full-time/US/technical-AI gates across experience levels. Eligibility remains unclear until JD review."),
            "qualifyingCount": len(selected),
        })
    # A slug can be present in both maintained metadata and legacy snapshots;
    # collapse aliases by canonical Ashby URL/source ID before writing.
    unique = {}
    for job in jobs:
        unique.setdefault((job.get("sourceId"), job.get("url")), job)
    jobs = list(unique.values())
    out = {
        "jobs": jobs,
        "coverage": coverage,
        "methodNotes": {
            "source": "Official Ashby posting-api job boards; raw records adapted to the shared Greenhouse-shaped screen without modifying that screen.",
            "review": "Automated discovery only. Every emitted role is newgradStatus=unclear; no degree, salary, sponsorship, or compound qualification path is inferred. Full-time and isListed checks are taken directly from Ashby API fields.",
            "deduplication": "All existing research JSON sourceId and canonical URLs were excluded before emission.",
        },
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"jobs": len(jobs), "companies": len({j['company'] for j in jobs}), "boards": len(coverage), "inaccessible": sum(c['status'] == 'inaccessible' for c in coverage)}))

if __name__ == "__main__":
    main()
