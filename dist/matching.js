/* Transparent, deterministic profile-to-job matching. No DOM or network dependencies. */

export const ROLE_GUIDES = {
  'ML Engineering': {
    description: 'Build and improve models for products such as recommendations, vision, speech, or prediction.',
    dayTasks: 'Prepare data, train or evaluate models, investigate errors, and work with engineers to ship results.',
    starterProject: 'Build a small model with a clear baseline, evaluation split, error analysis, and reproducible README.'
  },
  'AI Applications': {
    description: 'Turn models and LLMs into useful product features, agents, or workflows.',
    dayTasks: 'Design prompts or retrieval, build APIs and evaluations, inspect failures, and iterate with product users.',
    starterProject: 'Build a small retrieval or agent workflow with a held-out evaluation set and failure taxonomy.'
  },
  Research: {
    description: 'Run experiments that extend or test AI methods and communicate results clearly.',
    dayTasks: 'Read papers, formulate hypotheses, implement experiments, analyze results, and write technical findings.',
    starterProject: 'Reproduce one paper result, document deviations, and add one controlled ablation.'
  },
  'ML Infrastructure': {
    description: 'Build the data, training, inference, and reliability systems that make ML work at scale.',
    dayTasks: 'Operate pipelines, improve reproducibility, debug distributed workloads, and measure system reliability.',
    starterProject: 'Create a small training pipeline with versioned data, tracked experiments, and a reproducible run.'
  },
  'Applied Data Science': {
    description: 'Use statistical modeling and machine learning to answer applied product or business questions.',
    dayTasks: 'Define metrics, analyze experiments, build models, communicate uncertainty, and recommend next actions.',
    starterProject: 'Analyze a public dataset with a baseline, validation plan, uncertainty discussion, and concise decision memo.'
  }
};

export const SKILL_OPTIONS = [
  'Python', 'C++', 'Java', 'Go', 'JavaScript', 'SQL', 'PyTorch', 'TensorFlow', 'JAX',
  'Machine learning', 'Deep learning', 'LLMs', 'NLP', 'Computer vision', 'Statistics',
  'Docker', 'Kubernetes', 'CUDA', 'AWS', 'GCP', 'Spark', 'Ray', 'Airflow', 'MLOps', 'Distributed systems'
];
const SKILL_LABELS = new Map(SKILL_OPTIONS.map(label => [label.toLowerCase(), label]));

const DEGREE_ALIASES = new Map([
  ['bachelor', 'Bachelor'], ['bachelors', 'Bachelor'], ['bachelor’s', 'Bachelor'], ['bs', 'Bachelor'], ['b.s.', 'Bachelor'],
  ['master', 'Master'], ['masters', 'Master'], ['master’s', 'Master'], ['ms', 'Master'], ['m.s.', 'Master'],
  ['phd', 'PhD'], ['ph.d.', 'PhD'], ['doctorate', 'PhD']
]);
const SKILL_ALIASES = new Map([
  ['python', 'python'], ['py', 'python'], ['c++', 'c++'], ['cpp', 'c++'], ['c plus plus', 'c++'],
  ['pytorch', 'pytorch'], ['torch', 'pytorch'], ['tensorflow', 'tensorflow'], ['tf', 'tensorflow'], ['jax', 'jax'],
  ['sql', 'sql'], ['machine learning', 'machine learning'], ['ml', 'machine learning'], ['deep learning', 'deep learning'],
  ['llm', 'llms'], ['llms', 'llms'], ['large language models', 'llms'], ['nlp', 'nlp'], ['natural language processing', 'nlp'],
  ['computer vision', 'computer vision'], ['cv', 'computer vision'], ['statistics', 'statistics'], ['statistical modeling', 'statistics'],
  ['docker', 'docker'], ['kubernetes', 'kubernetes'], ['k8s', 'kubernetes'], ['cuda', 'cuda'], ['aws', 'aws'],
  ['gcp', 'gcp'], ['spark', 'spark'], ['ray', 'ray'], ['airflow', 'airflow'], ['mlops', 'mlops'],
  ['distributed systems', 'distributed systems'], ['distributed training', 'distributed systems']
]);
const STATUS_ORDER = { gap: 0, confirm: 1, aligned: 2 };

export function defaultProfile() {
  return { degree: '', graduation: '', industryYears: 0, researchYears: 0, skills: [], interests: [], states: [], relocate: true, workplace: '', priority: 'learning', minSalary: 0 };
}

