# MIT 1.125 PS1 — AI Career Compass

Author: Tianyu Zhao. Frozen snapshot: 2026-09-21. Skill target: fixed 70%.

Published site: https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site
Submission materials: https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site/submission.html
GitHub submission repository: https://github.com/zhaotianyu0702/mit-1.125-ps1

## Deliverables (excluding the recording)

1. Complete static site: `dist/`. Start with `dist/submission.html` for documents.
2. Dataset: `dist/downloads/jobs.csv` (852 postings) plus five related CSVs.
3. One-page data and methodology note: `dist/downloads/methodology.pdf` and editable Markdown.
4. Five-slide presentation: `dist/presentation.html`; timed demonstration script: `dist/downloads/demo-script.md`. Slides and script are prepared. No video file is included.
5. Short reflection: `dist/downloads/reflection.pdf` and editable Markdown.
6. Findings, two recommendations, definitions, sources and the fixed-target study: `dist/downloads/`.

The GitHub repository contains the collection partitions, scripts and tests. This pack includes the complete static website source and frozen data. There is no applicant profile data, local browser state or credential material.

## Run the packaged site locally

From this extracted folder:

    python3 -m http.server 8767 --directory dist --bind 127.0.0.1

Open http://127.0.0.1:8767/. Use HTTP because the dashboard fetches data.json.

## Verify the snapshot

Dataset SHA-256: `8a1fe8ed980e8dee6c2cb2c47d5980849937cbeab08176e535dc3c88d116f426`. `dist/downloads/submission-manifest.json` contains each packaged file's SHA-256 and CSV row counts. This is a dated purposive sample, not a labor-market census. The original brief asks for a five-minute demonstration without specifying a recording format. Video remains outside this package.

## Course submission locations

Enter the main published site URL in the course sheet's `PS1 Site URL` column and the repository URL in `PS1 Repo`. These are separate from the final-project columns.
