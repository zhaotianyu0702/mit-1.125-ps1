# Fixed skill target study

Snapshot: 2026-09-21. 852 postings; 816 have tracked skills. Fixed site target: **70%**.

## Evaluation design

Compare 40, 50, 60, 65, 70, 75 and 80 percent using the same canonical skill extraction. Focus the decision on 70–80%: the product should reward building a broader skill set while leaving useful, successive learning steps. Higher coverage alone is not the objective.

Five synthetic profiles cover engineering, applications, research, infrastructure and data science. Each contains 6–7 skills from the actual catalog. They are illustrative probes, not surveyed students or validated career standards. Evaluate each profile within its own direction, average directions equally, then greedily add three recommended skills. Also test a two-skill baseline, the 18 visible skill chips and the full catalog.

## Profile definitions

- **ML Engineering:** Python, Machine learning, PyTorch, Deep learning, C++, Kubernetes, Docker.
- **AI Applications:** Python, LLMs, RAG, AWS, GCP, Kubernetes, NLP.
- **Research:** Python, Machine learning, PyTorch, Reinforcement learning, Deep learning, JAX, CUDA.
- **ML Infrastructure:** Python, Machine learning, LLMs, Kubernetes, C++, CUDA, Docker.
- **Applied Data Science:** Python, SQL, Machine learning, Spark, LLMs, scikit-learn.

## Two-skill baseline

The previous any-skill rule counted 682/852 postings (80.0%). The current denominator excludes 36 postings without tracked skills.

| Target | Python + ML coverage | Share | Best single addition | Newly reaching target |
| --- | ---: | ---: | --- | ---: |
| 40% | 285/816 | 34.9% | LLMs | +180 |
| 50% | 246/816 | 30.1% | LLMs | +155 |
| 60% | 116/816 | 14.2% | LLMs | +141 |
| 65% | 116/816 | 14.2% | LLMs | +135 |
| 70% | 74/816 | 9.1% | LLMs | +93 |
| 75% | 74/816 | 9.1% | LLMs | +93 |
| 80% | 74/816 | 9.1% | LLMs | +79 |

## Each profile in its own direction

| Direction | Scored postings | 60% | 70% | 75% | 80% |
| --- | ---: | ---: | ---: | ---: | ---: |
| ML Engineering | 329 | 125 (38%) | 70 (21.3%) | 60 (18.2%) | 47 (14.3%) |
| AI Applications | 88 | 51 (58%) | 36 (40.9%) | 36 (40.9%) | 29 (33%) |
| Research | 150 | 101 (67.3%) | 80 (53.3%) | 78 (52%) | 69 (46%) |
| ML Infrastructure | 170 | 95 (55.9%) | 66 (38.8%) | 66 (38.8%) | 60 (35.3%) |
| Applied Data Science | 79 | 68 (86.1%) | 59 (74.7%) | 59 (74.7%) | 55 (69.6%) |
| Equal-weight mean of direction percentages | — | 61% | 45.8% | 44.9% | 39.6% |

## Successive learning steps

Each row starts from the role profile above. Values are cumulative covered postings after each addition. Rankings are recalculated after every step; these hypothetical paths do not measure learning effort or outcomes.

| Direction | Target | Initial | +1 skill | +2 skills | +3 skills | Skills added in order |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ML Engineering | 60% | 125 | 216 | 241 | 261 | LLMs → Reinforcement learning → RAG |
| ML Engineering | 70% | 70 | 120 | 162 | 196 | LLMs → TensorFlow → Reinforcement learning |
| ML Engineering | 75% | 60 | 107 | 144 | 176 | LLMs → Reinforcement learning → TensorFlow |
| ML Engineering | 80% | 47 | 86 | 121 | 155 | LLMs → Reinforcement learning → TensorFlow |
| AI Applications | 60% | 51 | 64 | 69 | 72 | Machine learning → PyTorch → Go |
| AI Applications | 70% | 36 | 57 | 61 | 64 | Machine learning → Spark → Go |
| AI Applications | 75% | 36 | 56 | 61 | 64 | Machine learning → Spark → Go |
| AI Applications | 80% | 29 | 51 | 57 | 61 | Machine learning → Reinforcement learning → SQL |
| Research | 60% | 101 | 118 | 126 | 130 | LLMs → Kubernetes → AWS |
| Research | 70% | 80 | 94 | 104 | 111 | LLMs → Kubernetes → Computer vision |
| Research | 75% | 78 | 91 | 102 | 109 | LLMs → Kubernetes → Computer vision |
| Research | 80% | 69 | 88 | 97 | 103 | LLMs → Kubernetes → Computer vision |
| ML Infrastructure | 60% | 95 | 113 | 128 | 142 | AWS → PyTorch → Go |
| ML Infrastructure | 70% | 66 | 80 | 95 | 113 | PyTorch → AWS → Go |
| ML Infrastructure | 75% | 66 | 78 | 92 | 104 | AWS → Go → PyTorch |
| ML Infrastructure | 80% | 60 | 69 | 78 | 90 | PyTorch → AWS → Go |
| Applied Data Science | 60% | 68 | 72 | 74 | 75 | PyTorch → Deep learning → Computer vision |
| Applied Data Science | 70% | 59 | 65 | 69 | 73 | NLP → PyTorch → Deep learning |
| Applied Data Science | 75% | 59 | 65 | 69 | 72 | NLP → PyTorch → Deep learning |
| Applied Data Science | 80% | 55 | 61 | 65 | 70 | NLP → PyTorch → Deep learning |