function text(value) { return value === null || value === undefined ? '' : String(value).trim(); }
function key(value) { return text(value).toLowerCase().replace(/[‐‑‒–—]/g, '-').replace(/\s+/g, ' '); }
function canonicalDegree(value) { return DEGREE_ALIASES.get(key(value)) || text(value); }
function canonicalSkill(value) { return SKILL_ALIASES.get(key(value)) || key(value); }
function displaySkill(value) {
  const normalized = canonicalSkill(value);
  return SKILL_LABELS.get(normalized) || text(value);
}
function list(value) { return Array.isArray(value) ? value : value ? [value] : []; }
function numberOrNull(value) { return value === null || value === undefined || value === '' || Number.isNaN(Number(value)) ? null : Number(value); }
function unique(values) { return [...new Set(values.filter(Boolean))]; }
function hasKnown(value) { return value !== null && value !== undefined && value !== '' && value !== 'Not stated'; }

export function normalizeProfile(input = {}) {
  const base = defaultProfile();
  const p = { ...base, ...(input || {}) };
  p.degree = canonicalDegree(p.degree);
  p.graduation = p.graduation === '' || p.graduation === null || p.graduation === undefined ? '' : String(p.graduation);
  p.industryYears = Math.max(0, numberOrNull(p.industryYears) ?? 0);
  p.researchYears = Math.max(0, numberOrNull(p.researchYears) ?? 0);
  p.skills = unique(list(p.skills).map(s => displaySkill(typeof s === 'string' ? s : s?.name)).filter(Boolean));
  p.interests = unique(list(p.interests).map(text).filter(Boolean));
  p.states = unique(list(p.states).map(s => text(s).toUpperCase() === 'REMOTE' ? 'Remote' : text(s).toUpperCase()).filter(Boolean));
  p.relocate = p.relocate !== false;
  p.workplace = text(p.workplace);
  p.priority = text(p.priority) || 'learning';
  p.minSalary = Math.max(0, numberOrNull(p.minSalary) ?? 0);
  return p;
}

function pathDegreeMatch(path, profile) {
  const degrees = list(path.degrees).map(canonicalDegree);
  if (!profile.degree) return degrees.length
    ? { state: 'unknown', reason: 'A degree is stated for this path, but the profile has no selected degree.' }
    : { state: 'unknown', reason: 'The posting does not state an accepted degree for this path.' };
  if (!degrees.length) return { state: 'unknown', reason: 'The posting does not state an accepted degree for this path.' };
  return degrees.includes(profile.degree)
    ? { state: 'pass' }
    : { state: 'gap', reason: `This path lists ${degrees.join(' / ')}, not ${profile.degree}.` };
}

function pathGraduationMatch(path, profile) {
  const years = list(path.graduationYears).map(String);
  if (!profile.graduation) return years.length
    ? { state: 'unknown', reason: 'A graduation year is stated for this path, but the profile has no selected graduation year.' }
    : { state: 'pass' };
  if (!years.length) return { state: 'unknown', reason: 'The selected path does not state a graduation year.' };
  return years.includes(profile.graduation)
    ? { state: 'pass' }
    : { state: 'gap', reason: `This path lists graduation years ${years.join(', ')}, not ${profile.graduation}.` };
}

function pathExperienceMatch(path, profile, job) {
  const required = numberOrNull(path.minYears);
  const type = key(path.experienceType);
  if (required === null) {
    return { state: 'unknown', reason: 'Experience minimum is not stated for this path.' };
  }
  if (type === 'research') return profile.researchYears >= required
    ? { state: 'pass' } : { state: 'gap', reason: `This path records at least ${required} research years.` };
  if (type === 'industry') return profile.industryYears >= required
    ? { state: 'pass' } : { state: 'gap', reason: `This path records at least ${required} industry years.` };
  if (required === 0) return { state: 'pass' };
  return { state: 'unknown', reason: `Experience type '${path.experienceType}' is not mapped.` };
}

function pathAssessment(path, profile, job) {
  const checks = [pathDegreeMatch(path, profile), pathGraduationMatch(path, profile), pathExperienceMatch(path, profile, job)];
  return { state: checks.some(c => c.state === 'gap') ? 'gap' : checks.some(c => c.state === 'unknown') ? 'unknown' : 'pass', checks };
}

