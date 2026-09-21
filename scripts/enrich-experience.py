#!/usr/bin/env python3
"""Build source-grounded experience evidence from ignored ATS snapshots.

This intentionally emits short excerpts only. It never uses the pre-existing
experienceReferences field, company history, preferred-only years, or degree
duration as an experience-level signal.
"""
import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))
from experience import classify_experience

YEAR_RE = re.compile(r"(?<![\d.])(\d{1,2})(?:\s*(?:[-–—]|to)\s*(\d{1,2}))?\s*(?:\+\s*)?(?:years?|yrs?)(?:\s+of)?\s+([A-Za-z][A-Za-z /,&-]{0,70})?\s*experience\b", re.I)
OPEN_RE = re.compile(r"(?:open to|consider(?:ing)?|welcome)\s+(?:candidates?\s+)?(?:at|from)\s+(?:multiple|all|any|different)\s+(?:seniority|experience|career)\s+levels?|(?:experience|years? of experience|level)\s+(?:required\s+)?(?:will )?(?:vary|varies|depend(?:s)?|correlate)", re.I | re.S)
SECTION_RE = re.compile(r"\b(?:required|minimum|basic|qualifications?|what you(?:'ll| will) bring|you have|must have|requirements?)\b", re.I)
PREFERRED_RE = re.compile(r"\b(?:preferred|nice to have|bonus|plus|ideally|desired|a plus|helpful)\b", re.I)
PROFESSIONAL_RE = re.compile(r"\b(?:professional|relevant|industry|software|engineering|research|machine learning|technical|commercial|full[- ]time|post[- ]degree|ML|AI|data science|post[- ]training|fine[- ]tuning)\b", re.I)
ACTION_YEAR_RE = re.compile(r"(?<![\d.])(\d{1,2})(?:\s*(?:[-–—]|to)\s*(\d{1,2}))?\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:building|designing|developing|shipping|working|leading|managing|operating|delivering|with|in (?:a )?technical role|demonstrated strength)\b", re.I)
DEGREE_RE = re.compile(r"\b(?:ph\.?d\.?|m\.?s\.?|b\.?s\.?|master|doctorate|bachelor|degree)\b", re.I)
COMPANY_RE = re.compile(r"\b(?:founded|years?\s+(?:old|in business))\b|\b(?:company|team|business|organization)\s+(?:has|have|brings?|with)\b", re.I)

def clean(value):
    value = html.unescape(str(value or ""))
    value = re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>", " ", value, flags=re.I | re.S)
    value = re.sub(r"</(?:p|li|h\d|div)>|<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]*>", " ", value)
    return "\n".join(re.sub(r"\s+", " ", x).strip() for x in value.splitlines() if x.strip())

def excerpt(text, match=None):
    line = (text if match is None else match.group(0)).strip()
    line = re.sub(r"\s+", " ", line)
    return line[:297].rstrip() + ("..." if len(line) > 300 else "")

