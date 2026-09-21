import { EXPERIENCE_LEVELS, EXPERIENCE_LEVEL_LABELS, ROLE_FAMILIES, experienceLevel } from './core.js?v=3.4';

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
export const jobSkills = job => {
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
  const skill = filters.skill ?? 'all';
  const query = normalize(filters.q).split(/\s+/).filter(Boolean);
  return jobs.filter(job => {
    if (role !== 'all' && text(job?.roleFamily) !== role) return false;
    if (level !== 'all' && experienceLevel(job) !== level) return false;
    if (region === 'remote') {
      if (!job?.remote) return false;
    } else if (region !== 'all' && !jobStates(job).includes(text(region).toUpperCase())) {
      return false;
    }
    if (skill !== 'all' && !jobSkills(job).some(value=>skillKey(value)===skillKey(skill))) return false;
    const searchable=normalize([job.company,job.title,job.roleFamily,...jobSkills(job)].join(' '));
    if (!query.every(term=>searchable.includes(term))) return false;
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

// One fixed learning target for the site. Explicit thresholds are only used
// by the offline sensitivity study and tests, never by user or URL controls.
export const SKILL_COVERAGE_TARGET = 70;
const skillThreshold = value => Number.isFinite(Number(value)) && Number(value) > 0 && Number(value) <= 100 ? Number(value) : SKILL_COVERAGE_TARGET;

function normalizedSelection(selectedSkills) {
  const byKey = new Map();
  for (const value of selectedSkills) {
    const display=canonicalSkill(value), key=skillKey(display);
    if(key && !byKey.has(key))byKey.set(key,display);
  }
  return byKey;
}

export function postingSkillCoverage(job, selectedSkills = [], threshold = SKILL_COVERAGE_TARGET) {
  const selected = new Set(normalizedSelection(selectedSkills).keys());
  return coverageRecord(job, selected, skillThreshold(threshold));
}
function coverageRecord(job, selected, threshold) {
  const skills = jobSkills(job), keys = skills.map(skillKey);
  const matched = keys.filter(key=>selected.has(key)).length;
  const required = Math.ceil(skills.length * threshold / 100);
  const scorable = skills.length > 0;
  return {skills, matched, total:skills.length, required, scorable,
    coverage:scorable ? percent(matched,skills.length) : null,
    covered:scorable && matched>=required,
    missing:skills.filter(skill=>!selected.has(skillKey(skill)))};
}

export function analyzeSkills(jobs = [], selectedSkills = [], threshold = SKILL_COVERAGE_TARGET) {
  threshold=skillThreshold(threshold);
  const selectedByKey=normalizedSelection(selectedSkills);
  const selectedKeys=new Set(selectedByKey.keys());
  const records=jobs.map(job=>coverageRecord(job,selectedKeys,threshold));
  const scorable=records.filter(row=>row.scorable);
  const coveredCount=scorable.filter(row=>row.covered).length;
  const oneAwayCount=scorable.filter(row=>row.required-row.matched===1).length;
  const byRole=ROLE_FAMILIES.map(key=>{
    const indexes=jobs.map((job,index)=>[job,index]).filter(([job])=>job.roleFamily===key).map(([,index])=>index);
    const eligible=indexes.map(index=>records[index]).filter(row=>row.scorable);
    const covered=eligible.filter(row=>row.covered).length;
    return {key,label:key,count:indexes.length,eligibleCount:eligible.length,coveredCount:covered,coveredShare:percent(covered,eligible.length)};
  });
  const demandMap=new Map();
  jobs.forEach((job,index)=>{
    const record=records[index];
    for(const skill of record.skills){
      const key=skillKey(skill);
      const row=demandMap.get(key)||{skill,count:0,companies:new Set(),gainCompanies:new Set(),gain:0,closerCount:0,progressGain:0};
      row.count++;
      if(job.company)row.companies.add(companyKey(job.company));
      if(!selectedKeys.has(key) && !record.covered){
        if(record.matched+1>=record.required){row.gain++;if(job.company)row.gainCompanies.add(companyKey(job.company));}
        else row.closerCount++;
        // Each previously unmet posting contributes at most one full target's
        // progress; adding a skill contributes 1 / ceil(skill count * target).
        row.progressGain+=1/record.required;
      }
      demandMap.set(key,row);
    }
  });
  const demand=[...demandMap.entries()].map(([key,row])=>({skill:row.skill,count:row.count,share:percent(row.count,jobs.length),companies:row.companies.size,selected:selectedKeys.has(key),gain:row.gain,gainCompanies:row.gainCompanies.size,closerCount:row.closerCount,progressGain:row.progressGain}))
    .sort((a,b)=>b.count-a.count||b.companies-a.companies||a.skill.localeCompare(b.skill));
  const recommendations=demand.filter(row=>!row.selected && (row.gain || row.closerCount))
    .sort((a,b)=>b.gain-a.gain||b.progressGain-a.progressGain||b.companies-a.companies||a.skill.localeCompare(b.skill)).slice(0,3);
  return {selectedSkills:[...selectedByKey.values()],threshold,total:jobs.length,eligibleCount:scorable.length,unscoredCount:jobs.length-scorable.length,coveredCount,coveredShare:percent(coveredCount,scorable.length),oneAwayCount,byRole,demand,recommendations};
}

export function skillScenario(jobs = [], selectedSkills = [], skill, threshold = SKILL_COVERAGE_TARGET) {
  const before=analyzeSkills(jobs,selectedSkills,threshold);
  const after=analyzeSkills(jobs,[...selectedSkills,skill],threshold);
  const candidate=before.demand.find(row=>skillKey(row.skill)===skillKey(skill));
  return {before:before.coveredCount,after:after.coveredCount,gain:after.coveredCount-before.coveredCount,total:before.eligibleCount,unscoredCount:before.unscoredCount,threshold:before.threshold,closerCount:candidate?.closerCount||0};
}
