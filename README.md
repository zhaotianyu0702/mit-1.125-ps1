# AI Career Compass — MIT 1.125 PS1

A guided exploration tool for students who are new to the US AI job market. Start with your background, project experience and preferences; learn what different AI roles involve; investigate a source-backed shortlist; and try skill or location scenarios.

Live site: [AI Career Compass](https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site) (access follows the current Site sharing setting).

Submission repository: [zhaotianyu0702/mit-1.125-ps1](https://github.com/zhaotianyu0702/mit-1.125-ps1).

## Run locally

The website is static HTML, CSS and JavaScript with no build-time frontend dependencies. Python 3 serves it; Node.js 22+ runs the tests.

```sh
git clone https://github.com/zhaotianyu0702/mit-1.125-ps1.git
cd mit-1.125-ps1
npm start
```

Open [localhost:8767](http://127.0.0.1:8767/#guide). Do not open `index.html` as a `file://` URL: the app loads the public data snapshot with `fetch`.

```sh
python3 scripts/build-data.py
npm test
```

## What the site does

- A four-step personal exploration flow, with plain-language explanations of five role families.
- Transparent qualification checks that preserve degree-specific experience and graduation alternatives.
- Separate groups for stated basics that align, requirements needing confirmation, and recorded conditions that differ.
- Preference-based ordering, a transparent what-if experiment (posting-skill connections, not unique job counts), a nationwide-location experiment, and a downloadable next-step plan.
- An independent experience-level filter: New grad, Entry/junior, Mid-level, Senior, Staff/principal, Leadership and Not specified. Explorer and charts initially cover all levels; the guided flow starts with a transparent beginner preset.
- Keyword, location, degree, role, skill, industry-years availability, salary-disclosure and graduate-evidence filters.
- Source-linked job details, device-local saved jobs, up to three-role comparison, charts and filtered CSV exports.
- Data downloads, methodology, reflection, and a five-minute presentation on the website.

This is a learning and decision-support tool. It does not estimate hiring probability or certify that an applicant meets every requirement. Skills selected in the profile mean self-reported project exposure.

## Data and reproducibility

`research/*.json` contains the source-specific collection partitions. `scripts/build-data.py` merges them, applies documented exclusions and the live Ashby corrections overlay when present, deduplicates official requisitions/URLs, and produces `dist/data.json` plus normalized CSV tables. `generatedAt` records the build time; source-check timestamps remain attached to individual records. `scripts/collect-public-boards.py` and `scripts/collect-ashby-discovery.py` query versioned public board registries without per-company caps; all their leads remain `unclear`. The earlier `research/collect_expanded_ats.py` queries public Greenhouse, Ashby and Lever board APIs for a declared early-career discovery set; its broad automated results are not equivalent to individual human review. `research/verified-corrections.json` records live Ashby checks for curated IDs and leaves unavailable or ambiguous fields unknown.

The earlier private career-search dataset was used only to discover employer and source links. It was targeted toward Bay Area LLM roles, so it is not a representative US sampling frame. Personal rankings, applicant information, notes and application progress are **not** part of this repository or the published dataset. New collection expands the employer/source frame and verifies official postings again. The sample still reflects source access, employer selection and uneven disclosure; it is not a census.

Collection now includes experienced roles, with no maximum experience-year gate. Experience level is derived from recognizable title wording or curated graduate evidence; numerical year references are displayed separately and do not certify a minimum. Unknown titles remain unspecified.

Graduate-evidence groups remain separate:

| Group | Meaning |
| --- | --- |
| `explicit` | The employer explicitly describes a graduate/early-graduate pathway. |
| `zero-experience` | A documented zero-experience pathway without an explicit graduate label. |
| `early-career` | A documented pathway with a minimum of up to two years; it may require experience a new graduate does not have. |
| `unclear` | Relevant US AI work, but graduate eligibility is not established. Missing requirements remain unknown. |

Re-running a collector is discovery/extraction, not final review. Ashby discovery requires its `FullTime` field and a listed posting; Greenhouse discovery does not establish employment terms. Qualification pathways still need role-level review. Recheck inclusion decisions, qualification alternatives, official application availability, US geography, dates, salary scope and skill wording before merging a refreshed partition. A successful HTTP response alone is not evidence of an active job. Old minimum acceptance dates are not application deadlines.

## Project structure

```text
dist/                       Deployable static site
  app.js, core.js            Explorer, charts, comparison and filters
  journey.js, matching.js    Guided experience and transparent matching rules
  data.json                 Published source-linked snapshot
  downloads/                CSV and submission materials
research/                   Collection partitions, provenance and document generator
scripts/build-data.py        Merge and CSV build
tests/                      Meaningful data, filtering and matching checks
.github/workflows/          Validation on pushes and pull requests
.openai/hosting.json        Static hosting configuration
```

To build the published snapshot and validate it:

```sh
python3 scripts/collect-public-boards.py    # optional Greenhouse discovery refresh
python3 scripts/collect-ashby-discovery.py   # optional Ashby discovery refresh
python3 scripts/build-data.py              # merge partitions and write dist/data.json/CSVs
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
```

After the snapshot is frozen, generate the research documents with the bundled Python/reportlab environment or an installed `reportlab`:

```sh
python3 research/generate_documents.py --input dist/data.json
cp research/artifacts/methodology.pdf research/artifacts/reflection.pdf research/artifacts/demo-script.md research/artifacts/data-dictionary.md dist/downloads/
cp research/artifacts/presentation.html dist/presentation.html
```

Inspect the resulting PDFs and presentation before publishing. The documentation generator computes counts from the input snapshot; do not distribute stale materials after a data change. The build and tests are the reproducibility checks; document generation is a separate finalization step.

## Privacy and limitations

No account, name, contact details, résumé, medical information or precise personal location is collected. Profile answers remain in page memory unless the student opts to remember them on that device. Saved jobs and optional profile storage use `localStorage`; profile data is not transmitted or included in shared URLs. Clearing the profile removes its saved copy. The site contains no analytics SDK.

Sources are official public postings; extracted fields and brief paraphrases can still contain errors. Counts describe unique postings, not headcount. State, skill and degree counts can overlap. Salary ranges are advertised base-pay ranges, not offers or total compensation. Source concentration and missing data affect every comparison. Always consult the official source before applying.

AI agents assisted collection, extraction, implementation and review. No employer or independent human certification is claimed.
