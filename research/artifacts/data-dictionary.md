# Data dictionary

Generated from snapshot `2026-09-21` with 852 postings and 107 companies.

The unit is one unique public job posting. A posting may contain multiple locations, qualification paths, skills, or salary ranges.

## Product measures

- `direction distribution`: postings grouped by primary `roleFamily` or selected direction.
- `experience distribution`: postings grouped by four broad exploration buckets; unspecified remains visible when evidence is insufficient.
- `region distribution`: one count per listed state and a separate `Remote - US` bucket; totals can overlap.
- `skill-demand matrix`: postings mentioning a skill divided by filtered postings in the direction; one count per cell.
- `skill lab coverage`: filtered postings meeting a per-posting skill target (fixed at 70%), shown as count and fraction by role.
- `missing-skill recommendation`: unselected skills ranked by new target crossings, then summed 1/ceil(skill count * target) progress on unmet postings, then company breadth.

## Snapshot fields

| Field | Meaning |
| --- | --- |
| `id` | Stable company-source identifier used for deduplication. |
| `company / title / url` | Employer, exact source title, and canonical official posting URL used by Job postings. |
| `source / sourceId / verifiedAt` | ATS or company-careers provenance and latest source check timestamp. |
| `roleFamily / tags` | Primary direction used for one-category charts, plus additional technical directions. |
| `locations / locationText / remote / workplace` | Source-listed US places and stated work arrangement; state and remote counts can overlap. |
| `newgradStatus / newgradEvidence` | Graduate evidence group: explicit, zero-experience, early-career, or unclear, with source explanation. |
| `experienceLevel / experienceLevelBasis / experienceLevelEvidence` | Four descriptive exploration buckets: 0–2 entry; experienced individual contributor with 3+ years, independent scope, or prior production track record, senior; explicit senior technical scope, staff; people-management scope, manager. Unsupported evidence remains unspecified. |
| `experienceEvidenceSource / requirementYears / classifiedRequirementYears` | Official excerpt, URL and check date; all parsed numbers and the numeric floor used for a requirements bucket. These do not establish eligibility. |
| `experienceReferences` | Raw year mentions from the full description; never a validated scalar minimum. |
| `skills` | Mentioned skill names with required, preferred, or mentioned level. Skill lab counts a posting when selected skills meet the chosen fraction of its distinct tracked skills. |
| `qualificationPaths` | Degree and experience alternatives; unknown values stay unknown and are not converted to zero. |
| `salary / sponsorship` | Disclosed base-pay ranges and public sponsorship statement; missing disclosure is not a negative answer. |
| `summary / aiEvidence / qualificationNote / reviewNote` | Short factual evidence and review/provenance notes retained for source-grounded interpretation. |
| `coverage` | Company-level source check; inaccessible or incomplete sources are not treated as no qualifying jobs. |
| `meta` | Snapshot date, scope, unit, partitions, review description, and excluded count for reproducibility. |

Unknown values remain explicit (`null`, empty arrays, `Not stated`, or `unclear`). Absence of a skill mention does not establish that the job does not require it.

## Provenance

The snapshot has 198 source checks and 23 postings with disclosed salary. Official URLs and review labels are preserved in `dist/downloads/jobs.csv` and the published data snapshot.