def extract_evidence(description):
    text = clean(description)
    # Preserve degree alternatives while splitting prose into sentences.
    text = re.sub(r"\bPh\.\s*D\.?", "PhD", text, flags=re.I)
    text = re.sub(r"\b([MB])\.\s*S\.?", r"\1S", text, flags=re.I)
    lines = [x for x in re.split(r"\n|(?<=[.!?])\s+", text) if x.strip()]
    preferred_section = False
    line_context = []
    scope_evidence = None
    for line in lines:
        # A preferred degree/location inside one bullet does not turn every
        # subsequent required bullet into a preference. Only headings do that.
        heading=line.strip().lstrip("-• ").rstrip(":?").strip()
        if len(heading)<85 and re.match(r"^(?:(?:our|the) )?(?:preferred qualifications?|nice[- ]to[- ]haves?|bonus(?: qualifications?)?|desired qualifications?|helpful extras)\b",heading,re.I):
            preferred_section=True
        elif len(heading)<100 and re.search(r"^(?:(?:required|minimum|minimal|basic)\s+)?(?:qualifications?|requirements?)$|^(?:what (?:you|we)|you (?:will|have|are)|about (?:you|the role)|responsibilities|in this role)",heading,re.I):
            preferred_section=False
        line_context.append((line, preferred_section))
        match = OPEN_RE.search(line)
        if match:
            scope_evidence = {"evidenceType": "scope", "open_level": excerpt(line), "excerpt": excerpt(line)}

    candidates = []
    for line, preferred_section in line_context:
        for match in [*YEAR_RE.finditer(line), *ACTION_YEAR_RE.finditer(line)]:
            sentence = line.strip()
            if preferred_section or re.search(r"\b(?:salary|compensation|pay range|benefits)\b", sentence, re.I) or COMPANY_RE.search(sentence) or re.search(r"\b(?:our|the)\s+(?:team|company|organization)\b", sentence, re.I):
                continue
            # Preferred/bonus experience is deliberately excluded. Degree
            # alternatives are retained as ambiguous evidence, never reduced
            # to the smallest number.
            if PREFERRED_RE.search(sentence):
                continue
            # Keep numeric experience alternatives even when the same sentence
            # mentions degree alternatives. They are comparable when all paths
            # map to the same broad bucket; the classifier handles mixed paths.
            if not (PROFESSIONAL_RE.search(sentence) or SECTION_RE.search(sentence) or re.search(r"\byears?\s+of\s+(?:relevant\s+)?experience\b", sentence, re.I)):
                continue
            # A degree can replace years entirely; the numeric branch alone
            # does not establish the level of the whole posting.
            degree_alternative = re.search(r"\b(?:PhD|MS|BS|doctorate|masters?(?:'s)?(?: degree)?|bachelors?(?:'s)?(?: degree)?)\b[^.;]{0,60}\bor\s+(?:at least\s+)?\d", sentence, re.I) or re.search(r"\byears?[^.;]{0,70}\bor\s+(?:a\s+)?(?:PhD|MS|BS|doctorate|masters?|bachelors?)\b", sentence, re.I)
            if degree_alternative and len(list(YEAR_RE.finditer(sentence))) < 2:
                return {"evidenceType":"ambiguous-requirements", "excerpt":excerpt(sentence), "reason":"A degree can replace the stated experience; no single level was inferred."}
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else None
            if high is not None and low <= 2 < high:
                return {"evidenceType":"ambiguous-requirements", "requirementYears":[low,high], "excerpt":excerpt(sentence), "reason":"The stated experience range spans entry and senior buckets; no single level was inferred."}
            candidates.append((low, high, sentence, match))
    if candidates:
        # Degree alternatives are usable when every path lands in the same
        # broad bucket. Mixed entry/senior alternatives remain ambiguous.
        values = sorted({v for low, high, _, _ in candidates for v in ((low, high) if high else (low,))})
        if len(candidates) == 1:
            low, high, sentence, match = candidates[0]
            return {"evidenceType": "required-experience", "required_years": low, "requirementYears": values, "excerpt": excerpt(sentence), "evidence": excerpt(sentence)}
        combined = "Multiple required experience statements: " + "; ".join(excerpt(x[2]) for x in candidates)
        # Separate required bullets are normally conjunctive: the highest
        # floor governs. Explicit ``or`` keeps alternatives ambiguous when
        # they span entry and senior buckets.
        if len({x[2] for x in candidates})>1 and not any(DEGREE_RE.search(x[2]) for x in candidates) or not re.search(r"\bor\b", " ".join(x[2] for x in candidates), re.I):
            low = max(x[0] for x in candidates)
            return {"evidenceType": "required-experience", "required_years": low, "requirementYears": values, "excerpt": excerpt(candidates[0][2]), "reason": "Multiple required statements are conjunctive; the highest stated floor governs.", "evidence": combined[:300]}
        buckets = {"entry" if low <= 2 else "senior" for low, _, _, _ in candidates}
        if len(buckets) == 1:
            low = min(x[0] for x in candidates)
            return {"evidenceType": "required-experience", "required_years": low, "requirementYears": values, "excerpt": excerpt(candidates[0][2]), "reason": "Alternative required paths fall in the same broad experience bucket.", "evidence": combined[:300]}
        return {"evidenceType": "ambiguous-requirements", "requirementYears": values, "excerpt": excerpt(candidates[0][2]), "reason": "Alternative required paths span different broad experience buckets; no single level was inferred.", "evidence": combined[:300]}

    # Specific candidate scope can resolve generic multi-level boilerplate.
    scoped_lines=[]
    for line, preferred_section in line_context:
        if preferred_section or PREFERRED_RE.search(line):
            continue
        if re.search(r"\b(?:our (?:team|company|org(?:anization)?|track record)|the (?:team|company|org(?:anization)?)|salary|compensation|pay range|everyone|our culture|for (?:tech |technical )?leadership roles)\b", line, re.I):
            continue
        scoped_lines.append(line)
    # Cross-team technical leadership, rather than company-wide product prose.
    for line in scoped_lines:
        if re.search(r"\b(?:set|define|shape|own|lead)\b.{0,80}\b(?:technical|engineering|architectur\w*)\b.{0,80}\b(?:strategy|direction)\b.{0,80}\b(?:across|multiple|cross[- ]team|company[- ]wide|organization[- ]wide)\b", line, re.I):
            return {"evidenceType":"role-scope", "scope_level":"staff", "scope_evidence":excerpt(line), "excerpt":excerpt(line)}
    for line in scoped_lines:
        independent = re.search(r"\b(?<!your )(?<!their )(?:own|owns|ownership|lead|led)\b.{0,90}\b(?:end[- ]to[- ]end|end to end|start to finish)\b|\b(?:independently|self[- ]directed|minimal (?:guidance|supervision)|autonomy)\b.{0,100}\b(?:own|lead|drive|deliver|projects?|research|systems?)\b", line, re.I)
        track_record = re.search(r"\b(?:proven|strong|extensive|demonstrated)\s+(?:prior\s+)?(?:track record|experience)\b.{0,130}\b(?:shipping|deploying|operating|maintaining|building)\b.{0,100}\b(?:production|at scale|large[- ]scale)\b|\btrack record\b.{0,100}\b(?:production|production[- ]grade)\b", line, re.I)
        if independent or track_record:
            return {"evidenceType":"role-scope", "scope_level":"senior", "scope_evidence":excerpt(line), "excerpt":excerpt(line)}
    if scope_evidence:
        return scope_evidence
    return {"evidenceType": "none", "excerpt": None, "reason": "No clear title or required-experience signal was found in the cached description."}

