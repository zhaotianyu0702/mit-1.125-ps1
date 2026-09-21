#!/usr/bin/env python3
"""Generate the course documentation bundle from the frozen data snapshot.

Usage:
  python3 research/generate_documents.py [--input dist/data.json]

The input is an object with ``meta``, ``jobs`` and ``coverage``.  The script
does not mutate the input or the website bundle; it writes only the five files
under ``research/artifacts``.
"""

from __future__ import annotations

import argparse
import html
import json
import statistics
from collections import Counter
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "research" / "artifacts"
NAVY = colors.HexColor("#10233f")
BLUE = colors.HexColor("#1f6feb")
LIME = colors.HexColor("#b7e35f")
MUTED = colors.HexColor("#55657a")
PALE = colors.HexColor("#edf4fb")
US_STATES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=ROOT / "dist" / "data.json")
    p.add_argument("--output", type=Path, default=ARTIFACTS)
    return p.parse_args()


def load_snapshot(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Input snapshot not found: {path}\nCreate dist/data.json or pass --input PATH.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), list) or not isinstance(data.get("coverage"), list):
        raise SystemExit("Snapshot must be an object containing list fields 'jobs' and 'coverage'.")
    data.setdefault("meta", {})
    return data


def clean(value: object, fallback: str = "Not stated") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, list):
        return ", ".join(clean(x, "") for x in value if x is not None)
    return str(value).replace("\u2013", "-").replace("\u2014", "-").replace("\u2011", "-")


def stats(data: dict) -> dict:
    jobs = data["jobs"]
    companies = {clean(j.get("company"), "Unknown") for j in jobs}
    families = Counter(clean(j.get("roleFamily"), "Not stated") for j in jobs)
    statuses = Counter(clean(j.get("newgradStatus"), "Not stated") for j in jobs)
    locations = Counter()
    for job in jobs:
        # Count each posting once per listed state. A posting may list several
        # cities in the same state, and Remote-US is its own bucket.
        # Aggregate only real US state abbreviations. Blank, country-level
        # placeholders, and Remote-US are not states; remote gets its own row.
        labels = {str(loc.get("state") or "").strip().upper() for loc in job.get("locations", [])}
        labels = {label for label in labels if label in US_STATES}
        if job.get("remote"):
            labels.add("Remote - US")
        for label in labels:
            locations[label] += 1
    salary_jobs = [j for j in jobs if j.get("salary")]
    mentioned_skills = Counter()
    for job in jobs:
        for skill in job.get("skills", []):
            label = skill.get("name") if isinstance(skill, dict) else skill
            if label:
                mentioned_skills[clean(label)] += 1
    coverage = data["coverage"]
    return {"jobs": jobs, "companies": companies, "families": families, "statuses": statuses,
            "locations": locations, "salary_jobs": salary_jobs, "coverage": coverage,
            "mentioned_skills": mentioned_skills}


def doc_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("DocTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, textColor=NAVY, alignment=TA_LEFT, spaceAfter=6),
        "sub": ParagraphStyle("DocSub", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=MUTED, spaceAfter=8),
        "h": ParagraphStyle("DocH", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=12.5, textColor=BLUE, spaceBefore=5, spaceAfter=3),
        "body": ParagraphStyle("DocBody", parent=base["BodyText"], fontName="Helvetica", fontSize=9.3, leading=11.2, textColor=NAVY, spaceAfter=3),
        "small": ParagraphStyle("DocSmall", parent=base["BodyText"], fontName="Helvetica", fontSize=8.9, leading=10.4, textColor=NAVY, spaceAfter=2),
        "foot": ParagraphStyle("DocFoot", parent=base["BodyText"], fontName="Helvetica", fontSize=6.6, leading=8, textColor=MUTED),
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LIME)
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin, 0.48 * inch, letter[0] - doc.rightMargin, 0.48 * inch)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.32 * inch, "AI Career Compass | evidence-backed public posting sample")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.32 * inch, f"Page {doc.page}")
    canvas.restoreState()


