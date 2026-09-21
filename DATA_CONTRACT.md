# Data collection contract

Agents write only their assigned JSON/JSONL and coverage files under `ps1/research/`. Site source belongs to the root agent. Collection seed lists contain public company career and ATS URLs only; never import a private applicant profile, saved-job list, application progress, recruiter contact, or personal notes. Read AI_Career_Compass_PLAN.md for scope.

Return a JSON object: `{ "jobs": [...], "coverage": [...] }`. Each job:

```json
{
  "id": "employer-sourceid",
  "company": "Company",
  "title": "Exact title",
  "url": "official canonical posting URL",
  "applyUrl": "official application URL or same posting URL",
  "source": "Greenhouse|Lever|Company careers",
  "sourceId": "official ID",
  "verifiedAt": "ISO timestamp",
  "publishedAt": null,
  "deadline": null,
  "roleFamily": "ML Engineering|AI Applications|Research|ML Infrastructure|Applied Data Science",
  "tags": ["LLM"],
  "locations": [{"city":"Seattle","state":"WA","country":"US"}],
  "remote": false,
  "workplace": "On-site|Hybrid|Remote|Not stated",
  "locationText": "Source specific location",
  "newgradStatus": "explicit|zero-experience|early-career|unclear",
  "qualificationPaths": [{"degrees":["Bachelor","Master"],"minYears":0,"experienceType":"industry|research|not stated","graduation":"Not stated","graduationYears":[],"evidence":"Paraphrase of qualification pathway"}],
  "startYears": [],
  "startWindow": "Not stated",
  "skills": [{"name":"Python","level":"required|preferred|mentioned","alternativeGroup":null}],
  "salary": [{"min":100000,"max":150000,"currency":"USD","period":"year","scope":"US base salary"}],
  "sponsorship": "Supported|Not offered|Conditional|Not stated",
  "sponsorshipNote": "Not stated",
  "summary": "Short factual paraphrase of core role",
  "newgradEvidence": "Short evidence excerpt or clearly marked paraphrase",
  "aiEvidence": "Short evidence excerpt or clearly marked paraphrase",
  "qualificationNote": "Important conditions and alternatives",
  "reviewNote": "How verified active and any limitations"
}
```

Use null for unknown minYears; **zero only with explicit new-grad/zero-experience path supported by full JD**, while noting research/project requirements separately. Never guess degree eligibility or sponsorship. Confirmed records must be full-time US AI technical roles with role-level evidence. Broad Greenhouse/Ashby API discovery may lack a reliable `employmentType`; such records may be retained only as separately labeled `unclear` discovery candidates with the missing full-time field visible, and must not be described as confirmed full-time or confirmed new-grad until role-level review. Prefer explicit newgrad eligibility or documented zero-experience alternatives. Additional early-career (minimum up to two years) and unclear-graduate-eligibility discovery roles are allowed with separate honest labels and source evidence. PhD newgrad allowed, even if title includes Senior. Do not include broad non-AI SWE, interns, closed/redirected posts, or unambiguously senior positions with 3+ industry years required under every degree pathway. Missing experience requirements only support the unclear group, never zero experience or confirmed graduate eligibility. No personal/contact data. Empty arrays for unknown salary, skills etc. Avoid copying complete JD. Total verbatim excerpts per posting <=25 words; prefer paraphrases.

Coverage rows: `{company, url, checkedAt, status: "verified roles|no qualifying roles|inaccessible|needs review", note, qualifyingCount}`. Do not label source inaccessible as no jobs. Verify role-level official title, requirements, US location and application presence; HTTP200 alone is insufficient. Include a small reproducible collector script only in your assigned research folder if practical. Do not use other agent company partitions. Send early first validated records when possible, then finish broader batch.

## Discovery versus verification

Public Greenhouse, Ashby and Lever board APIs are useful discovery inputs, but a successful board response does not prove that every returned listing is active, full-time, US-based or individually reviewed. Keep automated broad discovery separate from curated official-source verification. A source seed is a public employer or ATS URL; it is never a source for applicant identity, personal progress or private notes.

`qualificationPaths.minYears: null` means the inspected source did not establish a numeric minimum. It must not be converted to zero. A year in a title such as “2027 Start” is a start cohort unless the body also states a graduation window. Empty degree, salary, skill and location arrays preserve missing evidence.
