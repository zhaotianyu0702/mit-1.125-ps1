# Skill target comparison

Snapshot: 2026-09-21. 852 postings; 816 have tracked skills.

Synthetic skill sets illustrate sensitivity; they are not student survey results. A posting meets a target only when selected skills cover at least that proportion of its distinct tracked skills. No tracked skills means unscored, never a zero-skill match.

## Python + Machine learning

The previous any-skill rule counted 682/852 postings (80.0%). The new denominator excludes 36 postings without tracked skills.

| Target | Postings meeting target | Share of scored postings | Best single addition | Newly reaching target |
| --- | ---: | ---: | --- | ---: |
| 40% | 285/816 | 34.9% | LLMs | +180 |
| 50% | 246/816 | 30.1% | LLMs | +155 |
| 60% | 116/816 | 14.2% | LLMs | +141 |
| 70% | 74/816 | 9.1% | LLMs | +93 |
| 80% | 74/816 | 9.1% | LLMs | +79 |

## Sensitivity to selected skills

| Example skill set | 40% | 50% | 60% | 70% | 80% |
| --- | ---: | ---: | ---: | ---: | ---: |
| No skills | 0 | 0 | 0 | 0 | 0 |
| Python + ML | 285 | 246 | 116 | 74 | 74 |
| Python + ML + SQL | 334 | 289 | 175 | 123 | 108 |
| ML toolkit | 620 | 534 | 351 | 261 | 224 |
| ML systems | 682 | 597 | 390 | 238 | 203 |
| Data analysis | 366 | 324 | 190 | 135 | 126 |

## Sensitivity across directions

Python + Machine learning; cell values count postings meeting the target.

| Slice | Scored | 40% | 50% | 60% | 70% | 80% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| All | 816 | 285 | 246 | 116 | 74 | 74 |
| Entry | 57 | 8 | 8 | 5 | 2 | 2 |
| ML Engineering | 329 | 99 | 80 | 35 | 28 | 28 |
| ML Infrastructure | 170 | 38 | 34 | 16 | 12 | 12 |
| Research | 150 | 60 | 52 | 25 | 20 | 20 |
| AI Applications | 88 | 35 | 34 | 17 | 10 | 10 |
| Applied Data Science | 79 | 53 | 46 | 23 | 4 | 4 |

## Default and recommendation rule

60% is a product choice, not a statistically validated optimum. It requires a majority of each posting’s tracked skills, removes the permissive one-of-two match allowed by 50%, and retains more near-target opportunities than 70–80%. The control exposes 40–80% for sensitivity checks.

Rank unselected skills by the number of previously unmet postings that would reach the target. Break ties by summed progress toward the target across previously unmet postings: each improved posting contributes 1 / ceil(skill count × target). Then use employer breadth and skill name. “More move closer” counts only improved postings that still remain below target; it excludes the newly covered group. After adding a skill, recalculate the entire ranking.

Limitations: 256 postings list only one or two tracked skills. Sparse lists are easier to cover; broad terms such as Machine learning are not substitutes for depth. Fixed-vocabulary extraction includes required, preferred, and contextual mentions and can miss skills or list alternatives separately. Equal weighting does not reflect actual employer priorities. Coverage is a learning tool, not eligibility, proficiency, or hiring probability.

## Reproduce

`node scripts/analyze-skill-thresholds.mjs`

Snapshot SHA-256: `8a1fe8ed980e8dee6c2cb2c47d5980849937cbeab08176e535dc3c88d116f426`. Full profile/filter/threshold results: [research JSON](https://github.com/zhaotianyu0702/mit-1.125-ps1/blob/main/research/skill-threshold-study.json).
