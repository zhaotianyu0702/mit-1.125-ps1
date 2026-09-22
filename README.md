# AI Career Compass - MIT 1.125 PS1

AI Career Compass is a concise, source-backed visualizer for a frozen sample of US AI job postings. It helps a student inspect the opportunity landscape and run a local skill-mention experiment. Snapshot totals are derived from the published data rather than hard-coded in the interface documentation.

Live site: [AI Career Compass](https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site). Submission repository: [zhaotianyu0702/mit-1.125-ps1](https://github.com/zhaotianyu0702/mit-1.125-ps1).

## PS1 submission materials

All non-video deliverables are one click away through **Submission** in the website header, including the [complete submission pack](dist/downloads/ai-career-compass-ps1.zip). The [submission index](SUBMISSION.md) maps each assignment deliverable to its file.

- [Submission materials page](https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site/submission.html)
- Six CSV tables, the canonical JSON, a one-page methodology note, a short reflection, the five-slide presentation and a timed five-minute demo script
- Main findings, two data-supported recommendations, definitions, official source URLs and the fixed 70% target study
- The video recording is not included. The course sheet has separate `PS1 Site URL` and `PS1 Repo` columns.

The interface has two main tabs: `Opportunity landscape` (`#landscape`, the default) and `Skill lab` (`#skills`). `Job postings` (`#postings`) is the reference view for the full posting list, with experience, skills, direction, location, and source fields. It does not provide an application channel. Assignment materials, methodology, and reflection are accessible through the **Submission** header link on desktop and mobile, and the `Project files` footer. Skill profile data stays in the browser, with optional device-local memory.

All three views share four filters: primary role direction, experience level, US region/state/remote, and graduate evidence (`all`, `explicit graduate`, or `early career`). Job postings adds posting search and a canonical skill-mention filter; those selections can persist into the charts and Skill lab. Landscape shows distributions by direction, experience, and region, plus a skill-demand matrix. Skill lab reports the fraction and count of filtered postings meeting a per-posting skill target (fixed at 70%) by role. “Try one skill” shows before/after posting coverage; recommendations rank unselected skills by additional postings reaching the target, then normalized progress on unmet postings and company breadth, with a small suggested learning-project template.

Skill mention coverage is descriptive. It does not estimate eligibility, match score, readiness, hiring probability, proficiency, or the absence of an unmentioned skill. Experience buckets are four broad exploration labels, not graduate eligibility: `entry` covers 0–2 years; `senior` covers experienced individual contributors with 3+ years, supported independent scope, or a prior production track record; `staff` requires explicit senior technical scope; and `manager` requires people-management scope. Ordinary experience familiarity alone is insufficient. If the source does not support one of these interpretations, the value is `unspecified`. Source-derived labels record their evidence and do not change graduate flags or qualification paths.

Skill target is fixed at 70%, selected by comparing 40–80% on five role-specific skill profiles and successive learning steps. For a five-skill posting, four selected skills meet the target. The target cannot be changed through a control or URL. Coverage denominators exclude postings without tracked skills. “More move closer” counts improved postings still below target. Read the [threshold comparison](research/skill-threshold-study.md); reproduce with `node scripts/analyze-skill-thresholds.mjs`.

## Run locally

The site is static HTML, CSS, and JavaScript. Python serves it and Node.js runs the tests.

```sh
npm start
```

Open [localhost:8767](http://127.0.0.1:8767/#landscape). Do not open `index.html` as a `file://` URL because the app fetches the public data snapshot.

```sh
npm test
```

## Data and reproducibility

`dist/data.json` is the canonical snapshot. `research/*.json` contains source-specific collection partitions; `scripts/build-data.py` merges, deduplicates, and exports normalized CSV tables. Official source URLs, source IDs, verification timestamps, review levels, and extraction notes remain available in the data and downloads. The published snapshot is a purposive public ATS sample, not a representative labor-market census. Counts are postings, not headcount; state and skill counts can overlap.

Graduate evidence and experience level remain separate. Missing or unclear evidence stays unknown. Experience bucket is not graduate eligibility. Unknown skill is not skill absence. Earlier career/26fall material was discovery only and Bay Area LLM-biased; no applicant notes were imported.

Experience enrichment is saved in `research/experience-evidence.json` with source excerpts. When the ignored official ATS caches are available, run `python3 scripts/enrich-experience.py`, then `python3 scripts/build-data.py` to rebuild it. The checked-in artifact allows the published snapshot to rebuild without those local caches.

Regenerate the written materials and complete archive without recollecting data:

```sh
python3 research/generate_documents.py --input dist/data.json
python3 scripts/package-submission.py
```

PDF generation needs ReportLab. The content is pinned to the frozen dataset hash in `research/submission-content.json`; review those notes before generating materials for a different snapshot. The packager checks matching snapshot hashes, copies the reviewed artifacts, creates `dist/submission.html`, and verifies every ZIP member against its source bytes. `dist/downloads/submission-manifest.json` records the hashes and CSV row counts.

Inspect the PDFs after generation. `research/artifacts` contains the editable Markdown and source artifacts; `dist/downloads` contains deployable copies. The archive includes the static website source, datasets and all non-video deliverables. The GitHub repository also preserves collection partitions and scripts.

## Project structure

```text
dist/                       Deployable static site and canonical data snapshot
  data.json                 Source-linked snapshot
  downloads/                CSV exports and course materials
  presentation.html         Five-slide, five-minute presentation
research/                   Collection partitions and document generator
scripts/build-data.py       Merge partitions and build normalized exports
tests/                      Data and interaction checks
```

No account, name, contact details, résumé, medical information, or precise personal location is collected. The product has no analytics SDK. Always consult the official source before making a job-search decision.
