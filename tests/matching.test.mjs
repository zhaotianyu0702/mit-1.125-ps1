import test from 'node:test';
import assert from 'node:assert/strict';
import {
  assessJob,
  defaultProfile,
  jobSkillCoverage,
  normalizeProfile,
  rankJobs,
  skillOpportunities,
  summarizeMatches
} from '../dist/matching.js';

const path = ({ degrees = ['Bachelor'], minYears = 0, experienceType = 'industry', graduationYears = [] } = {}) => ({ degrees, minYears, experienceType, graduationYears, evidence: 'test qualification path' });
const job = (overrides = {}) => ({
  id: 'test-job', company: 'Example', title: 'ML Engineer', roleFamily: 'ML Engineering',
  newgradStatus: 'explicit', locations: [{ city: 'Seattle', state: 'WA', country: 'US' }], remote: false, workplace: 'Hybrid',
  qualificationPaths: [path()], skills: [], salary: [], ...overrides
});

test('normalizes degree, skill aliases, state, and numeric profile fields', () => {
  const p = normalizeProfile({ degree: 'MS', skills: ['PyTorch', 'C plus plus', 'LLM'], states: ['remote', 'wa'], industryYears: '2' });
  assert.equal(p.degree, 'Master');
  assert.deepEqual(p.skills, ['PyTorch', 'C++', 'LLMs']);
  assert.deepEqual(p.states, ['Remote', 'WA']);
  assert.equal(p.industryYears, 2);
  assert.deepEqual(defaultProfile().skills, []);
});

test('uses an accepted degree path and does not flatten conditional experience paths', () => {
  const result = assessJob(job({ qualificationPaths: [
    path({ degrees: ['Bachelor', 'Master'], minYears: 0 }),
    path({ degrees: ['PhD'], minYears: 3, experienceType: 'industry' })
  ] }), { degree: 'Bachelor', industryYears: 0 });
  assert.equal(result.status, 'aligned');
  assert.equal(result.gaps.length, 0);
});

test('checks graduation on the same degree path', () => {
  const result = assessJob(job({ qualificationPaths: [
    path({ degrees: ['Bachelor'], minYears: 0, graduationYears: [2026] }),
    path({ degrees: ['Master'], minYears: 0, graduationYears: [2027] })
  ] }), { degree: 'Bachelor', graduation: 2027 });
  assert.equal(result.status, 'gap');
  assert.match(result.gaps.join(' '), /2026/);
});

test('unknown experience is confirmation, never zero', () => {
  const result = assessJob(job({ qualificationPaths: [path({ minYears: null })] }), { degree: 'Bachelor', industryYears: 0 });
  assert.equal(result.status, 'confirm');
  assert.ok(result.unknown.some(x => /Experience minimum/.test(x)));
});

test('missing profile degree or graduation is confirmation when the source constrains it', () => {
  const result = assessJob(job({ qualificationPaths: [path({ degrees: ['Master'], graduationYears: [2027] })] }), {});
  assert.equal(result.status, 'confirm');
  assert.ok(result.unknown.some(x => /no selected degree/.test(x)));
  assert.ok(result.unknown.some(x => /no selected graduation/.test(x)));
});

test('unknown experience type is not assumed to be industry experience', () => {
  const result = assessJob(job({ qualificationPaths: [path({ minYears: 2, experienceType: 'professional or equivalent' })] }), { degree: 'Bachelor', industryYears: 5 });
  assert.equal(result.status, 'confirm');
  assert.ok(result.unknown.some(x => /not mapped/.test(x)));
  assert.deepEqual(result.gaps, []);
});

test('research years are separate from industry years', () => {
  const research = job({ qualificationPaths: [path({ degrees: ['PhD'], minYears: 2, experienceType: 'research' })] });
  assert.equal(assessJob(research, { degree: 'PhD', industryYears: 5, researchYears: 0 }).status, 'gap');
  assert.equal(assessJob(research, { degree: 'PhD', industryYears: 0, researchYears: 2 }).status, 'aligned');
});

test('alternative required skills satisfy one OR group and repeated skills count once', () => {
  const result = assessJob(job({ skills: [
    { name: 'Python', level: 'required', alternativeGroup: 'language' },
    { name: 'Python', level: 'required', alternativeGroup: 'language' },
    { name: 'PyTorch', level: 'required', alternativeGroup: 'framework' },
    { name: 'TensorFlow', level: 'required', alternativeGroup: 'framework' }
  ] }), { degree: 'Bachelor', skills: ['Python', 'TensorFlow'] });
  assert.equal(result.status, 'aligned');
  assert.deepEqual(result.skillMatches.sort(), ['Python', 'TensorFlow']);
  assert.deepEqual(result.skillGaps, []);
  assert.deepEqual(result.skillMentionsMatched.sort(), ['Python', 'TensorFlow']);
});

