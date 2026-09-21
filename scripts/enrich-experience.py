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
PROFESSIONAL_RE = re.compile(r"\b(?:professional|relevant|industry|software|engineering|research|machine learning|technical|commercial|full[- ]time|post[- ]degree)\b", re.I)
DEGREE_RE = re.compile(r"\b(?:ph\.?d\.?|m\.?s\.?|b\.?s\.?|master|doctorate|bachelor|degree)\b", re.I)
COMPANY_RE = re.compile(r"\b(?:founded|customers?|employees?|company|business|years?\s+(?:old|in business))\b", re.I)

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
    lines = [x for x in re.split(r"\n|(?<=[.!?])\s+", text) if x.strip()]
    preferred_section = False
    line_context = []
    scope_evidence = None
    for line in lines:
        if re.search(r"\b(?:preferred|nice to have|bonus|desired|helpful)\b", line, re.I) and not YEAR_RE.search(line):
            preferred_section = True
        if re.search(r"\b(?:required|minimum|basic)\s+(?:qualifications?|requirements?)\b", line, re.I):
            preferred_section = False
        line_context.append((line, preferred_section))
        match = OPEN_RE.search(line)
        if match:
            scope_evidence = {"evidenceType": "scope", "open_level": excerpt(line), "excerpt": excerpt(line)}

    candidates = []
    for line, preferred_section in line_context:
        for match in YEAR_RE.finditer(line):
            sentence = line.strip()
            if preferred_section or COMPANY_RE.search(sentence) or re.search(r"\b(?:our|the)\s+(?:team|company|organization)\b", sentence, re.I):
                continue
            # Preferred/bonus experience is deliberately excluded. Degree
            # alternatives are retained as ambiguous evidence, never reduced
            # to the smallest number.
            if PREFERRED_RE.search(sentence):
                continue
            if DEGREE_RE.search(sentence) and re.search(r"\b(?:or|equivalent|in lieu|substitute)\b", sentence, re.I):
                continue
            if not (PROFESSIONAL_RE.search(sentence) or SECTION_RE.search(sentence)):
                continue
            low = int(match.group(1))
            high = int(match.group(2)) if match.group(2) else None
            candidates.append((low, high, sentence, match))
    if candidates:
        # Multiple required alternatives/ranges remain a list, allowing the
        # consumer to see the ambiguity rather than manufacturing a floor.
        values = sorted({v for low, high, _, _ in candidates for v in ((low, high) if high else (low,))})
        if len(candidates) == 1:
            low, high, sentence, match = candidates[0]
            return {"evidenceType": "required-experience", "required_years": low, "requirementYears": values, "excerpt": excerpt(sentence), "evidence": excerpt(sentence)}
        return {"evidenceType": "ambiguous-requirements", "requirementYears": values, "excerpt": excerpt(candidates[0][2]), "reason": "Multiple required experience statements are present; no single floor was inferred.", "evidence": "Multiple required experience statements: " + "; ".join(excerpt(x[2]) for x in candidates)[:270]}

    # A concrete requirement takes precedence over generic level-dependent boilerplate.
    if scope_evidence:
        return scope_evidence

    for line, preferred_section in line_context:
        if preferred_section:
            continue
        if re.search(r"\b(?:experience|background|track record)\b", line, re.I) and not COMPANY_RE.search(line) and not re.search(r"\b(?:our|the)\s+(?:team|company|organization)\b", line, re.I) and not PREFERRED_RE.search(line):
            if re.search(r"\b(?:field of study|coursework|training|degree|equivalent)\b", line, re.I):
                continue
            if re.search(r"\b(?:or|equivalent|in lieu|substitute)\b", line, re.I) and DEGREE_RE.search(line):
                continue
            if re.search(r"\b(?:professional|relevant|industry|prior)\s+experience\b|\b(?:proven|demonstrated)\s+(?:professional\s+)?(?:experience|track record)\b|\btrack record\b|\bdeep background\b|\bexperienced (?:engineers?|scientists?|candidates?)\b", line, re.I):
                return {"evidenceType": "explicit-experience", "experienced": excerpt(line), "excerpt": excerpt(line)}
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
        if key not in cached: continue
        url, body = cached[key]
        evidence = extract_evidence(body)
        result = classify_experience(job.get("title"), job.get("newgradStatus"), job.get("experienceReferences"), evidence)
        row = {"id": job["id"], "source": job.get("source"), "sourceId": str(job.get("sourceId")), "sourceUrl": url, "sourceTitle": job.get("title"), "sourceVerifiedAt": job.get("verifiedAt"), "evidenceType": evidence["evidenceType"], "experienceLevel": result["experienceLevel"], "experienceLevelBasis": result["experienceLevelBasis"], "experienceLevelEvidence": result["experienceLevelEvidence"]}
        if evidence.get("requirementYears") is not None: row["requirementYears"] = evidence["requirementYears"]
        if evidence.get("excerpt"): row["excerpt"] = evidence["excerpt"]
        rows[job["id"]] = row
    out = {"schemaVersion": 1, "method": "Cached official Greenhouse/Ashby descriptions; title and curated overrides precede conservative required-experience evidence. Preferred-only, company-history, degree-duration and existing experienceReferences numbers are excluded.", "jobs": rows}
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"published": len(data.get("jobs", [])), "matched": len(rows), "levels": dict(Counter(r["experienceLevel"] for r in rows.values())), "basis": dict(Counter(r["experienceLevelBasis"] for r in rows.values()))}, ensure_ascii=False))

if __name__ == "__main__": main()