def p(text: str, style):
    return Paragraph(html.escape(clean(text)).replace("\n", "<br/>"), style)


def make_pdf(path: Path, title: str, subtitle: str, sections: list[tuple[str, str]], data: dict, compact: bool = False):
    styles = doc_styles()
    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.57 * inch, rightMargin=0.57 * inch, topMargin=0.48 * inch, bottomMargin=0.62 * inch)
    story = [Paragraph(html.escape(title), styles["title"]), Paragraph(html.escape(subtitle), styles["sub"])]
    for heading, text in sections:
        story.append(Paragraph(html.escape(heading), styles["h"]))
        story.append(Paragraph(html.escape(text).replace("\n", "<br/>"), styles["small" if compact else "body"]))
    s = stats(data)
    summary = [[p("Snapshot", styles["small"]), p(clean(data.get("meta", {}).get("snapshotDate"), "Not stated"), styles["small"])],
               [p("Postings / companies", styles["small"]), p(f"{len(s['jobs'])} / {len(s['companies'])}", styles["small"])],
               [p("Coverage checked", styles["small"]), p(str(len(s["coverage"])), styles["small"])]]
    table = Table(summary, colWidths=[1.55 * inch, 2.1 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d9ea")), ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story.insert(2, table)
    story.insert(3, Spacer(1, 5))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def write_methodology(data: dict, out: Path):
    s = stats(data)
    source_counts = Counter(clean(j.get("source"), "Not stated") for j in s["jobs"])
    status_text = ", ".join(f"{k} ({v})" for k, v in sorted(s["statuses"].items())) or "none recorded"
    sections = [
        ("Purpose", "AI Career Compass is a dated, source-backed guide to public US AI postings. Its default flow asks about background, role interests, project skills, and preferences, then shows evidence-based statuses and next steps. It does not predict hiring success or estimate the labor market."),
        ("Data and scope", f"The snapshot contains {len(s['jobs'])} deduplicated public postings from {len(s['companies'])} companies and {len(s['coverage'])} source checks. Sources: " + ", ".join(f"{k} ({v})" for k, v in sorted(source_counts.items())) + f". Pathway labels at run time: {status_text}. Fresh official ATS or company-career sources broaden US coverage."),
        ("Inclusion rules", "Curated records are selected for full-time status, a US location or explicit Remote-US scope, core AI or ML responsibilities, and an active official application route. Ashby discovery checks FullTime; Greenhouse discovery does not establish employment terms. Both remain separately labeled unclear until qualification review. Pathways are explicit new-grad, zero-experience, early-career (0-2 industry years), or unclear (graduate eligibility not established). Unknown experience is never converted to zero."),
        ("Extraction and review", "Collectors retrieve official ATS or company-career pages and normalize IDs, URLs, locations, role family, qualifications, skills, salary, and sponsorship statements. Curated records receive source-specific review; broad discovery is automated and is not presented as individually reviewed. AI assists extraction and summaries. This is agent review, not human verification. Evidence paraphrases stay linked to the official page and missing values remain unknown."),
        ("Product logic", "The four-step guide covers background, role interests, project skills, and preferences. Aligned, confirm, and gap statuses use only recorded conflicts or unknowns in stated degree, graduation, and experience conditions. Skills and preferences explain preparation and ordering but do not reject a person or create success odds. What-if skill overlap and nationwide scope are exploratory views. Remember on this device is an opt-in local browser profile; no applicant notes are imported."),
        ("Deduplication and analysis", "Company plus source ID is the primary key, followed by canonical URL when needed. Role counts are postings, not headcount. Location totals count each posting once per listed state and keep Remote - US separate; states can overlap because one posting can list several states. Salary figures are disclosed base ranges only. Missing data is not a negative answer."),
        ("Limits and provenance", "The earlier career/26fall dataset was used only for discovery and is biased toward Bay Area LLM roles; no applicant notes were imported. Fresh official sources broaden US coverage, but this remains a purposive public-posting sample rather than a census. ATS access, company selection, posting turnover, and wording differences create coverage bias, and a posting can close after the snapshot."),
        ("Reproduction", "Run generate_documents.py against the frozen dist/data.json snapshot after the expanded partitions are merged. All counts are computed at run time and the script writes the methodology, reflection, demo script, data dictionary, and keyboard-driven presentation under research/artifacts.")]
    make_pdf(out / "methodology.pdf", "Methodology", "AI Career Compass | transparent rules for a public US new-grad AI posting sample", sections, data, compact=True)


def write_reflection(data: dict, out: Path):
    s = stats(data)
    status_text = ", ".join(f"{k}: {v}" for k, v in sorted(s["statuses"].items())) or "none recorded"
    sections = [
        ("What the snapshot supports", f"The snapshot supports a reproducible description of {len(s['jobs'])} included postings across {len(s['companies'])} companies, including role family, stated US locations, qualification pathways, selected skills, disclosed base salary, and public application links. Recorded pathway categories are dynamic ({status_text})."),
        ("What the product supports", "The four-step guide helps a beginner state a background, choose role interests, add project skills, and set preferences. Results explain aligned, confirm, or gap statuses with source evidence. A what-if view can show skill overlap and a nationwide search. These are evidence and preparation aids, not ML predictions, success odds, or recruiter decisions."),
        ("AI assistance and agent review", "AI was used as an extraction aid for normalization, grouping, and short summaries. Curated records received source-specific checks for URL, title, US location, employment type where exposed, AI evidence, pathway, and application route; broad automated-discovery records were not all individually reviewed. This is agent review, not human verification: no human recruiter, employer, or independent annotator confirmed the fields. Ambiguities remain unknown or unclear."),
        ("Bias and missingness", "The earlier career/26fall dataset was used only for discovery and was biased toward Bay Area LLM roles; no applicant notes were imported. Fresh official sources broaden the sample but still favor accessible ATS pages. Salary and sponsorship disclosure are selective. A missing graduation date or experience statement stays unknown and never becomes zero."),
        ("Privacy and next improvement", "The optional remember-on-device control stores a profile in the local browser only; there is no account or server-side applicant record in this product. Repeat the snapshot, record status changes, add sampled human adjudication, and compare extraction decisions against a written log.")]
    make_pdf(out / "reflection.pdf", "Reflection and limitations", "AI Career Compass | what the evidence can and cannot say", sections, data, compact=True)


def write_markdown(data: dict, out: Path):
    s = stats(data)
    fields = [
        ("id", "Stable company-source identifier used for deduplication."), ("company", "Employer name from the official source."), ("title", "Exact official posting title."), ("url", "Canonical official posting URL."), ("applyUrl", "Official application route."), ("source/sourceId", "ATS or company-careers source and its official identifier."), ("verifiedAt", "Last source check timestamp."), ("roleFamily", "One primary AI function for mutually exclusive category charts."), ("tags", "Additional technical directions such as LLM, CV, or inference."), ("locations", "One or more source-listed US city/state/country objects."), ("workplace/remote", "Stated work arrangement; unknown remains Not stated."), ("newgradStatus", "explicit, zero-experience, early-career (0-2 industry years), or unclear (graduate eligibility not established)."), ("qualificationPaths", "Structured degree and experience alternatives; minYears is zero only when the source explicitly says no experience is needed."), ("skills", "Skill name, required/preferred/mentioned level, and alternativeGroup for OR language."), ("salary", "Disclosed base range with currency, period, and scope; bonus/equity are not merged."), ("sponsorship", "Only the source's public statement: Supported, Not offered, Conditional, or Not stated."), ("summary/evidence fields", "Short factual paraphrases supporting role, AI, qualification, and review decisions."), ("coverage", "Company-level source check; inaccessible is not treated as no qualifying jobs."), ("profile/matching", "The browser profile is opt-in and local. Statuses use recorded requirements and unknowns; skills and preferences explain preparation and order, not recruiting probability.")]
    lines = ["# Data dictionary", "", f"Generated from snapshot `{clean(data.get('meta', {}).get('snapshotDate'), 'Not stated')}` with {len(s['jobs'])} jobs and {len(s['companies'])} companies.", "", "The canonical record is one posting. One posting can have multiple qualification paths, skills, salary ranges, or US locations.", "", "| Field | Meaning |", "| --- | --- |"]
    lines += [f"| `{name}` | {meaning} |" for name, meaning in fields]
    lines += ["", "Unknown values remain explicit (`null`, empty arrays, or `Not stated`) and are never inferred as negative answers or zero experience."]
    (out / "data-dictionary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_demo(data: dict, out: Path):
    s = stats(data)
    non_ca = sum(1 for job in s["jobs"] if any(str(loc.get("state") or "").strip().upper() in US_STATES - {"CA"} for loc in job.get("locations", [])))
    remote = sum(1 for job in s["jobs"] if job.get("remote"))
    top_skill = s["mentioned_skills"].most_common(1)[0][0] if s["mentioned_skills"] else "one listed skill"
    lines = ["# Five-minute demo script", "", "Use the live site and this sequence. The companion presentation has visible Previous/Next controls, a page number, arrow-key support, and mobile swipe.", "", "## 0:00-0:40 - Start with the guided path", "Open the welcome screen. Say: this is a starting guide for a beginner, not a prediction engine. The snapshot is a dated set of public US AI postings; full-time status is retained from source evidence where available. No account or resume is required.", "", "## 0:40-1:35 - Four steps", "Walk through Your background, What interests you, What you've tried, and Your preferences. Enter degree, graduation, industry and research years, then choose role families, project skills, workplace, states, and learning priority. Explain that Remember on this device is an opt-in local browser setting.", "", "## 1:35-2:25 - Read a personalized result", "Open a result card and point to aligned, confirm, or gap. Read the evidence reasons, matched skills, skill gaps, and unknowns. Aligned means the recorded basics fit; confirm means the source or profile leaves something unknown; gap means a stated condition conflicts. These labels do not mean interview or offer odds.", "", "## 2:25-3:15 - Run two what-if actions", f"Use What if I add a skill to compare current overlap with a new skill. The metric counts posting-skill connections, so one posting can contribute multiple connections. The snapshot mentions {top_skill} most often, but overlap is preparation guidance, not proof of proficiency. Then enable Explore every US location. The data includes {non_ca} postings listing a non-CA state and {remote} marked Remote-US, so a beginner can test a wider search before narrowing to one metro.", "", "## 3:15-4:20 - Verify before applying", "Open a source-linked job detail or comparison. Show the official title, location, qualification path, skills, salary if disclosed, sponsorship statement, verification time, and Apply link. Open two employers' official pages. Tell the audience to resolve one confirm item and build one small project from a skill gap.", "", "## 4:20-5:00 - Close with limits", "Open methodology. Say: older career/26fall data was discovery only and Bay Area LLM-biased; fresh official pages broaden the sample; no applicant notes were imported. AI helped extract and summarize, followed by agent review, which is not human verification. Missing data stays unknown, and the product makes no ML prediction or success-odds claim.", "", f"Current snapshot values are generated at run time: {len(s['jobs'])} postings, {len(s['companies'])} companies, {len(s['coverage'])} source checks."]
    (out / "demo-script.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_presentation(data: dict, out: Path):
    s = stats(data)
    snapshot = html.escape(clean(data.get("meta", {}).get("snapshotDate"), "Not stated"))
    fam_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in s["families"].most_common()) or "<tr><td>Not stated</td><td>0</td></tr>"
    loc_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in s["locations"].most_common(8)) or "<tr><td>Not stated</td><td>0</td></tr>"
    # Pick two different employers for a readable, source-linked comparison.
    compare_jobs = []
    seen_companies = set()
    for job in s["jobs"]:
        company = clean(job.get("company"))
        if company not in seen_companies:
            compare_jobs.append(job)
            seen_companies.add(company)
        if len(compare_jobs) == 2:
            break
    cards = []
    for job in compare_jobs:
        paths = job.get("qualificationPaths") or []
        degree = "; ".join(clean(path.get("evidence")) for path in paths[:2]) or "Qualification path not stated"
        source_url = html.escape(clean(job.get("url"), "#"), quote=True)
        cards.append(
            "<article class='source-card'>"
            f"<p class='card-company'>{html.escape(clean(job.get('company')))}</p>"
            f"<h3>{html.escape(clean(job.get('title')))}</h3>"
            f"<p><b>US listing:</b> {html.escape(clean(job.get('locationText')))}</p>"
            f"<p><b>Degree path:</b> {html.escape(degree)}</p>"
            f"<p class='card-summary'>{html.escape(clean(job.get('summary')))}</p>"
            f"<a href='{source_url}' target='_blank' rel='noopener'>Open official source ↗</a>"
            "</article>"
        )
    compare_cards = "".join(cards) or "<p>No comparison records are available in this snapshot.</p>"
    non_ca = sum(1 for job in s["jobs"] if any(str(loc.get("state") or "").strip().upper() in US_STATES - {"CA"} for loc in job.get("locations", [])))
    phd_path = sum(1 for job in s["jobs"] if any("PhD" in (path.get("degrees") or []) for path in job.get("qualificationPaths", [])))
    salary_count = len(s["salary_jobs"])
    status_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in s["statuses"].most_common()) or "<tr><td>Not stated</td><td>0</td></tr>"
    remote_count = sum(1 for job in s["jobs"] if job.get("remote"))
    top_skill = html.escape(s["mentioned_skills"].most_common(1)[0][0] if s["mentioned_skills"] else "a listed skill")
    slides = [
        f"<section><p class='eyebrow'>AI CAREER COMPASS</p><h1>Start with a guided AI job search</h1><p class='lead'>A source-backed public posting sample that turns a beginner's background, interests, skills, and preferences into explainable next steps.</p><div class='accent'></div><p class='meta'>Snapshot: {snapshot} | {len(s['jobs'])} postings | {len(s['companies'])} companies</p></section>",
        f"<section><p class='eyebrow'>01 / SAMPLE</p><h2>What is in the snapshot?</h2><div class='cards'><div><b>{len(s['jobs'])}</b><span>postings</span></div><div><b>{len(s['companies'])}</b><span>companies</span></div><div><b>{len(s['coverage'])}</b><span>source checks</span></div></div><p>Records link to public ATS or company sources and are labeled by the evidence available; broad discovery records may still need role-level employment verification. Pathway labels stay explicit: new-grad, zero-experience, early-career, or unclear.</p></section>",
        f"<section><p class='eyebrow'>02 / FOUR STEPS</p><h2>Guide the beginner before ranking</h2><div class='advice-list'><div class='advice'><b>1. Your background</b><span>Degree, graduation, industry years, and research years.</span></div><div class='advice'><b>2. What interests you</b><span>Role families that make the search concrete.</span></div><div class='advice'><b>3. What you've tried</b><span>Project skills and visible evidence to build.</span></div><div class='advice'><b>4. Your preferences</b><span>Workplace, states, relocation, and learning priority.</span></div></div><p class='note'>The profile is optional and remembered only on this device when opted in.</p></section>",
        f"<section><p class='eyebrow'>03 / EVIDENCE</p><h2>Every match explains itself</h2><table><thead><tr><th>Pathway label</th><th>Postings</th></tr></thead><tbody>{status_rows}</tbody></table><div class='advice-list'><div class='advice'><b>Aligned</b><span>Recorded basics fit the source requirements.</span></div><div class='advice'><b>Confirm</b><span>Something is unknown and needs a source check.</span></div><div class='advice'><b>Gap</b><span>A stated condition conflicts; skills still suggest preparation.</span></div></div><p class='note'>These are evidence statuses, never ML predictions or success odds.</p></section>",
        f"<section><p class='eyebrow'>04 / WHAT-IF</p><h2>Change one input, learn what to do next</h2><div class='advice-list'><div class='advice'><b>Add a skill</b><span>Compare current overlap with {top_skill}; overlap guides a project plan, not qualification proof.</span></div><div class='advice'><b>Widen location</b><span>{non_ca} postings list a non-CA state and {remote_count} are Remote-US. Try nationwide search before narrowing.</span></div></div><p class='note'>The guide turns an unknown or skill gap into a concrete source check or starter project.</p><a class='site-link' href='./#guide'>Back to site ↗</a></section>",
        f"<section><p class='eyebrow'>05 / COMPARE</p><h2>Read two official pathways</h2><div class='source-grid'>{compare_cards}</div><div class='advice'><b>Preparation suggestion</b><span>Choose one confirm item and one small project from the evidence before applying.</span></div><p class='note'>Use each official source link for complete requirements and the application form.</p><a class='site-link' href='./#guide'>Back to site ↗</a></section>",
        f"<section><p class='eyebrow'>06 / METHOD</p><h2>Evidence with clear limits</h2><ul><li>Fresh official ATS or company-career sources</li><li>Earlier career/26fall data was discovery only and Bay Area LLM-biased</li><li>AI-assisted extraction plus agent review; not human verification</li><li>Missing data stays unknown; no applicant notes imported</li><li>No ML prediction or success-odds claim</li><li>Only {salary_count} of {len(s['jobs'])} postings disclose annual base salary</li></ul><div class='accent'></div><a class='site-link' href='./#guide'>Back to site and apply ↗</a></section>",
    ]
    body = "\n".join(slides)
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>AI Career Compass presentation</title><style>
    :root{{--navy:#10233f;--blue:#1f6feb;--lime:#b7e35f;--ink:#17324d;--muted:#61758b;--paper:#f7fbff}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}main{{min-height:100vh;display:grid;place-items:center;padding:3rem 3rem 6rem}}section{{display:none;width:min(960px,92vw);min-height:560px;padding:4rem 4.5rem;background:#fff;border:1px solid #d9e6f2;box-shadow:0 18px 60px #10233f14;border-radius:18px}}section.active{{display:block}}h1{{font-size:clamp(2.8rem,7vw,5.8rem);line-height:.98;letter-spacing:-.06em;color:var(--navy);max-width:750px;margin:.4rem 0 1.5rem}}h2{{font-size:clamp(2rem,4vw,3.2rem);line-height:1.05;letter-spacing:-.04em;color:var(--navy);margin:.5rem 0 2rem}}h3{{color:var(--navy);font-size:1rem;line-height:1.2;margin:.25rem 0 .7rem}}.eyebrow{{color:var(--blue);font-size:.78rem;font-weight:800;letter-spacing:.16em}}.lead{{font-size:1.35rem;max-width:650px;color:var(--muted)}}.meta,.note{{color:var(--muted);font-size:.9rem}}.accent{{width:100px;height:8px;background:var(--lime);border-radius:10px;margin:2rem 0}}.cards{{display:flex;gap:1rem;margin:2rem 0}}.cards div{{background:#eef6ff;border-radius:12px;padding:1.3rem 1.5rem;min-width:130px}}.cards b{{display:block;font-size:2.4rem;color:var(--blue)}}.cards span{{color:var(--muted)}}table{{width:100%;border-collapse:collapse;margin:1rem 0 1.4rem}}th,td{{text-align:left;border-bottom:1px solid #d9e6f2;padding:.7rem .55rem}}th{{color:var(--blue);font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}}li{{margin:.85rem 0;font-size:1.1rem}}.advice-list{{display:grid;gap:1rem;margin:1.5rem 0}}.advice{{display:grid;gap:.25rem;background:#eef6ff;border-left:5px solid var(--lime);padding:1rem 1.2rem;border-radius:0 10px 10px 0}}.advice b{{color:var(--navy)}}.advice span{{color:var(--muted)}}.source-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:1rem 0 1.2rem}}.source-card{{border:1px solid #d9e6f2;border-radius:12px;padding:1rem;background:#fbfdff}}.card-company{{color:var(--blue);font-weight:800;font-size:.8rem;margin:0 0 .4rem}}.card-summary{{color:var(--muted);font-size:.9rem}}a{{color:var(--blue);font-weight:700}}.site-link{{display:inline-block;margin-top:1rem}}.deck-nav{{position:fixed;bottom:1rem;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:.75rem;background:#fff;border:1px solid #d9e6f2;border-radius:999px;padding:.45rem .65rem;box-shadow:0 8px 30px #10233f20;z-index:5}}.deck-nav button{{border:0;background:#eef6ff;color:var(--navy);border-radius:999px;padding:.55rem .9rem;font:inherit;cursor:pointer}}.deck-nav button:hover,.deck-nav button:focus{{background:var(--lime)}}#page-number{{min-width:3.5rem;text-align:center;color:var(--muted);font-variant-numeric:tabular-nums}}@media(max-width:650px){{main{{padding:1rem 1rem 5.5rem}}section{{padding:2rem;min-height:600px;width:96vw}}.cards{{flex-wrap:wrap}}.source-grid{{grid-template-columns:1fr}}.deck-nav{{width:max-content;max-width:calc(100vw - 2rem)}}}}
    </style></head><body><main id='deck'>{body}</main><nav class='deck-nav' aria-label='Presentation navigation'><button id='prev' type='button' aria-label='Previous slide'>← Previous</button><span id='page-number'>1 / {len(slides)}</span><button id='next' type='button' aria-label='Next slide'>Next →</button></nav><script>const slides=[...document.querySelectorAll('section')],pageNumber=document.getElementById('page-number');let i=0;function show(n){{i=(n+slides.length)%slides.length;slides.forEach((s,k)=>s.classList.toggle('active',k===i));pageNumber.textContent=(i+1)+' / '+slides.length;location.hash='slide-'+(i+1)}}document.getElementById('prev').addEventListener('click',()=>show(i-1));document.getElementById('next').addEventListener('click',()=>show(i+1));document.addEventListener('keydown',e=>{{if(['ArrowRight',' ','PageDown'].includes(e.key)){{e.preventDefault();show(i+1)}}if(['ArrowLeft','PageUp'].includes(e.key)){{e.preventDefault();show(i-1)}}}});let touchX=null;document.addEventListener('touchstart',e=>{{touchX=e.changedTouches[0].screenX}},{{passive:true}});document.addEventListener('touchend',e=>{{if(touchX===null)return;const dx=e.changedTouches[0].screenX-touchX;if(Math.abs(dx)>45)show(i+(dx<0?1:-1));touchX=null}},{{passive:true}});const hash=Number(location.hash.replace('#slide-',''));show(Number.isFinite(hash)&&hash>0?hash-1:0);</script></body></html>"""
    (out / "presentation.html").write_text(page, encoding="utf-8")


def main():
    args = parse_args()
    data = load_snapshot(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    write_methodology(data, args.output)
    write_reflection(data, args.output)
    write_markdown(data, args.output)
    write_demo(data, args.output)
    write_presentation(data, args.output)
    print(f"Generated artifacts in {args.output}")


if __name__ == "__main__":
    main()