def source_jobs():
    for pattern, source in (("qa/source-cache/*.json", "Greenhouse"), ("qa/ashby-cache/*.json", "Ashby")):
        for path in sorted(ROOT.glob(pattern)):
            try: payload = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError): continue
            for job in payload.get("jobs", []):
                if source == "Greenhouse":
                    sid, url, title, body = str(job.get("id", "")), job.get("absolute_url"), job.get("title", ""), job.get("content", "")
                else:
                    sid, url, title, body = str(job.get("id", "")), job.get("jobUrl"), job.get("title", ""), job.get("descriptionPlain") or job.get("descriptionHtml", "")
                if sid and url: yield source, sid, url, title, body

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "research/experience-evidence.json"))
    args = parser.parse_args()
    data = json.loads((ROOT / "dist/data.json").read_text())
    cached = {(source, sid): (url, body) for source, sid, url, title, body in source_jobs()}
    rows = {}
    for job in data.get("jobs", []):
        key = (job.get("source"), str(job.get("sourceId", "")))
        # Keep every published posting in the evidence artifact. Cached
        # official descriptions enable requirement/scope inference; postings
        # without a local cache still retain title/curated classification and
        # explicit provenance fields for the downstream schema.
        url, body = cached.get(key, (job.get("url"), None))
        evidence = extract_evidence(body) if body else {"evidenceType": "none", "excerpt": None, "reason": "No cached official description was available for this posting."}
        result = classify_experience(job.get("title"), job.get("newgradStatus"), job.get("experienceReferences"), evidence)
        row = {"id": job["id"], "source": job.get("source"), "sourceId": str(job.get("sourceId")), "sourceUrl": url, "sourceTitle": job.get("title"), "sourceVerifiedAt": job.get("verifiedAt"), "evidenceType": evidence["evidenceType"], "experienceLevel": result["experienceLevel"], "experienceLevelBasis": result["experienceLevelBasis"], "experienceLevelEvidence": result["experienceLevelEvidence"]}
        if evidence.get("requirementYears") is not None: row["requirementYears"] = evidence["requirementYears"]
        if evidence.get("required_years") is not None: row["classifiedRequirementYears"] = evidence["required_years"]
        if evidence.get("excerpt"): row["excerpt"] = evidence["excerpt"]
        rows[job["id"]] = row
    out = {"schemaVersion": 1, "method": "Cached official Greenhouse/Ashby descriptions; title and curated overrides precede conservative required-experience evidence. Preferred-only, company-history, degree-duration and existing experienceReferences numbers are excluded.", "jobs": rows}
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"published": len(data.get("jobs", [])), "matched": len(rows), "levels": dict(Counter(r["experienceLevel"] for r in rows.values())), "basis": dict(Counter(r["experienceLevelBasis"] for r in rows.values()))}, ensure_ascii=False))

if __name__ == "__main__": main()
