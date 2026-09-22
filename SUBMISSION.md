# MIT 1.125 PS1 — AI Career Compass

Author: Tianyu Zhao. Frozen snapshot: 2026-09-21. Skill target: fixed 70%.

Published site: https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site
Submission materials: https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site/submission.html
GitHub submission repository: https://github.com/zhaotianyu0702/mit-1.125-ps1

## Deliverables

1. Complete static site: `dist/`. Start with `dist/submission.html` for documents.
2. Dataset: `dist/downloads/jobs.csv` (852 postings) plus five related CSVs.
3. One-page data and methodology note: `dist/downloads/methodology.pdf` and editable Markdown.
4. Five-minute website demonstration: `dist/presentation.html`; MP4: `dist/downloads/presentation.mp4`; narration: `dist/downloads/demo-script.md`. Actual website recording with English male synthetic narration and English captions (`dist/downloads/presentation.vtt`).
5. Short reflection: `dist/downloads/reflection.pdf` and editable Markdown.
6. Findings, two recommendations, definitions, sources and the fixed-target study: `dist/downloads/`.

The GitHub repository contains the collection partitions, scripts and tests. This pack includes the complete static website source and frozen data. There is no applicant profile data, local browser state or credential material.

## Run the packaged site locally

From this extracted folder:

    python3 -m http.server 8767 --directory dist --bind 127.0.0.1

Open http://127.0.0.1:8767/. Use HTTP because the dashboard fetches data.json.

## Verify the snapshot

Dataset SHA-256: `8a1fe8ed980e8dee6c2cb2c47d5980849937cbeab08176e535dc3c88d116f426`. `dist/downloads/submission-manifest.json` contains each packaged file's SHA-256 and CSV row counts. This is a dated purposive sample, not a labor-market census. The five-minute video is included in this package.

## Course submission locations

Enter the main published site URL in the course sheet's `PS1 Site URL` column and the repository URL in `PS1 Repo`. These are separate from the final-project columns.