## Saturation checks

| Selection | 60% | 70% | 75% | 80% |
| --- | ---: | ---: | ---: | ---: |
| Visible 18 | 784/816 (96.1%) | 749/816 (91.8%) | 746/816 (91.4%) | 725/816 (88.8%) |
| Full catalog | 816/816 (100%) | 816/816 (100%) | 816/816 (100%) | 816/816 (100%) |

## Rounding matters

| Tracked skills in posting | 60% required | 70% required | 75% required | 80% required |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1 | 1 | 1 | 1 |
| 2 | 2 | 2 | 2 | 2 |
| 3 | 2 | 3 | 3 | 3 |
| 4 | 3 | 3 | 3 | 4 |
| 5 | 3 | 4 | 4 | 4 |
| 6 | 4 | 5 | 5 | 5 |
| 7 | 5 | 5 | 6 | 6 |
| 8 | 5 | 6 | 6 | 7 |
| 9 | 6 | 7 | 7 | 8 |
| 10 | 6 | 7 | 8 | 8 |

## Fixed choice: 70%

Use 70% across the site, with no target selector or URL override. This is a product heuristic: ask for substantially broader coverage than 60% while preserving useful successive learning steps. In these probes the equal-weight mean across five directions falls from 61.0% to 45.8%. For the ML Engineering profile, three recommended additions move coverage from 70 to 120 to 162 to 196 of 329 postings; the same profile at 60% starts at 125 and reaches 261. The stronger target leaves more headroom for subsequent learning.

75% starts at the same coverage as 70% in three of five directions and an overall mean of 44.9%. It produces little additional separation at the starting profiles. 80% lowers the mean to 39.6% and, because of rounding, requires all four skills on a four-skill posting rather than three. With required, preferred and alternative mentions mixed in this dataset, that all-or-nothing step is a reason to prefer 70%. All five directions still have positive gains on each of the three tested additions. This evidence supports a transparent design choice; it does not prove 70% is optimal for every skill profile.

## Recommendation rule

Rank unselected skills by previously unmet postings that would cross the fixed target. Break ties by summed progress across unmet postings: each improved posting contributes 1 / ceil(skill count × target). Then use employer breadth and skill name. “More move closer” includes only improved postings still below target, excluding newly covered postings. Already covered postings add no benefit.

## Limitations

256/816 scored postings (31.4%) list only one or two tracked skills; all tested targets above 50% require every one of those skills. Sparse lists can inflate coverage. The 36 skill-less postings are unscored, not part of that sparse-list count. Fixed-vocabulary extraction includes required, preferred, contextual and alternative mentions and misses some skills. Equal weighting ignores employer priorities and proficiency. Synthetic profiles are sensitive to their composition; there is no ground-truth outcome data or statistically validated optimal target. This is a learning visualization, not a hiring or eligibility model.

## Reproduce

`node scripts/analyze-skill-thresholds.mjs`

Snapshot SHA-256: `8a1fe8ed980e8dee6c2cb2c47d5980849937cbeab08176e535dc3c88d116f426`. Full profile/filter/threshold results: [research JSON](https://github.com/zhaotianyu0702/mit-1.125-ps1/blob/main/research/skill-threshold-study.json).
