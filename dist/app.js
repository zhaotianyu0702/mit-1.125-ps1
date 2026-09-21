import { ROLE_FAMILIES, EXPERIENCE_LEVELS, EXPERIENCE_LEVEL_LABELS, unique } from './core.js?v=3.1';
import { selectJobs, distribution, analyzeSkills, skillScenario } from './analytics.js?v=3.1';

const $ = selector => document.querySelector(selector);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = value => Number(value).toLocaleString('en-US');
const pct = (count, total) => total ? Math.round(count / total * 100) : 0;
const defaults = { role: 'all', experience: 'all', region: 'all', evidence: 'all' };
const stateNames = {AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'Washington, DC',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming'};
const roleShort = {'ML Engineering':'ML engineering','AI Applications':'AI applications','Research':'Research','ML Infrastructure':'ML infrastructure','Applied Data Science':'Data science'};
const levelColors = {'new-grad':'#739743',entry:'#bdcf8f',mid:'#b49266',senior:'#397d70',staff:'#648ba7',leadership:'#bd936d',experienced:'#8aa99a','open-level':'#a49fc3',unspecified:'#dce2da'};
const storageKey = 'compass-skills-v1';
const guideKey = 'compass-guide-seen-v1';
const state = { jobs: [], meta: {}, coverage: [], filters: {...defaults}, view: 'landscape', skills: [], remember: false, scenario: '', guideActive: true, guideStep: 0, allRegions: false };
let toastTimer;

function readRoute() {
  const hash = location.hash.slice(1);
  state.view = ({guide:'skills',explore:'landscape',insights:'landscape',methodology:'data',compare:'landscape'})[hash] || (['landscape','skills','data'].includes(hash) ? hash : 'landscape');
  const params = new URLSearchParams(location.search);
  const role = params.get('role') || params.get('roles');
  const experience = params.get('experienceLevel');
  const region = params.get('region') || params.get('state');
  state.filters = {
    role: ROLE_FAMILIES.includes(role) ? role : 'all',
    experience: EXPERIENCE_LEVELS.includes(experience) ? experience : 'all',
    region: region === 'remote' || region === 'Remote' ? 'remote' : stateNames[region] ? region : 'all',
    evidence: ['graduate','early'].includes(params.get('evidence')) ? params.get('evidence') : 'all'
  };
}
function writeRoute() {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state.filters)) if (value !== 'all') params.set(key === 'experience' ? 'experienceLevel' : key, value);
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
  $('#filters').hidden = state.view === 'data';
  if (state.view === 'data') return;
  const regions = unique(state.jobs.flatMap(j => j.locations.map(l => l.state))).sort((a,b) => stateNames[a]?.localeCompare(stateNames[b]) || 0);
  $('#filters').innerHTML = selectControl('role','Direction',[['all','All directions'],...ROLE_FAMILIES.map(x=>[x,roleShort[x]])])
    + selectControl('experience','Experience level',[['all','All levels'],...EXPERIENCE_LEVELS.map(x=>[x,EXPERIENCE_LEVEL_LABELS[x]])])
    + selectControl('region','Location',[['all','Across the US'],['remote','Remote listings'],...regions.map(x=>[x,stateNames[x] || x])])
    + selectControl('evidence','Graduate evidence',[['all','All postings'],['graduate','Explicit graduate pathways'],['early','Graduate + 0–2 year pathways']])
    + '<div class="filter-tools"><button class="small-button" data-action="reset">Reset</button><button class="small-button" data-action="share" aria-label="Copy this chart view link">Share ↗</button></div>';
}
function renderHeading() {
  const headings = { landscape:['OPPORTUNITIES / 01','Opportunity landscape','See where AI work is concentrated.'], skills:['YOUR SKILLS / 02','Explore what to learn next.','Select your skills. Explore what comes next.'], data:['BEHIND THE CHARTS','Data & method','The sample, its limits, and the project files.'] };
  const [eyebrow,title,subtitle] = headings[state.view];
  $('#page-heading').innerHTML = `<div><h1 tabindex="-1">${title}</h1><p>${subtitle}</p></div><div class="snapshot">${escape(state.meta.snapshotDate)}${state.view!=='data'?'<button class="text-button guide-launch" data-action="start-guide">Guide me ↗</button>':''}</div>`;
  document.querySelectorAll('[data-nav]').forEach(link => {
    if (link.dataset.nav === state.view) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  });
}
function renderGuide() {
  const panel=$('#guide');
  panel.hidden=!state.guideActive || state.view==='data';
  document.querySelectorAll('.guide-focus').forEach(el=>el.classList.remove('guide-focus'));
  if(panel.hidden)return;
  if(state.view==='landscape')state.guideStep=0;
  else if(state.guideStep===0)state.guideStep=1;
  const steps=['Explore the market','Select your skills','Try one more'];
  const instructions=[
    'Click a chart to focus on a direction, level or location.',
    state.skills.length?`${state.skills.length} skills selected. Watch the coverage chart change.`:'Select skills you have used in coursework or projects.',
    'Try a suggested skill and compare how many more postings mention it.'
  ];
  const next=['Choose my skills →',state.skills.length?'Try a suggestion →':'Find a starting skill →','Finish ✓'];
  panel.innerHTML=`<div class="guide-top"><nav aria-label="Guide steps">${steps.map((label,i)=>`<button data-guide-step="${i}" ${i===state.guideStep?'aria-current="step"':''}><span>${i+1}</span>${label}</button>`).join('')}</nav><button class="text-button guide-skip" data-action="skip-guide">Skip</button></div><div class="guide-bottom"><p>${instructions[state.guideStep]}</p><div>${state.guideStep?'<button class="text-button" data-action="guide-back">← Back</button>':''}<button class="button primary" data-action="guide-next">${next[state.guideStep]}</button></div></div>`;
  const target=state.guideStep===0?'.dashboard-grid .panel':state.guideStep===1?'.skill-grid .panel':'.recommendations';
  document.querySelector(target)?.classList.add('guide-focus');
}
function guideTo(step) {
  state.guideActive=true;state.guideStep=Math.max(0,Math.min(2,step));
  state.view=step===0?'landscape':'skills';
  if(step===2&&!state.scenario)state.scenario=analyzeSkills(selectJobs(state.jobs,state.filters),state.skills).recommendations[0]?.skill||'';
  writeRoute();render();
  if(step===2)document.querySelector('.recommendations')?.scrollIntoView({behavior:'smooth',block:'center'});
  else window.scrollTo({top:0,behavior:'instant'});
  $('#guide [data-action="guide-next"]')?.focus({preventScroll:true});
}
function finishGuide() {
  state.guideActive=false;try{localStorage.setItem(guideKey,'true');}catch{}render();
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
  return `<div class="level-chart"><svg class="ring" viewBox="0 0 200 200" role="img" aria-label="Experience distribution, ${jobs.length} postings. Counts listed alongside.">${arcs}<text x="100" y="99" text-anchor="middle" class="ring-total">${fmt(jobs.length)}</text><text x="100" y="119" text-anchor="middle" class="ring-sub">POSTINGS</text></svg><div class="legend">${rows.map(row=>`<button data-drill="experience" data-value="${escape(row.key)}" aria-label="Filter ${escape(row.label)}: ${row.count} postings"><i class="dot" style="background:${levelColors[row.key]}"></i><span>${escape(row.label)}</span><b>${fmt(row.count)}</b></button>`).join('')}</div></div><p class="caption">Titles + source requirements · ${jobs.filter(j=>['requirements','scope'].includes(j.experienceLevelBasis)).length} inferred</p>`;
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
  return `<section class="panel"><div class="panel-head"><div><h2>Your skill footprint</h2><p>Postings mentioning at least one selected skill</p></div></div><div class="footprint-top"><strong>${state.skills.length?pct(analysis.withKnownSkillCount,analysis.total)+'%':'—'}</strong><span>${state.skills.length?`${fmt(analysis.withKnownSkillCount)} / ${fmt(analysis.total)} postings`:'Select a few skills to begin'}</span></div><div class="footprint-list">${analysis.byRole.map(r=>`<div class="footprint-row"><span>${escape(roleShort[r.key])}</span><div class="footprint-track" aria-hidden="true"><i style="width:${r.withKnownSkillShare}%"></i></div><b title="${r.withKnownSkillCount} of ${r.count} postings">${r.count?pct(r.withKnownSkillCount,r.count)+'%':'—'}</b></div>`).join('')}</div><p class="caption">Skill mentions, not a qualification score.</p></section>`;
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
  if (!rows.length) return '<div class="scenario-placeholder">No unselected skill mentions remain in this view. Try another direction.</div>';
  return `<div class="section-title"><h2>${state.skills.length?'What could you learn next?':'Common skills to start with'}</h2><p>Unselected skills, ranked by mentions in this view</p></div><div class="recommendations">${rows.map((r,i)=>`<article class="recommendation ${state.scenario===r.skill?'previewing':''}"><div class="rec-title"><span class="rank">0${i+1}</span><h3>${escape(r.skill)}</h3></div><div class="rec-number">${Math.round(r.share)}%<small>of this view</small></div><p class="rec-detail">${fmt(r.count)} postings · ${r.companies} companies</p><button class="small-button" data-preview="${escape(r.skill)}">Try adding ${escape(r.skill)} ↗</button><details class="practice"><summary>One practice project +</summary><p>${escape(projectIdea(r.skill))}</p></details></article>`).join('')}</div>`;
}
function scenarioPanel(jobs) {
  if (!state.scenario || state.skills.includes(state.scenario)) return '<div class="scenario-placeholder">Try a suggested skill to preview the change.</div>';
  const result = skillScenario(jobs,state.skills,state.scenario);
  return `<section class="scenario" aria-label="Skill scenario"><div class="scenario-copy"><h2>What if I add ${escape(state.scenario)}?</h2></div><div class="scenario-bars">${[['before','Now',result.before],['after','With it',result.after]].map(([cls,label,count])=>`<div class="scenario-row ${cls}"><span>${label}</span><div class="track"><i style="width:${pct(count,result.total)}%"></i></div><b>${fmt(count)}</b></div>`).join('')}</div><div class="scenario-gain">+${fmt(result.gain)}<small>additional postings</small></div><button class="button" data-action="apply-skill">Add to my skills</button></section>`;
}
function renderSkills(jobs) {
  const analysis = analyzeSkills(jobs,state.skills);
  return `<div class="skill-grid">${skillPicker()}${footprint(analysis)}</div>${jobs.length ? recommendations(analysis)+scenarioPanel(jobs) : `<div style="margin-top:18px">${emptyView()}</div>`}`;
}
function download(url,title,type) { return `<a class="download-link" href="${url}"><span>${title} ↗</span><span class="file-type">${type}</span></a>`; }
function safeUrl(value) { try { const u = new URL(value); return u.protocol === 'https:' ? escape(u.href) : '#'; } catch { return '#'; } }
function renderData() {
  const jobs=state.jobs, curated=jobs.filter(j=>j.reviewLevel!=='automated-discovery').length;
  return summary(jobs)+`<div class="data-grid"><section class="panel"><h2>How to read the charts</h2>
    <details class="method-row" open><summary>Sample & collection</summary><p>${fmt(jobs.length)} deduplicated US AI postings from ${unique(jobs.map(j=>j.company)).length} companies. Official career pages and public <a href="https://docs.greenhouse.io/job-board.html" target="_blank" rel="noopener">Greenhouse</a>, <a href="https://developers.ashbyhq.com/docs/public-job-posting-api" target="_blank" rel="noopener">Ashby</a> and <a href="https://github.com/lever/postings-api" target="_blank" rel="noopener">Lever</a> sources. ${curated} curated records; ${jobs.length-curated} automated discovery records. Collected on the dates in the downloadable data.</p></details>
    <details class="method-row"><summary>Definitions & recommendation logic</summary><p>One posting is one observation, not one vacancy or hire. Role and experience counts sum to the selected total. States and skills overlap. Heatmap percentages use postings within each direction as the denominator. A skill counts once per posting, including required, preferred and contextual mentions.</p><p>Your skill footprint counts postings mentioning at least one selected skill. Suggestions rank unselected skills by posting mentions, then company breadth. The scenario adds one skill and recounts. Practice projects are learning suggestions. Experience labels prioritize explicit titles. When titles give no level, clear requirements map 0–2 years to entry, 3–4 to mid, and 5+ to senior. These are inferred exploration buckets. Experience requested means relevant experience is stated without a clear numeric level; Level varies means the employer states multiple or level-dependent requirements. Preferred-only or ambiguous numbers remain unclassified. Graduate eligibility is separate.</p></details>
    <details class="method-row"><summary>Missing data & limits</summary><p>This is a purposive ATS sample, not the whole US market. Employer selection, inaccessible boards and uneven disclosure shape the charts. The older personal search was Bay Area / LLM focused and used only for discovery. Automated skill extraction uses a fixed vocabulary, so tracked terms are overrepresented. Missing or unparsed fields remain unknown; a missing skill mention is not proof a skill is unnecessary. Experience titles vary by company. Postings can close after collection. Skill counts support exploration, not hiring odds or causal salary claims.</p></details>
    <details class="method-row"><summary>Privacy & AI assistance</summary><p>No name, résumé, contact details or personal location is collected. Skill choices stay in page memory, or in your browser if you enable Remember on this device. They are not sent to a server or included in shared links. Clear skills removes that saved set. AI agents assisted collection and coding; automated discovery records were not individually verified.</p></details>
  </section><section class="panel"><h2>Data & project files</h2><div class="download-links">
    ${download('./downloads/jobs.csv','Posting dataset','CSV')}
    ${download('./downloads/methodology.pdf','One-page methodology','PDF')}
    ${download('./downloads/reflection.pdf','Reflection','PDF')}
    ${download('./presentation.html','Five-minute presentation','SLIDES')}
    ${download('./downloads/demo-script.md','Demo notes','MD')}
    ${download('./downloads/data-dictionary.md','Data dictionary','MD')}
    ${download(safeUrl(state.meta.githubUrl),'Source code on GitHub','CODE')}
  </div><details class="method-row"><summary>Additional data tables</summary><div class="download-links">${download('./downloads/job_skills.csv','Skill mentions','CSV')}${download('./downloads/job_locations.csv','Locations','CSV')}${download('./downloads/qualification_paths.csv','Qualification pathways','CSV')}${download('./downloads/salary_ranges.csv','Salary ranges','CSV')}${download('./downloads/source_coverage.csv','Source checks','CSV')}</div></details></section></div>
  <details class="panel source-panel"><summary><h2>Source coverage <span class="selection-count">${state.coverage.length} checks · expand +</span></h2></summary><p class="caption">An inaccessible source does not imply no hiring.</p><div class="source-table-wrap"><table class="source-table"><thead><tr><th>Company / source</th><th>Result</th><th>Checked</th></tr></thead><tbody>${state.coverage.map(c=>`<tr><td><a href="${safeUrl(c.url)}" target="_blank" rel="noopener">${escape(c.company)} ↗</a></td><td class="status">${escape(c.status)}</td><td>${escape(c.checkedAt?.slice(0,10))}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function emptyView() { return '<div class="empty"><h2>No postings in this slice.</h2><p>Try another level, location or evidence group.</p><button class="button" data-action="reset">Reset filters</button></div>'; }
function render(focusKey) {
  renderHeading(); renderFilters();
  const jobs=selectJobs(state.jobs,state.filters);
  $('#content').innerHTML = state.view==='data' ? renderData() : state.view==='skills' ? renderSkills(jobs) : renderLandscape(jobs);
  $('#content').setAttribute('aria-busy','false');
  renderGuide();
  if (focusKey) document.querySelector(focusKey)?.focus({preventScroll:true});
  writeRoute();
}

$('#filters').addEventListener('change',event=>{
  const key=event.target.dataset.filter;
  if (!(key in defaults)) return;
  state.filters[key]=event.target.value;
  state.allRegions=false;
  render(`[data-filter="${key}"]`);
});
document.addEventListener('change',event=>{
  if(event.target.hasAttribute('data-other-skill') && event.target.value) { state.skills=unique([...state.skills,event.target.value]);persistSkills();render();return; }
  if(event.target.hasAttribute('data-remember')) { state.remember=event.target.checked; persistSkills(); }
});
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');
  if(!button)return;
  if(button.dataset.guideStep!==undefined){guideTo(Number(button.dataset.guideStep));return;}
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
    state.allRegions=false;render();return;
  }
  if(button.dataset.matrixRole){state.filters.role=button.dataset.matrixRole;state.scenario=button.dataset.matrixSkill;navigate('skills');return;}
  if(button.dataset.preview){state.scenario=button.dataset.preview;if(state.view!=='skills')navigate('skills');else render();$('.scenario')?.scrollIntoView({behavior:'smooth',block:'nearest'});return;}
  switch(button.dataset.action){
    case 'start-guide': guideTo(state.view==='skills'?1:0);break;
    case 'skip-guide': finishGuide();break;
    case 'guide-back': guideTo(state.guideStep-1);break;
    case 'guide-next': if(state.guideStep<2)guideTo(state.guideStep+1);else{finishGuide();toast('Keep exploring — you can reopen the guide anytime.');}break;
    case 'reset': state.filters={...defaults};state.allRegions=false;render();break;
    case 'regions': state.allRegions=!state.allRegions;render();break;
    case 'clear-skills': state.skills=[];state.scenario='';state.remember=false;persistSkills();render();break;
    case 'apply-skill': if(state.scenario){state.skills=unique([...state.skills,state.scenario]);state.scenario='';persistSkills();render();}break;
    case 'share': try {await navigator.clipboard.writeText(location.href);toast('Chart view copied. Your skills stay private.');}catch{toast('Copy the page address to share this view.');}break;
  }
});
window.addEventListener('hashchange',()=>{if(location.hash==='#main'){$('#main').focus();return;}readRoute();render();});
window.addEventListener('popstate',()=>{readRoute();render();});

async function init(){
  readRoute();
  try{state.guideActive=localStorage.getItem(guideKey)!=='true';}catch{}
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
