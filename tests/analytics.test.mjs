import test from 'node:test';
import assert from 'node:assert/strict';
import { analyzeSkills, distribution, selectJobs, skillScenario, postingSkillCoverage, SKILL_COVERAGE_TARGET } from '../dist/analytics.js';

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

test('coverage uses the fraction of distinct posting skills and rounds the target up', () => {
  const role=job({skills:['Python','python3','SQL','Docker','PyTorch','LLMs']});
  assert.equal(postingSkillCoverage(role,['Python','SQL'],60).covered,false);
  const covered=postingSkillCoverage(role,['Python','SQL','LLM'],60);
  assert.equal(covered.total,5);assert.equal(covered.matched,3);assert.equal(covered.required,3);assert.equal(covered.covered,true);
  assert.equal(postingSkillCoverage(job(),['Python'],50).covered,true);
  assert.equal(postingSkillCoverage(job(),['Python'],60).covered,false);
});

test('the fixed site target agrees across posting, role and what-if coverage', () => {
  const posting=job({skills:['Python','Machine learning','LLMs','SQL','PyTorch']});
  const selected=['Python','Machine learning','LLMs'];
  assert.equal(SKILL_COVERAGE_TARGET,70);
  assert.equal(postingSkillCoverage(posting,selected).required,4);
  assert.equal(postingSkillCoverage(posting,selected).covered,false);
  const before=analyzeSkills([posting],selected);
  assert.equal(before.threshold,70);
  assert.equal(before.coveredCount,0);
  assert.equal(before.byRole.find(r=>r.key==='ML Engineering').coveredCount,0);
  assert.equal(skillScenario([posting],selected,'SQL').gain,1);
  assert.equal(analyzeSkills([posting],[...selected,'SQL']).coveredCount,1);
  // A four-skill posting can miss one; an 80% cutoff would require all four.
  assert.equal(postingSkillCoverage(job({skills:['Python','SQL','PyTorch','LLMs']}),['Python','SQL','LLMs']).covered,true);
});

test('offline sensitivity studies can compare 70, 75 and 80 without fallback', () => {
  const posting=job({skills:['Python','SQL','Docker','CUDA','AWS','Spark','Ray']});
  const selected=['Python','SQL','Docker','CUDA','AWS'];
  assert.equal(analyzeSkills([posting],selected,70).coveredCount,1);
  assert.equal(analyzeSkills([posting],selected,75).coveredCount,0);
  assert.equal(analyzeSkills([posting],selected,80).coveredCount,0);
});

test('unknown skill lists are unscored and excluded from each role denominator', () => {
  const jobs=[job({skills:['Python']}),job({id:'unknown',skills:[]})];
  const result=analyzeSkills(jobs,['Python']);
  assert.equal(result.total,2);assert.equal(result.eligibleCount,1);assert.equal(result.unscoredCount,1);
  assert.equal(result.coveredCount,1);assert.equal(result.coveredShare,100);
  assert.equal(result.byRole.find(r=>r.key==='ML Engineering').eligibleCount,1);
  assert.equal(postingSkillCoverage(jobs[1],[]).covered,false);
  assert.equal(analyzeSkills([],[]).coveredShare,0);
});

test('marginal recommendations outrank more frequent skills that do not cross the target', () => {
  const jobs=[job({skills:['Python','SQL']}),job({id:'other',skills:['Docker','CUDA','AWS','Spark','Ray']}),job({id:'third',skills:['Docker','C++','PyTorch','GCP','Java']})];
  const before=structuredClone(jobs);
  const result=analyzeSkills(jobs,['Python'],60);
  assert.equal(result.recommendations[0].skill,'SQL');assert.equal(result.recommendations[0].gain,1);
  assert.equal(result.demand.find(r=>r.skill==='Docker').count,2);
  assert.equal(result.demand.find(r=>r.skill==='Docker').gain,0);
  assert.equal(result.demand.find(r=>r.skill==='Docker').closerCount,2);
  assert.equal(result.recommendations.some(r=>r.skill==='Python'),false);
  assert.deepEqual(jobs,before);
});

test('aliases collapse in both the selection and the posting denominator', () => {
  const result=analyzeSkills([job({skills:['LLMs','LLM','large language models','SQL']})],['llm','large language models'],60);
  assert.deepEqual(result.selectedSkills,['LLMs']);assert.equal(result.coveredCount,0);assert.equal(result.oneAwayCount,1);
  assert.equal(result.recommendations[0].skill,'SQL');assert.equal(result.recommendations[0].gain,1);
});

test('scenarios distinguish crossing the target from intermediate progress', () => {
  const jobs=[job({skills:['Python','SQL']}),job({id:'j2',skills:['Python','SQL','Docker','CUDA','AWS']}),job({id:'j3',skills:[]})];
  assert.deepEqual(skillScenario(jobs,['Python'],'SQL',60),{before:0,after:1,gain:1,total:2,unscoredCount:1,threshold:60,closerCount:1});
  assert.equal(skillScenario(jobs,['Python'],'Python',60).gain,0);
  assert.equal(analyzeSkills(jobs,[],60).coveredCount,0);
  assert.equal(analyzeSkills(jobs,['Python','SQL','Docker','CUDA','AWS'],60).recommendations.length,0);
});

test('coverage is monotone in skills and inverse-monotone in threshold; card gains equal scenarios', () => {
  const jobs=[job({skills:['Python','SQL','Docker']}),job({id:'j2',skills:['Python','SQL','Docker','AWS','CUDA']}),job({id:'j3',skills:['Python']})];
  const counts=[40,50,60,70,80].map(t=>analyzeSkills(jobs,['Python','SQL'],t).coveredCount);
  assert.ok(counts.every((count,i)=>i===0||count<=counts[i-1]));
  for(const threshold of [40,60,80]){
    const before=analyzeSkills(jobs,['Python'],threshold);
    for(const row of before.demand.filter(r=>!r.selected)){
      const result=skillScenario(jobs,['Python'],row.skill,threshold);
      assert.equal(result.gain,row.gain);assert.equal(result.closerCount,row.closerCount);assert.ok(result.gain>=0);
    }
  }
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