function matchingPath(job, profile) {
  const paths = list(job.qualificationPaths);
  if (!paths.length) return { state: 'unknown', reasons: ['No qualification path is recorded.'], path: null };
  const assessed = paths.map(path => ({ path, assessment: pathAssessment(path, profile, job) }));
  const pass = assessed.find(x => x.assessment.state === 'pass');
  if (pass) return { state: 'pass', reasons: [], path: pass.path };
  const unknown = assessed.find(x => x.assessment.state === 'unknown');
  if (unknown) return { state: 'unknown', reasons: unknown.assessment.checks.filter(c => c.state === 'unknown').map(c => c.reason), path: unknown.path };
  return { state: 'gap', reasons: assessed.flatMap(x => x.assessment.checks.filter(c => c.state === 'gap').map(c => c.reason)), path: null };
}

function requiredSkills(job) {
  const skills = list(job.skills);
  const groups = new Map();
  for (const skill of skills) {
    if (skill.level !== 'required') continue;
    const normalized = canonicalSkill(skill.name);
    const group = text(skill.alternativeGroup) || `__${normalized}`;
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(normalized);
  }
  return [...groups.values()].map(unique);
}

function skillAssessment(job, profile) {
  const owned = new Set(profile.skills.map(canonicalSkill));
  const matches = [];
  const gaps = [];
  for (const group of requiredSkills(job)) {
    const hit = group.find(skill => owned.has(skill));
    if (hit) matches.push(displaySkill(hit));
    else gaps.push(group.join(' / '));
  }
  return { matches: unique(matches), gaps: unique(gaps) };
}

function skillMentionAssessment(job, profile) {
  const owned = new Set(profile.skills.map(canonicalSkill));
  const matches = [];
  for (const skill of list(job.skills)) {
    const normalized = canonicalSkill(skill.name);
    if (normalized && owned.has(normalized)) matches.push(displaySkill(normalized));
  }
  return unique(matches);
}

function preferenceAssessment(job, profile) {
  const reasons = [];
  let score = 0;
  if (profile.interests.length && profile.interests.includes(job.roleFamily)) { score += 10; reasons.push(`Role family matches interest: ${job.roleFamily}.`); }
  const jobStates = new Set(list(job.locations).map(l => text(l.state).toUpperCase()).filter(Boolean));
  const remoteHit = Boolean(job.remote) && job.remoteScope === 'nationwide' && profile.states.length > 0;
  const stateHit = profile.states.some(state => state === 'Remote' ? Boolean(job.remote) : jobStates.has(state) || remoteHit);
  if (profile.states.length && stateHit) {
    score += 8;
    reasons.push(remoteHit && ![...jobStates].some(state => profile.states.includes(state))
      ? 'Remote-US can meet the preferred-state search; verify the employer restriction.'
      : 'A preferred state or Remote-US option is listed.');
  }
  if (profile.states.length && !stateHit && !profile.relocate) { score -= 4; reasons.push('No preferred state or Remote-US option is listed; relocation is off.'); }
  if (profile.workplace && job.workplace === profile.workplace) { score += 5; reasons.push(`Workplace matches preference: ${job.workplace}.`); }
  else if (profile.workplace) score -= 2;
  const ranges = list(job.salary).filter(s => s.currency === 'USD' && s.period === 'year');
  if (profile.priority === 'salary') {
    if (ranges.length) reasons.push('Salary priority uses the highest disclosed annual USD range ceiling; not a promised offer.');
    else reasons.push('Salary is not stated, so the salary preference needs confirmation.');
  }
  if (profile.minSalary > 0) {
    if (ranges.length && ranges.some(s => numberOrNull(s.max) >= profile.minSalary)) { score += 5; reasons.push('A disclosed salary range reaches the selected minimum.'); }
    else if (!ranges.length) { score -= 1; reasons.push('Salary is not stated, so the salary preference needs confirmation.'); }
    else { score -= 2; reasons.push('Disclosed salary ranges are below the selected minimum.'); }
  }
  if (profile.priority === 'research' && job.roleFamily === 'Research') { score += 12; reasons.push('Research priority matches this role family.'); }
  return { score, reasons };
}

