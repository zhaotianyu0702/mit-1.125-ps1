import { EXPERIENCE_LEVELS, EXPERIENCE_LEVEL_LABELS, ROLE_FAMILIES, experienceLevel } from './core.js';

const GRADUATE_STATUSES = new Set(['explicit', 'zero-experience']);
const EARLY_STATUSES = new Set([...GRADUATE_STATUSES, 'early-career']);
const SKILL_ALIASES = new Map([
  ['python', 'Python'], ['python3', 'Python'], ['py', 'Python'],
  ['pytorch', 'PyTorch'], ['torch', 'PyTorch'],
  ['tensorflow', 'TensorFlow'], ['tf', 'TensorFlow'],
  ['sql', 'SQL'], ['cuda', 'CUDA'], ['docker', 'Docker'],
  ['kubernetes', 'Kubernetes'], ['k8s', 'Kubernetes'],
  ['scikit-learn', 'scikit-learn'], ['sklearn', 'scikit-learn'],
  ['machine learning', 'Machine learning'], ['machine-learning', 'Machine learning'],
  ['deep learning', 'Deep learning'], ['deep-learning', 'Deep learning'],
  ['reinforcement learning', 'Reinforcement learning'], ['computer vision', 'Computer vision'],
  ['llm', 'LLMs'], ['llms', 'LLMs'],
  ['large language models', 'LLMs'], ['large language model', 'LLMs'],
]);

const text = value => String(value ?? '').trim();
const normalize = value => text(value).toLowerCase().replace(/\s+/g, ' ');
const canonicalSkill = value => {
  const raw = text(value);
  if (!raw) return '';
  return SKILL_ALIASES.get(normalize(raw)) || raw;
};
const skillKey = value => normalize(canonicalSkill(value));
const unique = values => [...new Set(values.filter(Boolean))];
const companyKey = value => normalize(value);
const jobSkills = job => {
  const byKey = new Map();
  for (const skill of (job?.skills || [])) {
    const display = canonicalSkill(typeof skill === 'string' ? skill : skill?.name);
    const key = skillKey(display);
    if (key && !byKey.has(key)) byKey.set(key, display);
  }
  return [...byKey.values()];
};
const jobStates = job => unique((job?.locations || []).map(location => text(location?.state).toUpperCase()).filter(Boolean));
const percent = (count, total) => total ? Math.round((count / total) * 1000) / 10 : 0;

function evidenceMatches(job, evidence) {
  if (evidence === 'graduate') return GRADUATE_STATUSES.has(text(job?.newgradStatus));
  if (evidence === 'early') return EARLY_STATUSES.has(text(job?.newgradStatus));
  return true;
}

export function selectJobs(jobs = [], filters = {}) {
  const role = filters.role ?? 'all';
  const level = filters.experience ?? 'all';
  const region = filters.region ?? 'all';
  const evidence = filters.evidence ?? 'all';
  return jobs.filter(job => {
    if (role !== 'all' && text(job?.roleFamily) !== role) return false;
    if (level !== 'all' && experienceLevel(job) !== level) return false;
    if (region === 'remote') {
      if (!job?.remote) return false;
    } else if (region !== 'all' && !jobStates(job).includes(text(region).toUpperCase())) {
      return false;
    }
    return evidenceMatches(job, evidence);
  });
}

function emptyRows(dimension) {
  if (dimension === 'role') return ROLE_FAMILIES.map(key => ({ key, label: key }));
  if (dimension === 'experience') return EXPERIENCE_LEVELS.map(key => ({ key, label: EXPERIENCE_LEVEL_LABELS[key] || key }));
  return [];
}

export function distribution(jobs = [], dimension) {
  const rows = new Map(emptyRows(dimension).map(row => [row.key, row]));
  const add = (key, label, job) => {
    if (!key) return;
    if (!rows.has(key)) rows.set(key, { key, label });
    const row = rows.get(key);
    row.count = (row.count || 0) + 1;
    row._companies ||= new Set();
    if (job?.company) row._companies.add(companyKey(job.company));
  };
  for (const job of jobs) {
    if (dimension === 'role') add(text(job?.roleFamily), text(job?.roleFamily), job);
    else if (dimension === 'experience') {
      const key = experienceLevel(job);
      add(key, EXPERIENCE_LEVEL_LABELS[key] || key, job);
    } else if (dimension === 'state') {
      for (const state of jobStates(job)) add(state, state, job);
      if (job?.remote) add('remote', 'Remote', job);
    } else if (dimension === 'skill') {
      for (const skill of jobSkills(job)) add(skillKey(skill), skill, job);
    } else if (dimension === 'company') add(text(job?.company), text(job?.company), job);
  }
  // Shares use postings as the denominator for every dimension. State rows may
  // overlap because one posting can name several states (or be remote).
  const total = jobs.length;
  return [...rows.values()]
    .map(row => ({ key: row.key, label: row.label, count: row.count || 0, companies: row._companies?.size || 0, share: percent(row.count || 0, total) }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label));
}

export function analyzeSkills(jobs = [], selectedSkills = []) {
  const selectedByKey = new Map();
  for (const skill of selectedSkills) {
    const display = canonicalSkill(skill);
    if (skillKey(display) && !selectedByKey.has(skillKey(display))) selectedByKey.set(skillKey(display), display);
  }
  const selected = [...selectedByKey.values()];
  const selectedKeys = new Set(selected.map(skillKey));
  const postingSkills = jobs.map(job => new Set(jobSkills(job).map(skillKey)));
  const withKnownSkill = postingSkills.filter(skills => selectedKeys.size && [...selectedKeys].some(skill => skills.has(skill))).length;
  const byRole = ROLE_FAMILIES.map(key => {
    const indexes = jobs.map((job, index) => [job, index]).filter(([job]) => text(job?.roleFamily) === key).map(([, index]) => index);
    const count = indexes.length;
    const known = indexes.filter(index => selectedKeys.size && [...selectedKeys].some(skill => postingSkills[index].has(skill))).length;
    return { key, label: key, count, withKnownSkillCount: known, withKnownSkillShare: percent(known, count) };
  });
  const demandMap = new Map();
  jobs.forEach((job, index) => {
    for (const skill of new Set(jobSkills(job))) {
      const key = skillKey(skill);
      const row = demandMap.get(key) || { skill, count: 0, companies: new Set(), cooccurrenceCount: 0, newPostingCount: 0 };
      row.count++;
      if (job?.company) row.companies.add(companyKey(job.company));
      if ([...selectedKeys].some(selectedKey => postingSkills[index].has(selectedKey))) row.cooccurrenceCount++;
      else row.newPostingCount++;
      demandMap.set(key, row);
    }
  });
  const demand = [...demandMap.entries()].map(([key, row]) => ({ skill: row.skill, count: row.count, share: percent(row.count, jobs.length), companies: row.companies.size, selected: selectedKeys.has(key), cooccurrenceCount: row.cooccurrenceCount, newPostingCount: row.newPostingCount }))
    .sort((a, b) => b.count - a.count || b.companies - a.companies || a.skill.localeCompare(b.skill));
  return { selectedSkills: selected, total: jobs.length, withKnownSkillCount: withKnownSkill, withKnownSkillShare: percent(withKnownSkill, jobs.length), byRole, demand, recommendations: demand.filter(row => !row.selected).slice(0, 3) };
}

export function skillScenario(jobs = [], selectedSkills = [], skill) {
  const before = analyzeSkills(jobs, selectedSkills).withKnownSkillCount;
  const after = analyzeSkills(jobs, [...selectedSkills, skill]).withKnownSkillCount;
  return { before, after, gain: after - before, total: jobs.length };
}
