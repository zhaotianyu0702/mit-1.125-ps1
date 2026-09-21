import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {analyzeSkills,jobSkills,selectJobs,distribution,SKILL_COVERAGE_TARGET} from '../dist/analytics.js';

const thresholds=[40,50,60,65,70,75,80];
const raw=readFileSync(new URL('../dist/data.json',import.meta.url));
const data=JSON.parse(raw);
const roleProfiles={
  'ML Engineering':['Python','Machine learning','PyTorch','Deep learning','C++','Kubernetes','Docker'],
  'AI Applications':['Python','LLMs','RAG','AWS','GCP','Kubernetes','NLP'],
  Research:['Python','Machine learning','PyTorch','Reinforcement learning','Deep learning','JAX','CUDA'],
  'ML Infrastructure':['Python','Machine learning','LLMs','Kubernetes','C++','CUDA','Docker'],
  'Applied Data Science':['Python','SQL','Machine learning','Spark','LLMs','scikit-learn']
};
const profiles={
  'No skills':[],
  'Python + ML':['Python','Machine learning'],
  'Python + ML + SQL':['Python','Machine learning','SQL'],
  ...roleProfiles,
  'Visible 18':distribution(data.jobs,'skill').slice(0,18).map(row=>row.label),
  'Full catalog':[...new Set(data.jobs.flatMap(jobSkills))]
};
const slices={All:data.jobs,Entry:selectJobs(data.jobs,{experience:'entry'}),...Object.fromEntries(Object.keys(roleProfiles).map(role=>[role,selectJobs(data.jobs,{role})]))};
const rows=[];
for(const [slice,jobs] of Object.entries(slices))for(const [profile,skills] of Object.entries(profiles))for(const threshold of thresholds){
 const a=analyzeSkills(jobs,skills,threshold);
 rows.push({slice,profile,threshold,total:a.total,scored:a.eligibleCount,covered:a.coveredCount,share:a.coveredShare,oneAway:a.oneAwayCount,recommendations:a.recommendations.map(({skill,gain,closerCount})=>({skill,gain,closerCount}))});
}
const learningPaths=[];
for(const [role,initial] of Object.entries(roleProfiles))for(const threshold of [60,70,75,80]){
 const skills=[...initial],jobs=slices[role],steps=[];
 for(let step=0;step<4;step++){
  const a=analyzeSkills(jobs,skills,threshold),next=a.recommendations[0];
  steps.push({step,covered:a.coveredCount,scored:a.eligibleCount,share:a.coveredShare,next:next?{skill:next.skill,gain:next.gain,closerCount:next.closerCount}:null});
  if(!next)break;
  skills.push(next.skill);
 }
 learningPaths.push({role,threshold,steps});
}
const skillsCounts=data.jobs.map(job=>jobSkills(job).length);
const oldAnyMatch=data.jobs.filter(job=>jobSkills(job).some(skill=>profiles['Python + ML'].includes(skill))).length;
const macro=threshold=>Object.keys(roleProfiles).reduce((sum,role)=>{const r=rows.find(r=>r.slice===role&&r.profile===role&&r.threshold===threshold);return sum+100*r.covered/r.scored;},0)/5;
const report={snapshot:data.meta.snapshotDate,dataSha256:createHash('sha256').update(raw).digest('hex'),formula:'matched >= ceil(unique tracked skills * threshold / 100)',selectedTarget:SKILL_COVERAGE_TARGET,thresholds,total:data.jobs.length,skillLess:skillsCounts.filter(n=>!n).length,oneOrTwoSkills:skillsCounts.filter(n=>n>0&&n<=2).length,oldAnyMatch,profiles,roleBalancedCoverage:Object.fromEntries(thresholds.map(t=>[t,Number(macro(t).toFixed(1))])),learningPaths,rows};
writeFileSync(new URL('../research/skill-threshold-study.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
const lines=['# Fixed skill target study','',`Snapshot: ${report.snapshot}. ${report.total} postings; ${report.total-report.skillLess} have tracked skills. Fixed site target: **${SKILL_COVERAGE_TARGET}%**.`, '', '## Evaluation design', '', 'Compare 40, 50, 60, 65, 70, 75 and 80 percent using the same canonical skill extraction. Focus the decision on 70–80%: the product should reward building a broader skill set while leaving useful, successive learning steps. Higher coverage alone is not the objective.', '', 'Five synthetic profiles cover engineering, applications, research, infrastructure and data science. Each contains 6–7 skills from the actual catalog. They are illustrative probes, not surveyed students or validated career standards. Evaluate each profile within its own direction, average directions equally, then greedily add three recommended skills. Also test a two-skill baseline, the 18 visible skill chips and the full catalog.', '', '## Profile definitions', '', ...Object.entries(roleProfiles).map(([role,skills])=>`- **${role}:** ${skills.join(', ')}.`), '', '## Two-skill baseline', '', `The previous any-skill rule counted ${oldAnyMatch}/${report.total} postings (${(100*oldAnyMatch/report.total).toFixed(1)}%). The current denominator excludes ${report.skillLess} postings without tracked skills.`, '', '| Target | Python + ML coverage | Share | Best single addition | Newly reaching target |', '| --- | ---: | ---: | --- | ---: |'];
for(const row of rows.filter(r=>r.slice==='All'&&r.profile==='Python + ML')){const best=row.recommendations[0];lines.push(`| ${row.threshold}% | ${row.covered}/${row.scored} | ${row.share}% | ${best.skill} | +${best.gain} |`);}
lines.push('', '## Each profile in its own direction', '', '| Direction | Scored postings | 60% | 70% | 75% | 80% |','| --- | ---: | ---: | ---: | ---: | ---: |');
for(const role of Object.keys(roleProfiles)){const group=[60,70,75,80].map(t=>rows.find(r=>r.slice===role&&r.profile===role&&r.threshold===t));lines.push(`| ${role} | ${group[0].scored} | ${group.map(r=>`${r.covered} (${r.share}%)`).join(' | ')} |`);}
lines.push(`| Equal-weight mean of direction percentages | — | ${[60,70,75,80].map(t=>`${report.roleBalancedCoverage[t]}%`).join(' | ')} |`, '', '## Successive learning steps', '', 'Each row starts from the role profile above. Values are cumulative covered postings after each addition. Rankings are recalculated after every step; these hypothetical paths do not measure learning effort or outcomes.', '', '| Direction | Target | Initial | +1 skill | +2 skills | +3 skills | Skills added in order |', '| --- | ---: | ---: | ---: | ---: | ---: | --- |');
for(const path of learningPaths)lines.push(`| ${path.role} | ${path.threshold}% | ${path.steps.map(s=>s.covered).join(' | ')} | ${path.steps.slice(0,3).map(s=>s.next?.skill||'—').join(' → ')} |`);
lines.push('', '## Saturation checks', '', '| Selection | 60% | 70% | 75% | 80% |', '| --- | ---: | ---: | ---: | ---: |');
for(const profile of ['Visible 18','Full catalog'])lines.push(`| ${profile} | ${[60,70,75,80].map(t=>{const r=rows.find(r=>r.slice==='All'&&r.profile===profile&&r.threshold===t);return `${r.covered}/${r.scored} (${r.share}%)`;}).join(' | ')} |`);
lines.push('', '## Rounding matters', '', '| Tracked skills in posting | 60% required | 70% required | 75% required | 80% required |','| --- | ---: | ---: | ---: | ---: |');
for(let n=1;n<=10;n++)lines.push(`| ${n} | ${[60,70,75,80].map(t=>Math.ceil(n*t/100)).join(' | ')} |`);
lines.push('', '## Fixed choice: 70%', '', 'Use 70% across the site, with no target selector or URL override. This is a product heuristic: ask for substantially broader coverage than 60% while preserving useful successive learning steps. In these probes the equal-weight mean across five directions falls from 61.0% to 45.8%. For the ML Engineering profile, three recommended additions move coverage from 70 to 120 to 162 to 196 of 329 postings; the same profile at 60% starts at 125 and reaches 261. The stronger target leaves more headroom for subsequent learning.', '', '75% starts at the same coverage as 70% in three of five directions and an overall mean of 44.9%. It produces little additional separation at the starting profiles. 80% lowers the mean to 39.6% and, because of rounding, requires all four skills on a four-skill posting rather than three. With required, preferred and alternative mentions mixed in this dataset, that all-or-nothing step is a reason to prefer 70%. All five directions still have positive gains on each of the three tested additions. This evidence supports a transparent design choice; it does not prove 70% is optimal for every skill profile.', '', '## Recommendation rule', '', 'Rank unselected skills by previously unmet postings that would cross the fixed target. Break ties by summed progress across unmet postings: each improved posting contributes 1 / ceil(skill count × target). Then use employer breadth and skill name. “More move closer” includes only improved postings still below target, excluding newly covered postings. Already covered postings add no benefit.', '', '## Limitations', '', `${report.oneOrTwoSkills}/${report.total-report.skillLess} scored postings (${(report.oneOrTwoSkills/(report.total-report.skillLess)*100).toFixed(1)}%) list only one or two tracked skills; all tested targets above 50% require every one of those skills. Sparse lists can inflate coverage. The ${report.skillLess} skill-less postings are unscored, not part of that sparse-list count. Fixed-vocabulary extraction includes required, preferred, contextual and alternative mentions and misses some skills. Equal weighting ignores employer priorities and proficiency. Synthetic profiles are sensitive to their composition; there is no ground-truth outcome data or statistically validated optimal target. This is a learning visualization, not a hiring or eligibility model.`, '', '## Reproduce', '', '`node scripts/analyze-skill-thresholds.mjs`', '', `Snapshot SHA-256: \`${report.dataSha256}\`. Full profile/filter/threshold results: [research JSON](https://github.com/zhaotianyu0702/mit-1.125-ps1/blob/main/research/skill-threshold-study.json).`);
writeFileSync(new URL('../research/skill-threshold-study.md',import.meta.url),lines.join('\n')+'\n');
console.log(JSON.stringify({total:report.total,scored:report.total-report.skillLess,selectedTarget:report.selectedTarget,roleBalancedCoverage:report.roleBalancedCoverage,learningPaths}));