export function assessJob(job = {}, rawProfile = {}) {
  const profile = normalizeProfile(rawProfile);
  const path = matchingPath(job, profile);
  const unknown = path.state === 'unknown' ? [...path.reasons] : [];
  const gaps = path.state === 'gap' ? [...path.reasons] : [];
  if (job.newgradStatus !== 'explicit') unknown.push('New-grad eligibility is not explicit in this record; confirm the full posting.');
  if (job.reviewLevel === 'automated-discovery' && job.experienceReferences?.length) unknown.unshift(`The source mentions ${job.experienceReferences.join(' / ')} years of experience. These references are not parsed qualification pathways; confirm whether they are required, preferred, or degree-specific.`);
  const skills = skillAssessment(job, profile);
  if (skills.gaps.length) unknown.push(`Required skill evidence to confirm: ${skills.gaps.join('; ')}.`);
  const skillMentionsMatched = skillMentionAssessment(job, profile);
  const preference = preferenceAssessment(job, profile);
  const status = gaps.length ? 'gap' : unknown.length ? 'confirm' : 'aligned';
  const matched = [];
  if (path.state === 'pass' && path.path) {
    if (profile.degree) matched.push(`Qualification path accepts ${profile.degree}.`);
    if (profile.graduation) matched.push(`Qualification path lists graduation year ${profile.graduation}.`);
    if (profile.industryYears > 0 && key(path.path.experienceType) === 'industry') matched.push(`Industry experience meets the recorded ${profile.industryYears}-year profile.`);
    if (profile.researchYears > 0 && key(path.path.experienceType) === 'research') matched.push(`Research experience meets the recorded ${profile.researchYears}-year profile.`);
    if (!matched.length) matched.push('At least one recorded qualification path is compatible.');
  }
  return {
    status,
    matched,
    unknown: unique(unknown),
    gaps: unique(gaps),
    preferenceReasons: preference.reasons,
    skillMatches: skills.matches,
    skillGaps: skills.gaps,
    skillMentionsMatched,
    priorityScore: STATUS_ORDER[status] * 100 + preference.score + (profile.priority === 'learning' ? skillMentionsMatched.length * 2 : skills.matches.length)
  };
}

function salaryCeiling(job) {
  return Math.max(0, ...list(job.salary).filter(s => s.currency === 'USD' && s.period === 'year').map(s => numberOrNull(s.max) || 0));
}

export function rankJobs(jobs = [], rawProfile = {}) {
  const profile = normalizeProfile(rawProfile);
  return list(jobs).map(job => ({ job, ...assessJob(job, profile) }))
    .sort((a, b) => STATUS_ORDER[b.status] - STATUS_ORDER[a.status]
      || (profile.priority === 'salary' ? salaryCeiling(b.job) - salaryCeiling(a.job) : 0)
      || b.priorityScore - a.priorityScore
      || text(a.job.company).localeCompare(text(b.job.company))
      || text(a.job.title).localeCompare(text(b.job.title))
      || text(a.job.id).localeCompare(text(b.job.id)));
}

export function summarizeMatches(ranked = []) {
  const counts = { aligned: 0, confirm: 0, gap: 0 };
  for (const item of ranked) counts[item.status] = (counts[item.status] || 0) + 1;
  return { total: ranked.length, ...counts, topAligned: ranked.filter(x => x.status === 'aligned').slice(0, 3).map(x => x.job) };
}

export function skillOpportunities(ranked = []) {
  const counts = new Map();
  for (const item of ranked) for (const gap of unique(item.skillGaps || [])) counts.set(gap, (counts.get(gap) || 0) + 1);
  return [...counts.entries()].map(([skill, postings]) => ({ skill, postings })).sort((a, b) => b.postings - a.postings || a.skill.localeCompare(b.skill));
}

export function jobSkillCoverage(jobs = [], skills = SKILL_OPTIONS) {
  const selected = new Set(list(skills).map(canonicalSkill));
  const rows = new Map();
  for (const job of jobs) {
    const seen = new Set();
    for (const skill of list(job.skills)) {
      const normalized = canonicalSkill(skill.name);
      if (!selected.has(normalized) || seen.has(normalized)) continue;
      seen.add(normalized);
      if (!rows.has(normalized)) rows.set(normalized, { skill: displaySkill(normalized), postings: 0, companies: new Set() });
      const row = rows.get(normalized);
      row.postings += 1;
      row.companies.add(job.company);
    }
  }
  return [...rows.values()].map(row => ({ ...row, companies: row.companies.size })).sort((a, b) => b.postings - a.postings || a.skill.localeCompare(b.skill));
}

export function scenarioComparison(jobs = [], profiles = {}) {
  return Object.entries(profiles).map(([name, profile]) => ({ name, summary: summarizeMatches(rankJobs(jobs, profile)) }));
}
