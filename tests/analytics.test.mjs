import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeSkills, distribution, selectJobs, skillScenario } from '../dist/analytics.js';

const job = (overrides = {}) => ({
  id: 'j1', company: 'Acme', title: 'ML role', roleFamily: 'ML Engineering',
  experienceLevel: 'entry', newgradStatus: 'explicit', remote: false,
  locations: [{ state: 'MA' }], skills: [{ name: 'Python' }, { name: 'PyTorch' }], ...overrides,
});

test('skill mentions are case and alias normalized and counted once per posting', () => {
  const jobs = [job({ skills: [{ name: 'Python' }, { name: 'python3' }, { name: 'PYTHON' }, { name: 'SQL' }, { name: 'sql' }, { name: 'LLM' }, { name: 'LLMs' }, { name: 'large language models' }] })];
  const row = distribution(jobs, 'skill').find(item => item.key === 'python');
  assert.deepEqual(row, { key: 'python', label: 'Python', count: 1, companies: 1, share: 100 });
  assert.equal(distribution(jobs, 'skill').find(item => item.key === 'sql').count, 1);
  assert.equal(distribution(jobs, 'skill').find(item => item.key === 'llms').label, 'LLMs');
});

test('role and experience distributions retain empty core groups and unspecified levels', () => {
  const rows = distribution([job({ experienceLevel: undefined, roleFamily: 'Research' })], 'experience');
  assert.equal(rows.find(row => row.key === 'unspecified').count, 1);
  assert.equal(rows.find(row => row.key === 'staff').count, 0);
  assert.equal(distribution([], 'role').every(row => row.count === 0), true);
});

test('state rows deduplicate states per posting and remote can overlap transparently', () => {
  const jobs = [job({ locations: [{ state: 'MA' }, { state: 'MA' }, { state: 'NY' }], remote: true }), job({ id: 'j2', locations: [{ state: 'MA' }] })];
  const rows = distribution(jobs, 'state');
  assert.equal(rows.find(row => row.key === 'MA').count, 2);
  assert.equal(rows.find(row => row.key === 'NY').count, 1);
  assert.equal(rows.find(row => row.key === 'remote').count, 1);
  assert.equal(rows.find(row => row.key === 'NY').share, 50);
});

test('selection filters role, independent experience, region and evidence without mutation', () => {
  const jobs = [job(), job({ id: 'j2', roleFamily: 'Research', experienceLevel: undefined, newgradStatus: 'early-career', locations: [{ state: 'CA' }], remote: true })];
  const before = structuredClone(jobs);
  assert.deepEqual(selectJobs(jobs, { role: 'Research', experience: 'unspecified', region: 'remote', evidence: 'early' }).map(item => item.id), ['j2']);
  assert.deepEqual(jobs, before);
});

test('graduate evidence includes explicit and zero experience, while experience level remains independent', () => {
  const jobs = [job({ id: 'explicit' }), job({ id: 'zero', newgradStatus: 'zero-experience', experienceLevel: 'senior' }), job({ id: 'early', newgradStatus: 'early-career' })];
  assert.deepEqual(selectJobs(jobs, { evidence: 'graduate' }).map(item => item.id), ['explicit', 'zero']);
  assert.deepEqual(selectJobs(jobs, { evidence: 'early', experience: 'senior' }).map(item => item.id), ['zero']);
});

test('skill analysis excludes preselected recommendations and reports cooccurrence/new postings', () => {
  const jobs = [job({ skills: [{ name: 'Python' }, { name: 'SQL' }] }), job({ id: 'j2', skills: [{ name: 'SQL' }, { name: 'Docker' }], company: 'Beta' })];
  const result = analyzeSkills(jobs, ['python']);
  assert.equal(result.withKnownSkillCount, 1);
  assert.equal(result.demand.find(row => row.skill === 'Python').selected, true);
  assert.equal(result.demand.find(row => row.skill === 'SQL').cooccurrenceCount, 1);
  assert.equal(result.demand.find(row => row.skill === 'Docker').newPostingCount, 1);
  assert.equal(result.recommendations.some(row => row.skill === 'Python'), false);
});

test('selected skill aliases collapse before matching', () => {
  const result = analyzeSkills([job({ skills: [{ name: 'LLMs' }] })], ['llm', 'large language models']);
  assert.deepEqual(result.selectedSkills, ['LLMs']);
  assert.equal(result.withKnownSkillCount, 1);
});

test('skill scenarios handle empty selections and increment by distinct postings', () => {
  const jobs = [job({ skills: [{ name: 'Python' }] }), job({ id: 'j2', skills: [{ name: 'SQL' }] }), job({ id: 'j3', skills: [] })];
  assert.deepEqual(skillScenario(jobs, [], 'SQL'), { before: 0, after: 1, gain: 1, total: 3 });
  assert.deepEqual(skillScenario(jobs, ['Python'], 'SQL'), { before: 1, after: 2, gain: 1, total: 3 });
});

test('reference skill filters select exactly the postings counted in the charts', () => {
  const jobs = [job({ id:'llm', skills:[{name:'large language models'},{name:'LLMs'}] }), job({ id:'sql', skills:[{name:'SQL'}] }), job({ id:'empty', skills:[] })];
  for (const row of distribution(jobs,'skill')) {
    assert.equal(selectJobs(jobs,{skill:row.label}).length,row.count);
  }
  assert.deepEqual(selectJobs(jobs,{skill:'LLM'}).map(j=>j.id),['llm']);
  assert.deepEqual(selectJobs(jobs,{skill:'SQL',q:'acme',experience:'entry'}).map(j=>j.id),['sql']);
  assert.equal(selectJobs(jobs,{skill:'SQL',q:'python'}).length,0);
});
