import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {ROLE_FAMILIES,aggregate,freshFilters,filteredJobs} from '../dist/core.js';
const data=JSON.parse(readFileSync(new URL('../dist/data.json',import.meta.url)));
test('every published job has a unique ID and necessary source evidence',()=>{const ids=new Set();for(const j of data.jobs){assert.ok(!ids.has(j.id),j.id);ids.add(j.id);for(const key of ['company','title','url','source','sourceId','verifiedAt','newgradEvidence','aiEvidence','reviewNote'])assert.ok(j[key],`${j.id}: ${key}`);assert.ok(/^https:\/\//.test(j.url));assert.ok(ROLE_FAMILIES.includes(j.roleFamily),j.roleFamily);assert.ok(j.locations.length||j.remote);assert.ok(j.locations.every(l=>l.country==='US'));assert.ok(['explicit','zero-experience','early-career','unclear'].includes(j.newgradStatus));assert.ok(j.qualificationPaths.length);assert.ok(j.salary.every(s=>s.min>=0&&s.max>=s.min));}});
test('official source URLs and employer IDs are unique within the snapshot',()=>{assert.equal(new Set(data.jobs.map(j=>j.url)).size,data.jobs.length);assert.equal(new Set(data.jobs.map(j=>j.company+'::'+j.sourceId)).size,data.jobs.length);});
test('all role-chart counts sum to the same filtered posting total',()=>{for(const degree of ['', 'Bachelor','Master','PhD']){const f=freshFilters();f.degrees=degree?[degree]:[];const jobs=filteredJobs(data.jobs,f);const a=aggregate(jobs);assert.equal(a.total,jobs.length);assert.equal(a.roles.reduce((s,r)=>s+r.count,0),jobs.length);assert.equal(a.companies,new Set(jobs.map(j=>j.company)).size);}});
test('integration exclusions are absent from the published sample',()=>{for(const x of data.excluded)assert.ok(!data.jobs.some(j=>j.id===x.id));});

test('automated discovery never creates implied graduate qualification or pay evidence',()=>{for(const j of data.jobs.filter(j=>j.reviewLevel==='automated-discovery')){assert.equal(j.newgradStatus,'unclear');assert.equal(j.salary.length,0);for(const p of j.qualificationPaths){assert.equal(p.minYears,null);assert.deepEqual(p.degrees,[]);assert.deepEqual(p.graduationYears,[]);}}});
