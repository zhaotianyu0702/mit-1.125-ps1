import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { assessJob } from '../dist/matching.js';
const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url)));
const levels=new Set(['entry','senior','staff','manager','unspecified']);
test('each published role has a traceable experience label independent of graduate evidence',()=>{
  for(const j of data.jobs){
    assert.ok(levels.has(j.experienceLevel),j.id);
    assert.ok(['title','curated','requirements','scope','unknown'].includes(j.experienceLevelBasis),j.id);
    assert.ok(j.experienceLevelEvidence,j.id);
    assert.ok(Array.isArray(j.experienceReferences),j.id);
    assert.ok(j.experienceReferences.every(n=>Number.isFinite(n)&&n>=0),j.id);
  }
});
test('unparsed year references prompt source review and never imply a hard qualification verdict',()=>{
  const role={id:'example',company:'Example',title:'Senior ML Engineer',roleFamily:'ML Engineering',newgradStatus:'unclear',reviewLevel:'automated-discovery',experienceLevel:'senior',experienceReferences:[5,10],qualificationPaths:[{degrees:[],minYears:null,graduationYears:[]}],locations:[],skills:[],salary:[]};
  const result=assessJob(role,{degree:'Master',industryYears:0});
  assert.equal(result.status,'confirm');
  assert.deepEqual(result.gaps,[]);
  assert.ok(result.unknown.some(t=>t.includes('5 / 10')));
});

// Descriptive source inferences must remain auditable and separate from paths.
test('source-inferred levels preserve a matching excerpt and source record',()=>{
  const inferred=data.jobs.filter(j=>['requirements','scope'].includes(j.experienceLevelBasis));
  assert.ok(inferred.length>0);
  for(const j of inferred){
    assert.ok(j.experienceEvidenceSource?.excerpt,j.id);
    assert.ok(j.experienceEvidenceSource.url.startsWith('https://'),j.id);
    assert.equal(j.experienceEvidenceSource.verifiedAt,j.verifiedAt,j.id);
    if(j.experienceLevelBasis==='requirements' && j.requirementYears?.length){
      assert.ok(j.requirementYears?.length,j.id);
      const n=j.classifiedRequirementYears;
      assert.ok(Number.isFinite(n),j.id);
      assert.equal(j.experienceLevel,n<=2?'entry':'senior',j.id);
    }
  }
});
