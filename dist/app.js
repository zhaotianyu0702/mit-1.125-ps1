import { ROLE_FAMILIES, EXPERIENCE_LEVELS, EXPERIENCE_LEVEL_LABELS, unique } from './core.js?v=3.4';
import { selectJobs, distribution, analyzeSkills, skillScenario, jobSkills, SKILL_COVERAGE_TARGET, postingSkillCoverage } from './analytics.js?v=3.4';

const $ = selector => document.querySelector(selector);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = value => Number(value).toLocaleString('en-US');
const pct = (count, total) => total ? Math.round(count / total * 100) : 0;
const defaults = { role: 'all', experience: 'all', region: 'all', evidence: 'all', skill: 'all', q: '' };
const stateNames = {AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'Washington, DC',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'};
const roleShort = {'ML Engineering':'ML engineering','AI Applications':'AI applications','Research':'Research','ML Infrastructure':'ML infrastructure','Applied Data Science':'Data science'};
const levelColors = {entry:'#91b06a',senior:'#397d70',staff:'#648ba7',manager:'#bd936d',unspecified:'#dce2da'};
const storageKey = 'compass-skills-v1';
const state = { jobs: [], meta: {}, coverage: [], filters: {...defaults}, view: 'landscape', skills: [], remember: false, scenario: '', allRegions: false, referencePage: 0 };
let toastTimer;

function readRoute() {
  const hash = location.hash.slice(1);
  state.view = ({guide:'skills',explore:'landscape',insights:'landscape',methodology:'postings',data:'postings',compare:'landscape'})[hash] || (['landscape','skills','postings'].includes(hash) ? hash : 'landscape');
  const params = new URLSearchParams(location.search);
  const role = params.get('role') || params.get('roles');
  const rawExperience = params.get('experienceLevel');
  const experience = ({'new-grad':'entry',mid:'senior',leadership:'manager'})[rawExperience] || rawExperience;
  const region = params.get('region') || params.get('state');
  state.filters = {
    role: ROLE_FAMILIES.includes(role) ? role : 'all',
    experience: EXPERIENCE_LEVELS.includes(experience) ? experience : 'all',
    region: region === 'remote' || region === 'Remote' ? 'remote' : stateNames[region] ? region : 'all',
    evidence: ['graduate','early'].includes(params.get('evidence')) ? params.get('evidence') : 'all',
    skill: params.get('skill') || 'all', q: params.get('q') || ''
  };
}
function writeRoute() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state.filters)) if (value !== 'all' && value !== '') params.set(key === 'experience' ? 'experienceLevel' : key, value);
  history.replaceState(null, '', `${location.pathname}${params.size ? '?' + params : ''}#${state.view}`);
}
function navigate(view) { state.view = view; writeRoute(); render(); window.scrollTo({top:0,behavior:'instant'}); $('#page-heading h1')?.focus({preventScroll:true}); }
function toast(message) { clearTimeout(toastTimer); $('#toast').textContent = message; $('#toast').hidden = false; toastTimer = setTimeout(() => $('#toast').hidden = true, 2300); }
function persistSkills() {
  try { if (state.remember) localStorage.setItem(storageKey, JSON.stringify(state.skills)); else localStorage.removeItem(storageKey); }
  catch { toast('This browser could not save your skills.'); }
}
function selectControl(key, label, options) {
  return `<label>${label}<select data-filter="${key}" aria-label="${label}">${options.map(([value,text]) => `<option value="${escape(value)}" ${state.filters[key] === value ? 'selected' : ''}>${escape(text)}</option>`).join('')}</select></label>`;
}
function renderFilters() {
  const regions = unique(state.jobs.flatMap(j => j.locations.map(l => l.state))).sort((a,b) => stateNames[a]?.localeCompare(stateNames[b]) || 0);
  $('#filters').innerHTML = selectControl('role','Direction',[['all','All directions'],...ROLE_FAMILIES.map(x=>[x,roleShort[x]])])
    + selectControl('experience','Experience level',[['all','All levels'],...EXPERIENCE_LEVELS.map(x=>[x,EXPERIENCE_LEVEL_LABELS[x]])])
    + selectControl('region','Location',[['all','Across the US'],['remote','Remote listings'],...regions.map(x=>[x,stateNames[x] || x])])
    + selectControl('evidence','Graduate evidence',[['all','All postings'],['graduate','Explicit graduate pathways'],['early','Graduate + 0–2 year pathways']])
    + '<div class="filter-tools"><button class="small-button" data-action="reset">Reset</button><button class="small-button" data-action="share" aria-label="Copy this view link">Share ↗</button></div>';
  $('#active-filters').innerHTML = ['skill','q'].filter(key=>state.filters[key] && state.filters[key]!=='all').map(key=>`<button class="filter-tag" data-clear-filter="${key}" aria-label="Remove ${key==='q'?'search':'skill'} filter: ${escape(state.filters[key])}">${key==='q'?'Search':'Skill'}: ${escape(state.filters[key])} <span aria-hidden="true">×</span></button>`).join('');
}
function renderHeading() {
  const headings = { landscape:['Opportunity landscape','See where AI work is concentrated.'], skills:['Explore what to learn next.','Select your skills. Explore what comes next.'], postings:['Job postings','The postings behind the charts.'] };
  const [title,subtitle] = headings[state.view];
  $('#page-heading').innerHTML = `<div><h1 tabindex="-1">${title}</h1><p>${subtitle}</p></div><div class="snapshot">${escape(state.meta.snapshotDate)}</div>`;
  document.querySelectorAll('[data-nav]').forEach(link => {
    if (link.dataset.nav === state.view) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  });
}
function summary(jobs) {
  const stats = [[jobs.length,'Postings'],[unique(jobs.map(j=>j.company)).length,'Companies'],[unique(jobs.flatMap(j=>j.locations.map(l=>l.state))).length,'States & DC'],[jobs.filter(j=>j.newgradStatus==='explicit').length,'Explicit new grad']];
  return `<div class="summary" aria-label="Current sample">${stats.map(([n,label])=>`<div class="stat"><strong>${fmt(n)}</strong><span>${label}</span></div>`).join('')}</div>`;
}
function panel(title, sub, contents, tail = '', unit = 'Postings') {
  return `<section class="panel"><div class="panel-head"><div><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ''}</div><span class="micro">${unit}</span></div>${contents}${tail}</section>`;
}
function bars(rows, dimension) {
  const max = Math.max(1,...rows.map(r=>r.count));
  return `<div class="bar-list">${rows.map(row=>`<button class="chart-row ${dimension === 'region' ? 'region' : ''}" data-drill="${dimension}" data-value="${escape(row.key)}" aria-pressed="${state.filters[dimension] === row.key}" aria-label="Filter ${escape(row.label)}: ${row.count} postings"><span class="bar-label">${escape(row.label)}</span><span class="bar-track" aria-hidden="true"><span class="bar-fill" style="display:block;width:${row.count/max*100}%"></span></span><span class="value">${fmt(row.count)}</span></button>`).join('')}</div>`;
}
function experienceChart(jobs) {
  const rows = distribution(jobs,'experience').sort((a,b)=>EXPERIENCE_LEVELS.indexOf(a.key)-EXPERIENCE_LEVELS.indexOf(b.key));
  const circumference = 2 * Math.PI * 70;
  let offset = 0;
  const arcs = rows.filter(r=>r.count).map(row=> {
    const length = row.count / jobs.length * circumference;
    const arc = `<circle cx="100" cy="100" r="70" fill="none" stroke="${levelColors[row.key]}" stroke-width="21" stroke-dasharray="${length} ${circumference-length}" stroke-dashoffset="${-offset}" transform="rotate(-90 100 100)"/>`;
    offset += length; return arc;
  }).join('');
  return `<div class="level-chart"><svg class="ring" viewBox="0 0 200 200" role="img" aria-label="Experience distribution, ${jobs.length} postings. Counts listed alongside.">${arcs}<text x="100" y="99" text-anchor="middle" class="ring-total">${fmt(jobs.length)}</text><text x="100" y="119" text-anchor="middle" class="ring-sub">POSTINGS</text></svg><div class="legend">${rows.map(row=>`<button data-drill="experience" data-value="${escape(row.key)}" aria-label="Filter ${escape(row.label)}: ${row.count} postings"><i class="dot" style="background:${levelColors[row.key]}"></i><span>${escape(row.label)}</span><b>${fmt(row.count)}</b></button>`).join('')}</div></div><details class="level-key"><summary>How levels are grouped · ${jobs.filter(j=>['requirements','scope'].includes(j.experienceLevelBasis)).length} inferred</summary><p>Entry: graduate / 0–2 years. Senior: experienced IC, including 3+ years or independent ownership. Staff: senior technical scope. Manager: people leadership. Unspecified: insufficient evidence.</p></details>`;
}
function skillMatrix(jobs) {
  const skills = distribution(jobs,'skill').slice(0,7);
  const families = ROLE_FAMILIES.filter(role=>jobs.some(j=>j.roleFamily===role));
  const groups = families.map(role=>({role,jobs:jobs.filter(j=>j.roleFamily===role)}));
  const tables = groups.map(group => new Map(distribution(group.jobs,'skill').map(r=>[r.key,r])));
  const table = `<div class="heat-scroll"><table class="heatmap"><caption class="skip-link">Percent of postings in each direction mentioning a skill</caption><thead><tr><th>Skill</th>${groups.map(g=>`<th>${escape(roleShort[g.role])}<br>n=${g.jobs.length}</th>`).join('')}</tr></thead><tbody>${skills.map(skill=>`<tr><th scope="row"><button data-preview="${escape(skill.label)}" title="Explore ${escape(skill.label)} in Skill lab">${escape(skill.label)}</button></th>${groups.map((g,i)=>{const count=tables[i].get(skill.key)?.count||0;const rate=pct(count,g.jobs.length);return `<td style="background:rgba(36,116,103,${.04+rate/100*.48})"><button data-matrix-role="${escape(g.role)}" data-matrix-skill="${escape(skill.label)}" aria-label="${escape(skill.label)}, ${escape(g.role)}: ${count} of ${g.jobs.length} postings, ${rate} percent">${rate}%</button></td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`;
  return table + '<div class="panel-bottom"><span class="caption">% within each direction</span><span class="heat-legend">Low <i></i> High</span></div>';
}
function renderLandscape(jobs) {
  if (!jobs.length) return emptyView();
  const roleRows = distribution(jobs,'role').filter(r=>r.count).map(r=>({...r,label:roleShort[r.key]}));
  const regions = distribution(jobs,'state').map(r=>({...r,label:stateNames[r.key] || 'Remote'}));
  const topRegions = state.allRegions ? regions : regions.slice(0,7);
  const nonCA = jobs.filter(j=>j.locations.some(l=>l.state && l.state !== 'CA')).length;
  const mainRole = roleRows[0];
  return summary(jobs) + `<div class="dashboard-grid">
    ${panel('Which directions?','',bars(roleRows,'role'),`<p class="caption">${mainRole.label} accounts for ${pct(mainRole.count,jobs.length)}% of this view.</p>`)}
    ${panel('Where is the work?','',bars(topRegions,'region'),`<div class="panel-bottom"><p class="caption">Multi-location postings overlap.</p>${regions.length>7?`<button class="text-button" data-action="regions">${state.allRegions?'Show less':'All locations'} ${state.allRegions?'↑':'↓'}</button>`:''}</div>`)}
    ${panel('What experience level?','',experienceChart(jobs))}
    ${panel('Which skills recur?','',skillMatrix(jobs),'','Share (%)')}
  </div><div class="insight-strip"><p><strong>${fmt(nonCA)} of ${fmt(jobs.length)}</strong> postings list a location outside California. Compare locations before narrowing your search.</p><button class="button" data-view="skills">Explore my skills ↗</button></div>`;
}
function skillChip(skill) {
  const selected = state.skills.includes(skill);
  return `<button class="skill-chip" data-skill="${escape(skill)}" aria-pressed="${selected}" aria-label="${escape(skill)}">${escape(skill)}<span aria-hidden="true">${selected?'✓':'+'}</span></button>`;
}
function skillPicker() {
  const skills = distribution(state.jobs,'skill').map(r=>r.label);
  const main = skills.slice(0,18), more = skills.slice(18);
  const shown = unique([...main,...state.skills]);
  const remaining = more.filter(skill => !state.skills.includes(skill)).sort((a,b)=>a.localeCompare(b));
  return `<section class="panel"><div class="panel-head"><div><h2>What have you used?</h2><p>Coursework, projects or research</p></div><span class="selection-count">${state.skills.length} selected</span></div><div class="skill-chips">${shown.map(skillChip).join('')}</div>${remaining.length?`<label class="other-skill"><span class="skip-link">Add another skill</span><select data-other-skill aria-label="Add another skill"><option value="">Add another skill…</option>${remaining.map(skill=>`<option value="${escape(skill)}">${escape(skill)}</option>`).join('')}</select></label>`:''}<div class="selection-footer"><label class="remember"><input type="checkbox" data-remember ${state.remember?'checked':''}>Remember on this device</label><button class="text-button" data-action="clear-skills">Clear skills</button></div></section>`;
}
function footprint(analysis) {
  return `<section class="panel coverage-panel"><div class="panel-head"><div><h2>Your skill coverage</h2><p>At least ${SKILL_COVERAGE_TARGET}% of each posting’s skills</p></div></div>
    <div class="coverage-stats"><div class="coverage-main"><strong>${analysis.eligibleCount?pct(analysis.coveredCount,analysis.eligibleCount)+'%':'—'}</strong><span>${fmt(analysis.coveredCount)} / ${fmt(analysis.eligibleCount)} postings meet target</span></div><div class="coverage-near"><strong>${fmt(analysis.oneAwayCount)}</strong><span>one skill away</span></div></div>
    <div class="footprint-list">${analysis.byRole.map(r=>`<div class="footprint-row"><span>${escape(roleShort[r.key])}</span><div class="footprint-track" aria-hidden="true"><i style="width:${r.coveredShare}%"></i></div><b title="${r.coveredCount} of ${r.eligibleCount} scored postings meet the ${SKILL_COVERAGE_TARGET}% target">${r.eligibleCount?pct(r.coveredCount,r.eligibleCount)+'%':'—'}</b></div>`).join('')}</div>
    <details class="coverage-definition"><summary>${SKILL_COVERAGE_TARGET}% means ${Math.ceil(5*SKILL_COVERAGE_TARGET/100)} of 5 listed skills${analysis.unscoredCount?` · ${analysis.unscoredCount} unscored`:""} +</summary><p>Required matches = ${SKILL_COVERAGE_TARGET}% × tracked skills, rounded up to a whole skill. ${analysis.unscoredCount?`${fmt(analysis.unscoredCount)} postings without tracked skills excluded. `:''}Mentions include required and preferred skills; this is a learning target, not a qualification score.</p></details></section>`;
}
function projectIdea(skill) {
  const ideas = {
    Python:'Clean a public dataset and publish a reproducible analysis notebook.',
    PyTorch:'Train a small model; compare a baseline and one ablation on held-out data.',
    TensorFlow:'Train and export a small model, then check predictions after deployment.',
    JAX:'Reproduce a small training loop and measure the effect of compilation.',
    SQL:'Answer three business questions from a public dataset using joins and window functions.',
    'C++':'Benchmark a small data-processing or inference routine against a Python baseline.',
    LLMs:'Build a small retrieval demo and evaluate it on questions with known answers.',
    'Machine learning':'Compare a simple baseline with a trained model and inspect the errors.',
    'Deep learning':'Train a small neural model and chart learning curves and failure cases.',
    'Computer vision':'Evaluate an image model across categories and inspect common errors.',
    NLP:'Compare two approaches to classifying a small public text dataset.',
    Docker:'Package a model demo so another person can reproduce it with one command.',
    Kubernetes:'Deploy a small model service and observe how it behaves under load.',
    CUDA:'Profile one GPU operation and document a measured performance improvement.',
    AWS:'Deploy a small prediction service with a budget cap and basic monitoring.',
    GCP:'Deploy a small prediction service with a budget cap and basic monitoring.',
    Spark:'Compare batch processing on a public dataset at two different sizes.',
    Ray:'Run a small parallel experiment and measure its overhead and speedup.',
    'Reinforcement learning':'Train a simple agent and compare reward curves across random seeds.'
  };
  return ideas[skill] || `Build a small ${skill} project with a baseline, a reproducible run, and one measurable result.`;
}
function recommendations(analysis) {
  const rows = analysis.recommendations;
  if (!rows.length) return `<div class="scenario-placeholder">${analysis.eligibleCount?'Every scored posting meets the target. Explore another direction.':'No tracked skills in this view. Try another direction.'}</div>`;
  return `<div class="section-title"><h2>${state.skills.length?'What could you learn next?':'Skills to start with'}</h2><p>Added coverage at the ${SKILL_COVERAGE_TARGET}% target</p></div><div class="recommendations">${rows.map((r,i)=>`<article class="recommendation ${state.scenario===r.skill?'previewing':''}"><div class="rec-title"><span class="rank">0${i+1}</span><h3>${escape(r.skill)}</h3></div><div class="rec-number">+${fmt(r.gain)}<small>postings reach target</small></div><p class="rec-progress">${fmt(r.closerCount)} more move closer</p><p class="rec-detail"><button class="text-button" data-reference-skill="${escape(r.skill)}">Mentioned in ${fmt(r.count)} postings ↗</button></p><button class="small-button" data-preview="${escape(r.skill)}">Try adding ${escape(r.skill)} ↗</button><details class="practice"><summary>One practice project +</summary><p>${escape(projectIdea(r.skill))}</p></details></article>`).join('')}</div>`;
}
function scenarioPanel(jobs) {
  if (!state.scenario || state.skills.includes(state.scenario)) return '<div class="scenario-placeholder">Try a suggested skill to preview the change.</div>';
  const result = skillScenario(jobs,state.skills,state.scenario,SKILL_COVERAGE_TARGET);
  return `<section class="scenario" aria-label="Skill scenario"><div class="scenario-copy"><h2>What if I add ${escape(state.scenario)}?</h2><p class="caption">Postings reaching the ${SKILL_COVERAGE_TARGET}% target</p></div><div class="scenario-bars">${[['before','Now',result.before],['after','With it',result.after]].map(([cls,label,count])=>`<div class="scenario-row ${cls}"><span>${label}</span><div class="track"><i style="width:${pct(count,result.total)}%"></i></div><b>${fmt(count)}</b></div>`).join('')}</div><div class="scenario-gain">+${fmt(result.gain)}<small>reach target</small><span class="scenario-closer">${fmt(result.closerCount)} more move closer</span></div><button class="button" data-action="apply-skill">Add to my skills</button></section>`;
}
function renderSkills(jobs) {
  const analysis = analyzeSkills(jobs,state.skills,SKILL_COVERAGE_TARGET);
  return `<div class="skill-grid">${skillPicker()}${footprint(analysis)}</div>${jobs.length ? recommendations(analysis)+scenarioPanel(jobs) : `<div style="margin-top:18px">${emptyView()}</div>`}`;
}
function download(url,title,type) { return `<a class="download-link" href="${url}"><span>${title} ↗</span><span class="file-type">${type}</span></a>`; }
function safeUrl(value) { try { const u = new URL(value); return u.protocol === 'https:' ? escape(u.href) : '#'; } catch { return '#'; } }
function referenceRow(job) {
  const inferred=['requirements','scope'].includes(job.experienceLevelBasis);
  const skills=jobSkills(job);
  const coverage=postingSkillCoverage(job,state.skills,SKILL_COVERAGE_TARGET);
  const locations=unique(job.locations.map(l=>[l.city==='US location not specified'?'':l.city,l.state].filter(Boolean).join(', ')));
  if(job.remote)locations.unshift('Remote');
  const source=job.experienceEvidenceSource;
  return `<tr>
    <td class="posting-title"><strong>${escape(job.title)}</strong><span>${escape(job.company)}</span><span class="posting-direction">${escape(roleShort[job.roleFamily]||job.roleFamily)}</span></td>
    <td class="posting-level"><details><summary class="level-badge level-${escape(job.experienceLevel)}">${escape(EXPERIENCE_LEVEL_LABELS[job.experienceLevel]||'Unspecified')}<span>${inferred?'inferred':'↘'}</span></summary><div class="level-evidence"><p>${escape(job.experienceLevelEvidence)}</p>${source?.excerpt?`<blockquote>${escape(source.excerpt)}</blockquote>`:''}</div></details></td>
    <td>${state.skills.length && coverage.scorable?`<div class="posting-coverage ${coverage.covered?'target-met':''}"><span>${coverage.matched}/${coverage.total} skills selected</span><b>${coverage.covered?'Target met':`${coverage.required-coverage.matched} more to ${SKILL_COVERAGE_TARGET}%`}</b></div>`:''}<div class="reference-skills">${skills.length?skills.map(skill=>`<button data-reference-skill="${escape(skill)}" class="reference-skill ${state.skills.includes(skill)?'known-skill':''}" aria-label="Show postings mentioning ${escape(skill)}">${escape(skill)}</button>`).join(''):'<span class="reference-muted">No tracked mentions</span>'}</div></td>
    <td class="posting-location">${escape(locations.join(' · ')||'US — not specified')}</td>
    <td class="posting-source"><a href="${safeUrl(job.url)}" target="_blank" rel="noopener" aria-label="Source for ${escape(job.title)} at ${escape(job.company)}">Source ↗</a><span>${escape(job.verifiedAt?.slice(0,10))}</span></td>
  </tr>`;
}
function renderPostings(jobs) {
  const pageSize=25, pages=Math.max(1,Math.ceil(jobs.length/pageSize));
  state.referencePage=Math.max(0,Math.min(state.referencePage,pages-1));
  const start=state.referencePage*pageSize;
  const sorted=[...jobs].sort((a,b)=>a.company.localeCompare(b.company)||a.title.localeCompare(b.title));
  const skills=distribution(state.jobs,'skill');
  return `<div class="reference-toolbar"><form id="reference-search" role="search"><label class="skip-link" for="posting-search">Search postings</label><input id="posting-search" name="q" type="search" value="${escape(state.filters.q)}" placeholder="Company, title or skill" autocomplete="off"><button class="small-button" type="submit">Search</button></form><label class="reference-skill-select"><span class="skip-link">Filter by skill mention</span><select data-reference-filter="skill" aria-label="Filter by skill mention"><option value="all">All skill mentions</option>${skills.map(skill=>`<option value="${escape(skill.label)}" ${state.filters.skill.toLowerCase()===skill.label.toLowerCase()?'selected':''}>${escape(skill.label)}</option>`).join('')}</select></label></div>
  <div class="reference-heading"><p><strong>${fmt(jobs.length)}</strong> of ${fmt(state.jobs.length)} postings</p><button class="text-button" data-view="landscape">View this slice in charts ↗</button></div>
  ${jobs.length?`<div class="reference-table-wrap"><table class="reference-table"><caption class="skip-link">Job postings for the selected chart filters</caption><thead><tr><th scope="col">Role / company</th><th scope="col">Experience</th><th scope="col">Skill mentions</th><th scope="col">Location</th><th scope="col">Source / checked</th></tr></thead><tbody>${sorted.slice(start,start+pageSize).map(referenceRow).join('')}</tbody></table></div><div class="reference-pagination"><span>${fmt(start+1)}–${fmt(Math.min(start+pageSize,jobs.length))} of ${fmt(jobs.length)}</span><div><button class="small-button" data-reference-page="${state.referencePage-1}" ${state.referencePage===0?'disabled':''}>← Previous</button><span>Page ${state.referencePage+1} / ${pages}</span><button class="small-button" data-reference-page="${state.referencePage+1}" ${state.referencePage===pages-1?'disabled':''}>Next →</button></div></div>`:emptyView()}`;
}
function renderProjectFiles() {
  $('#project-files').innerHTML=`<summary>Project files +</summary><div class="download-links">${download('./submission.html','Submission materials','PAGE')}${download('https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site/downloads/ai-career-compass-ps1.zip','Complete submission pack','ZIP')}${download('./downloads/jobs.csv','Posting dataset','CSV')}${download(safeUrl(state.meta.githubUrl),'Source code','GITHUB')}</div>`;
}
function emptyView() { return '<div class="empty"><h2>No postings in this slice.</h2><p>Try another level, location or evidence group.</p><button class="button" data-action="reset">Reset filters</button></div>'; }
function render(focusKey) {
  renderHeading(); renderFilters();
  const jobs=selectJobs(state.jobs,state.filters);
  $('#content').innerHTML = state.view==='postings' ? renderPostings(jobs) : state.view==='skills' ? renderSkills(jobs) : renderLandscape(jobs);
  $('#content').setAttribute('aria-busy','false');
  renderProjectFiles();
  if (focusKey) document.querySelector(focusKey)?.focus({preventScroll:true});
  writeRoute();
}

$('#filters').addEventListener('change',event=>{
  const key=event.target.dataset.filter;
  if (!(key in defaults)) return;
  state.filters[key]=event.target.value;
  state.allRegions=false;state.referencePage=0;
  render(`[data-filter="${key}"]`);
});
document.addEventListener('change',event=>{
  if(event.target.dataset.referenceFilter==='skill'){state.filters.skill=event.target.value;state.referencePage=0;render('[data-reference-filter="skill"]');return;}
  if(event.target.hasAttribute('data-other-skill') && event.target.value) { state.skills=unique([...state.skills,event.target.value]);persistSkills();render();return; }
  if(event.target.hasAttribute('data-remember')) { state.remember=event.target.checked; persistSkills(); }
});
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');
  if(!button)return;
  if(button.dataset.clearFilter){const key=button.dataset.clearFilter;state.filters[key]=defaults[key];state.referencePage=0;render();return;}
  if(button.dataset.referenceSkill){state.filters.skill=button.dataset.referenceSkill;state.referencePage=0;navigate('postings');return;}
  if(button.dataset.referencePage!==undefined){state.referencePage=Number(button.dataset.referencePage);render();$('.reference-heading')?.scrollIntoView({block:'start'});$('.reference-pagination button:not(:disabled)')?.focus({preventScroll:true});return;}
  if(button.dataset.view){navigate(button.dataset.view);return;}
  if(button.dataset.skill){
    const skill=button.dataset.skill;
    state.skills=state.skills.includes(skill)?state.skills.filter(x=>x!==skill):[...state.skills,skill];
    if(state.scenario===skill)state.scenario='';
    persistSkills();
    render();
    [...document.querySelectorAll('[data-skill]')].find(el=>el.dataset.skill===skill)?.focus({preventScroll:true});
    return;
  }
  if(button.dataset.drill){
    const key=button.dataset.drill;
    state.filters[key]=state.filters[key]===button.dataset.value?'all':button.dataset.value;
    state.allRegions=false;state.referencePage=0;render();return;
  }
  if(button.dataset.matrixRole){state.filters.role=button.dataset.matrixRole;state.scenario=button.dataset.matrixSkill;navigate('skills');return;}
  if(button.dataset.preview){state.scenario=button.dataset.preview;if(state.view!=='skills')navigate('skills');else render();$('.scenario')?.scrollIntoView({behavior:'smooth',block:'nearest'});return;}
  switch(button.dataset.action){
    case 'reset': state.filters={...defaults};state.allRegions=false;state.referencePage=0;render();break;
    case 'regions': state.allRegions=!state.allRegions;render();break;
    case 'clear-skills': state.skills=[];state.scenario='';state.remember=false;persistSkills();render();break;
    case 'apply-skill': if(state.scenario){state.skills=unique([...state.skills,state.scenario]);state.scenario='';persistSkills();render();}break;
    case 'share': try {await navigator.clipboard.writeText(location.href);toast('Chart view copied. Your skills stay private.');}catch{toast('Copy the page address to share this view.');}break;
  }
});
document.addEventListener('submit',event=>{if(event.target.id!=='reference-search')return;event.preventDefault();state.filters.q=new FormData(event.target).get('q').trim();state.referencePage=0;render('#posting-search');});
window.addEventListener('hashchange',()=>{if(location.hash==='#main'){$('#main').focus();return;}readRoute();render();});
window.addEventListener('popstate',()=>{readRoute();render();});

async function init(){
  readRoute();
  try{
    const response=await fetch('./data.json', {cache:'no-cache'});
    if(!response.ok)throw Error('Snapshot unavailable');
    const data=await response.json();state.jobs=data.jobs;state.meta=data.meta;state.coverage=data.coverage;
    const catalog=distribution(state.jobs,'skill').map(r=>r.label);
    try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(Array.isArray(saved)){state.skills=unique(saved.filter(x=>catalog.includes(x)));state.remember=true;}}catch{}
    render();
  }catch{
    $('#content').setAttribute('aria-busy','false');
    $('#content').innerHTML='<div class="empty"><h1>The data could not load.</h1><p>Refresh to try again, or download the snapshot.</p><a class="button" href="./downloads/jobs.csv">Download data</a></div>';
  }
}
init();
