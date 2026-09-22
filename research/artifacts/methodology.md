# Data and methodology

Tianyu Zhao | MIT 1.125 PS1 | Snapshot: 2026-09-21

## Problem, user and decision

Students starting to explore AI careers often see a long list of roles without knowing how directions, locations and skills differ. AI Career Compass helps students, university career services and student groups compare those patterns and choose a direction and next learning project.

## Data collection and scope

Frozen snapshot: 21 September 2026. The unit is one unique public US AI technical job posting. We collected official Greenhouse and Ashby board APIs plus Lever and employer careers pages, using employer registries and an earlier targeted career-search list for discovery. The final sample contains 852 postings from 107 companies: Greenhouse 522, Ashby 309, employer careers 17 and Lever 4. All experience levels are included. The broad screen excludes internships, temporary work, non-US roles and nontechnical AI titles. This is a purposive sample, not a census.

## Cleaning and review

The build merges seven source partitions, removes tracking parameters, and deduplicates by employer plus source/requisition ID, canonical URL and record ID. It normalizes skill aliases and US locations, retains multi-location records, and applies documented source corrections and exclusions. 795 postings are labeled automated discovery and 57 curated source review; these labels do not certify hiring eligibility. The 198 source-check records include 26 inaccessible endpoints. Missing access never establishes that an employer has no jobs.

## Measures and definitions

Charts count postings; state and skill totals can overlap. Each posting has one primary direction. Entry means graduate/0-2 years; Senior means experienced individual contributor; Staff means senior technical scope; Manager means people leadership. Unsupported cases remain Unspecified. Graduate evidence is a separate filter. Skill lab uses distinct tracked skills and a fixed 70% target: matched skills >= ceil(0.70 x tracked skills). Four of five skills meet the target. Recommendations rank new target crossings, then progress on unmet postings and company breadth.

## Missingness, uncertainty and privacy

198 postings have unspecified experience, 101 have no named US state, 36 have no tracked skills and 829 have no salary disclosure. Skill coverage excludes the 36 skill-less records, leaving 816 scored postings. Another 256 list only one or two skills. Fixed-vocabulary extraction can miss terms or combine required, preferred, contextual and alternative mentions. Board selection and the earlier Bay Area/LLM discovery list bias coverage. The snapshot cannot establish national demand, proficiency, eligibility or hiring probability. Selected skills stay in the browser; no applicant identity, resume or contact information is collected.

## Sources and reproducibility

Official posting URLs and UTC check timestamps are in jobs.csv; endpoint URLs, access outcomes and dates are in source_coverage.csv. All recorded source checks are dated 2026-09-21. The data dictionary defines fields and units. Collection scripts, corrections, source partitions and the fixed-target study are in the GitHub repository. Reproduce published analysis from the frozen data.json; recollecting live boards can change the sample.

## Source links

- [Official posting example (checked 2026-09-21)](https://job-boards.greenhouse.io/affirm/jobs/7822387003)
- [Source URLs and collection dates](https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site/downloads/source_coverage.csv)
- [Code, collection scripts and frozen source partitions](https://github.com/zhaotianyu0702/mit-1.125-ps1)
