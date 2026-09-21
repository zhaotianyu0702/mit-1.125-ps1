import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {analyzeSkills,jobSkills,selectJobs,SKILL_THRESHOLDS} from '../dist/analytics.js';

const raw=readFileSync(new URL('../dist/data.json',import.meta.url));
const data=JSON.parse(raw);
const profiles={
  'No skills':[],
  'Python + ML':['Python','Machine learning'],
  'Python + ML + SQL':['Python','Machine learning','SQL'],
  'ML toolkit':['Python','Machine learning','LLMs','PyTorch','SQL'],
  'ML systems':['Python','Machine learning','LLMs','PyTorch','Docker','Kubernetes','CUDA'],
  'Data analysis':['Python','SQL','Spark','Machine learning']
};
const slices={All:data.jobs,Entry:selectJobs(data.jobs,{experience:'entry'}),...Object.fromEntries([...new Set(data.jobs.map(job=>job.roleFamily))].map(role=>[role,selectJobs(data.jobs,{role})]))};
const rows=[];
for(const [slice,jobs] of Object.entries(slices))for(const [profile,skills] of Object.entries(profiles))for(const threshold of SKILL_THRESHOLDS){
 const a=analyzeSkills(jobs,skills,threshold);
 rows.push({slice,profile,threshold,total:a.total,scored:a.eligibleCount,covered:a.coveredCount,share:a.coveredShare,oneAway:a.oneAwayCount,recommendations:a.recommendations.map(({skill,gain,closerCount})=>({skill,gain,closerCount}))});
}
const skillsCounts=data.jobs.map(job=>jobSkills(job).length);
const oldAnyMatch=data.jobs.filter(job=>jobSkills(job).some(skill=>profiles['Python + ML'].includes(skill))).length;
const report={snapshot:data.meta.snapshotDate,dataSha256:createHash('sha256').update(raw).digest('hex'),formula:'matched >= ceil(unique tracked skills * threshold / 100)',default:60,total:data.jobs.length,skillLess:skillsCounts.filter(n=>!n).length,oneOrTwoSkills:skillsCounts.filter(n=>n>0&&n<=2).length,oldAnyMatch,profiles,rows};
writeFileSync(new URL('../research/skill-threshold-study.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
const lines=['# Skill target comparison','',`Snapshot: ${report.snapshot}. ${report.total} postings; ${report.total-report.skillLess} have tracked skills.`, '', 'Synthetic skill sets illustrate sensitivity; they are not student survey results. A posting meets a target only when selected skills cover at least that proportion of its distinct tracked skills. No tracked skills means unscored, never a zero-skill match.','', '## Python + Machine learning', '', `The previous any-skill rule counted ${oldAnyMatch}/${report.total} postings (${(100*oldAnyMatch/report.total).toFixed(1)}%). The new denominator excludes ${report.skillLess} postings without tracked skills.`, '', '| Target | Postings meeting target | Share of scored postings | Best single addition | Newly reaching target |', '| --- | ---: | ---: | --- | ---: |'];
for(const row of rows.filter(r=>r.slice==='All'&&r.profile==='Python + ML')){const best=row.recommendations[0];lines.push(`| ${row.threshold}% | ${row.covered}/${row.scored} | ${row.share}% | ${best.skill} | +${best.gain} |`);}
lines.push('', '## Sensitivity to selected skills', '', '| Example skill set | 40% | 50% | 60% | 70% | 80% |','| --- | ---: | ---: | ---: | ---: | ---: |');
for(const profile of Object.keys(profiles))lines.push(`| ${profile} | ${rows.filter(r=>r.slice==='All'&&r.profile===profile).map(r=>r.covered).join(' | ')} |`);
lines.push('', '## Sensitivity across directions', '', 'Python + Machine learning; cell values count postings meeting the target.','', '| Slice | Scored | 40% | 50% | 60% | 70% | 80% |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |');
for(const slice of Object.keys(slices)){const group=rows.filter(r=>r.slice===slice&&r.profile==='Python + ML');lines.push(`| ${slice} | ${group[0].scored} | ${group.map(r=>r.covered).join(' | ')} |`);}
lines.push('', '## Default and recommendation rule', '', '60% is a product choice, not a statistically validated optimum. It requires a majority of each posting’s tracked skills, removes the permissive one-of-two match allowed by 50%, and retains more near-target opportunities than 70–80%. The control exposes 40–80% for sensitivity checks.', '', 'Rank unselected skills by the number of previously unmet postings that would reach the target. Break ties by summed progress toward the target across previously unmet postings: each improved posting contributes 1 / ceil(skill count × target). Then use employer breadth and skill name. “More move closer” counts only improved postings that still remain below target; it excludes the newly covered group. After adding a skill, recalculate the entire ranking.', '', `Limitations: ${report.oneOrTwoSkills} postings list only one or two tracked skills. Sparse lists are easier to cover; broad terms such as Machine learning are not substitutes for depth. Fixed-vocabulary extraction includes required, preferred, and contextual mentions and can miss skills or list alternatives separately. Equal weighting does not reflect actual employer priorities. Coverage is a learning tool, not eligibility, proficiency, or hiring probability.`, '', '## Reproduce', '', '`node scripts/analyze-skill-thresholds.mjs`', '', `Snapshot SHA-256: \`${report.dataSha256}\`. Full profile/filter/threshold results: [research JSON](https://github.com/zhaotianyu0702/mit-1.125-ps1/blob/main/research/skill-threshold-study.json).`);
writeFileSync(new URL('../research/skill-threshold-study.md',import.meta.url),lines.join('\n')+'\n');
console.log(JSON.stringify({total:report.total,scored:report.total-report.skillLess,oldAnyMatch,default60:rows.find(r=>r.slice==='All'&&r.profile==='Python + ML'&&r.threshold===60)}));
