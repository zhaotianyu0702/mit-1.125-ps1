# Data dictionary

Generated from snapshot `2026-09-21` with 852 jobs and 107 companies.

The canonical record is one posting. One posting can have multiple qualification paths, skills, salary ranges, or US locations.

| Field | Meaning |
| --- | --- |
| `id` | Stable company-source identifier used for deduplication. |
| `company` | Employer name from the official source. |
| `title` | Exact official posting title. |
| `url` | Canonical official posting URL. |
| `applyUrl` | Official application route. |
| `source/sourceId` | ATS or company-careers source and its official identifier. |
| `verifiedAt` | Last source check timestamp. |
| `roleFamily` | One primary AI function for mutually exclusive category charts. |
| `tags` | Additional technical directions such as LLM, CV, or inference. |
| `locations` | One or more source-listed US city/state/country objects. |
| `workplace/remote` | Stated work arrangement; unknown remains Not stated. |
| `newgradStatus` | explicit, zero-experience, early-career (0-2 industry years), or unclear (graduate eligibility not established). |
| `experienceLevel/Basis/Evidence` | Recognized title seniority or curated graduate fallback, with provenance; unspecified is not entry level. |
| `experienceReferences` | Year values mentioned in source text or curated paths, not a validated minimum. Required/preferred and degree alternatives need review. |
| `qualificationPaths` | Structured degree and experience alternatives; minYears is zero only when the source explicitly says no experience is needed. |
| `skills` | Skill name, required/preferred/mentioned level, and alternativeGroup for OR language. |
| `salary` | Disclosed base range with currency, period, and scope; bonus/equity are not merged. |
| `sponsorship` | Only the source's public statement: Supported, Not offered, Conditional, or Not stated. |
| `summary/evidence fields` | Short factual paraphrases supporting role, AI, qualification, and review decisions. |
| `coverage` | Company-level source check; inaccessible is not treated as no qualifying jobs. |
| `profile/matching` | The browser profile is opt-in and local. Statuses use recorded requirements and unknowns; skills and preferences explain preparation and order, not recruiting probability. |

Unknown values remain explicit (`null`, empty arrays, or `Not stated`) and are never inferred as negative answers or zero experience.