test('skill gaps ask for confirmation rather than rejecting a role', () => {
  const result = assessJob(job({ skills: [{ name: 'CUDA', level: 'required', alternativeGroup: null }] }), { degree: 'Bachelor' });
  assert.equal(result.status, 'confirm');
  assert.deepEqual(result.gaps, []);
  assert.deepEqual(result.skillGaps, ['cuda']);
});

test('non-explicit new-grad status remains a confirmation', () => {
  const result = assessJob(job({ newgradStatus: 'zero-experience' }), { degree: 'Bachelor' });
  assert.equal(result.status, 'confirm');
  assert.ok(result.unknown.some(x => /New-grad eligibility/.test(x)));
});

test('preferences affect score and explanation, not recruiting eligibility', () => {
  const base = assessJob(job(), { degree: 'Bachelor' });
  const preference = assessJob(job(), { degree: 'Bachelor', states: ['CA'], relocate: false, workplace: 'Remote', interests: ['Research'], minSalary: 200000 });
  assert.equal(base.status, 'aligned');
  assert.equal(preference.status, 'aligned');
  assert.ok(preference.preferenceReasons.some(x => /No preferred state/.test(x)));
  assert.ok(preference.priorityScore < base.priorityScore);
});

test('research priority and disclosed salary are useful tie-breakers within a status', () => {
  const research = job({ id: 'research', roleFamily: 'Research', salary: [{ currency: 'USD', period: 'year', min: 100000, max: 180000 }] });
  const ml = job({ id: 'ml', roleFamily: 'ML Engineering', salary: [] });
  const ranked = rankJobs([ml, research], { degree: 'Bachelor', priority: 'research' });
  assert.equal(ranked[0].job.id, 'research');
  assert.ok(ranked[0].preferenceReasons.some(x => /Research priority/.test(x)));
});

test('remote listing can satisfy a preferred-state search with a restriction note', () => {
  const result = assessJob(job({ remote: true, remoteScope: 'nationwide', locations: [] }), { degree: 'Bachelor', states: ['WA'], relocate: false });
  assert.equal(result.status, 'aligned');
  assert.ok(result.preferenceReasons.some(x => /Remote-US can meet/.test(x)));
});

test('ranking is deterministic, aligned first, and summaries are useful', () => {
  const jobs = [job({ id: 'gap', company: 'Zed', qualificationPaths: [path({ degrees: ['Master'] })] }), job({ id: 'aligned', company: 'Alpha' })];
  const ranked = rankJobs(jobs, { degree: 'Bachelor' });
  assert.deepEqual(ranked.map(x => x.job.id), ['aligned', 'gap']);
  assert.deepEqual(summarizeMatches(ranked), { total: 2, aligned: 1, confirm: 0, gap: 1, topAligned: [jobs[1]] });
  assert.deepEqual(skillOpportunities(ranked), []);
  assert.deepEqual(jobSkillCoverage(jobs, ['Python']), []);
});


test('salary priority changes order without turning unknown eligibility into alignment', () => {
  const low = job({id: 'low', company:'Alpha', skills:[{name:'Python',level:'mentioned'}], salary:[{min:90000,max:120000,currency:'USD',period:'year'}]});
  const high = job({id:'high',company:'Beta',salary:[{min:100000,max:180000,currency:'USD',period:'year'}]});
  const unverified = job({id:'unknown',newgradStatus:'unclear',salary:[{min:200000,max:500000,currency:'USD',period:'year'}]});
  assert.deepEqual(rankJobs([high,low],{degree:'Bachelor',skills:['Python'],priority:'learning'}).map(x=>x.job.id),['low','high']);
  assert.deepEqual(rankJobs([unverified,low,high],{degree:'Bachelor',skills:['Python'],priority:'salary'}).map(x=>x.job.id),['high','low','unknown']);
});

test('state-limited or unspecified remote work does not imply nationwide eligibility', () => {
  for(const remoteScope of ['state-limited','unspecified']) {
    const r=assessJob(job({remote:true,remoteScope,locations:[{city:'Los Angeles',state:'CA',country:'US'}]}),{degree:'Bachelor',states:['MA'],relocate:false});
    assert.ok(r.preferenceReasons.some(x=>x.startsWith('No preferred state')));
    assert.ok(!r.preferenceReasons.some(x=>x.startsWith('Remote-US can meet')));
  }
});
