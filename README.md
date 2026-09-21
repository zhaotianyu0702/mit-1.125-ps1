# AI Career Compass - MIT 1.125 PS1

AI Career Compass is a concise, source-backed visualizer for a frozen sample of US AI job postings. It helps a student inspect the opportunity landscape and run a local skill-mention experiment. The current snapshot contains **852 postings from 107 companies**.

Live site: [AI Career Compass](https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site). Submission repository: [zhaotianyu0702/mit-1.125-ps1](https://github.com/zhaotianyu0702/mit-1.125-ps1).

The interface has two main tabs: `Opportunity landscape` (`#landscape`, the default) and `Skill lab` (`#skills`). A lightweight guided tour moves through three prompts: explore opportunities, map your skills, and try a suggested skill. `Data & method` (`#data`) is the secondary tab for CSV exports, source provenance, assignment materials, methodology, and reflection. The tour preserves the shared filters and selected skills; skill profile data stays in the browser, with optional device-local memory.

The two main views share four filters: primary role direction, experience level, US region/state/remote, and graduate evidence (`all`, `explicit graduate`, or `early career`). Landscape shows distributions by direction, experience, and region, plus a skill-demand matrix. Skill lab reports the fraction and count of filtered postings mentioning at least one selected skill by role. “Try one skill” shows before/after posting coverage; recommendations rank missing skills by posting mentions and then company breadth, with a small suggested learning-project template.

Skill mention coverage is descriptive. It does not estimate eligibility, match score, readiness, hiring probability, proficiency, or the absence of an unmentioned skill. Experience buckets are descriptive exploration labels, not graduate eligibility: title and curated labels are retained; when no title label exists, a numeric requirement of 0–2 years maps to entry, 3–4 to mid, and 5+ to senior; prior professional experience without years maps to experienced; explicit multi-level or level-dependent requirements map to Level varies; otherwise the value remains unknown. These inferred buckets record the basis in the data and do not change graduate flags or qualification paths.

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

Regenerate the course materials after the snapshot is frozen with Python 3 and ReportLab installed (or use the bundled runtime):

```sh
python3 research/generate_documents.py --input dist/data.json
cp research/artifacts/methodology.pdf research/artifacts/reflection.pdf \
  research/artifacts/demo-script.md research/artifacts/data-dictionary.md dist/downloads/
cp research/artifacts/presentation.html dist/presentation.html
```

If ReportLab is missing, install it in the active Python environment with `python3 -m pip install reportlab`.

Inspect the PDFs after generation. `research/artifacts` contains the source artifacts; `dist/downloads` contains the deployable copies.

## Project structure

```text
dist/                       Deployable static site and canonical data snapshot
  data.json                 852-posting source-linked snapshot
  downloads/                CSV exports and course materials
  presentation.html         Five-slide, five-minute presentation
research/                   Collection partitions and document generator
scripts/build-data.py       Merge partitions and build normalized exports
tests/                      Data and interaction checks
```

No account, name, contact details, résumé, medical information, or precise personal location is collected. The product has no analytics SDK. Always consult the official source before making a job-search decision.
