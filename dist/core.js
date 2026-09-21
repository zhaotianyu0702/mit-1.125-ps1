export const ROLE_FAMILIES=['ML Engineering','AI Applications','Research','ML Infrastructure','Applied Data Science'];
export const DEGREES=['Bachelor','Master','PhD'];
export const DEFAULT_FILTERS={q:'',degrees:[],roles:[],state:'',city:'',company:'',workplace:'',graduation:'',start:'',experience:'',skill:'',tag:'',sponsorship:'',salary:'',deadlineOnly:false,includeZero:false,includeEarly:false,includeUnclear:false,includeUnknown:true,savedOnly:false,sort:'company'};
export const freshFilters=()=>({...DEFAULT_FILTERS,degrees:[],roles:[]});
export function unique(xs){return [...new Set(xs.filter(x=>x!==null&&x!==undefined&&x!==''))];}
export function canonicalUrl(url){try{const u=new URL(url);u.hash='';for(const key of [...u.searchParams.keys()])if(/^(utm_|source$|gh_src$|lever-source$|spread$|ref$)/i.test(key))u.searchParams.delete(key);return u.href.replace(/\/$/,'');}catch{return url;}}
export function deduplicate(jobs){const seen=new Set();return jobs.filter(j=>{const k=`${j.company.toLowerCase()}::${j.requisitionId||j.sourceId||canonicalUrl(j.url)}`;if(seen.has(k))return false;seen.add(k);return true;});}
const unknown=v=>v===null||v===undefined||v===''||v==='Not stated';
function pathChecks(path,f){const checks=[];
 if(f.degrees.length){const ds=path.degrees||[];checks.push(ds.length?f.degrees.some(d=>ds.includes(d)):null);}
 if(f.graduation){const ys=(path.graduationYears||[]).map(String);checks.push(ys.length?ys.includes(f.graduation):null);}
 if(f.experience!==''){const y=path.minYears;checks.push(y===null||y===undefined?null:path.experienceType==='research'&&y>0?null:y<=Number(f.experience));}
 return checks;
}
export function pathwayMatch(job,f){const active=f.degrees.length||f.graduation||f.experience!=='';if(!active)return 'not-filtered';const paths=job.qualificationPaths||[];if(!paths.length)return 'unknown';let unresolved=false;
 for(const p of paths){const checks=pathChecks(p,f);if(checks.every(x=>x===true))return 'match';if(!checks.includes(false)&&checks.includes(null))unresolved=true;}
 return unresolved?'unknown':'conflict';
}
export function filteredJobs(jobs,f,saved=[]){const result=jobs.filter(j=>{
 if(j.newgradStatus==='zero-experience'&&!f.includeZero)return false;
 if(j.newgradStatus==='early-career'&&!f.includeEarly)return false;
 if(j.newgradStatus==='unclear'&&!f.includeUnclear)return false;
 if(f.savedOnly&&!saved.includes(j.id))return false;
 const searchable=[j.company,j.title,j.summary,j.roleFamily,...(j.tags||[]),...(j.skills||[]).map(s=>s.name)].join(' ').toLowerCase();
 if(f.q&&!f.q.toLowerCase().trim().split(/\s+/).every(q=>searchable.includes(q)))return false;
 if(f.roles.length&&!f.roles.includes(j.roleFamily))return false;
 if(f.company&&j.company!==f.company)return false;
 if(f.state==='Remote'){if(!j.remote)return false;}else if(f.state&&!j.locations.some(l=>l.state===f.state))return false;
 if(f.city&&!j.locations.some(l=>l.city===f.city))return false;
 if(f.workplace&&j.workplace!==f.workplace&&!(f.includeUnknown&&unknown(j.workplace)))return false;
 const p=pathwayMatch(j,f);if(p==='conflict'||(p==='unknown'&&!f.includeUnknown))return false;
 if(f.start){const ys=(j.startYears||[]).map(String);if(ys.length?!ys.includes(f.start):!f.includeUnknown)return false;}
 if(f.skill&&!(j.skills||[]).some(s=>s.name===f.skill))return false;
 if(f.tag&&!(j.tags||[]).includes(f.tag))return false;
 if(f.sponsorship&&j.sponsorship!==f.sponsorship)return false;
 if(f.deadlineOnly&&!j.deadline)return false;
 if(f.salary){const rs=(j.salary||[]).filter(s=>s.currency==='USD'&&s.period==='year');if(rs.length?!rs.some(s=>s.max>=Number(f.salary)):!f.includeUnknown)return false;}
 return true;
 });
 return result.sort((a,b)=>{
  if(f.sort==='title')return a.title.localeCompare(b.title)||a.company.localeCompare(b.company);
  if(f.sort==='published')return (Date.parse(b.publishedAt)||0)-(Date.parse(a.publishedAt)||0)||a.company.localeCompare(b.company);
  if(f.sort==='deadline')return (Date.parse(a.deadline)||Infinity)-(Date.parse(b.deadline)||Infinity)||a.company.localeCompare(b.company);
  if(f.sort==='salary'){const top=j=>Math.max(0,...(j.salary||[]).filter(s=>s.currency==='USD'&&s.period==='year').map(s=>s.max||0));return top(b)-top(a)||a.company.localeCompare(b.company);}
  return a.company.localeCompare(b.company)||a.title.localeCompare(b.title);
 });
}
export function counts(jobs,getLabels){const values=new Map();for(const j of jobs)for(const k of unique(getLabels(j))){if(!values.has(k))values.set(k,{label:k,count:0,companies:new Set()});const v=values.get(k);v.count++;v.companies.add(j.company);}return [...values.values()].map(v=>({...v,companies:v.companies.size})).sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label));}
export function aggregate(jobs){return {total:jobs.length,companies:unique(jobs.map(j=>j.company)).length,states:unique(jobs.flatMap(j=>j.locations.map(l=>l.state))).length,explicit:jobs.filter(j=>j.newgradStatus==='explicit').length,remote:jobs.filter(j=>j.remote).length,salaryDisclosed:jobs.filter(j=>j.salary?.some(s=>s.currency==='USD'&&s.period==='year')).length,roles:counts(jobs,j=>[j.roleFamily]),locations:counts(jobs,j=>[...j.locations.map(l=>l.state),...(j.remote?['Remote — US']:[])]),degrees:counts(jobs,j=>j.qualificationPaths.flatMap(p=>p.degrees)),skills:counts(jobs,j=>(j.skills||[]).map(s=>s.name))};}
export function salaryText(job){const a=job.salary||[];if(!a.length)return 'Salary not stated';const usd=a.filter(s=>s.currency==='USD'&&s.period==='year');if(!usd.length)return 'See salary details';if(usd.length>1)return `${usd.length} disclosed pay ranges`;const s=usd[0];return `$${Math.round(s.min/1000)}k–$${Math.round(s.max/1000)}k / year`;}
export function locationText(j){if(j.locationText)return j.locationText;return j.remote?'Remote — US':j.locations.map(l=>[l.city,l.state].filter(Boolean).join(', ')).join(' · ');}
export function degreeText(j){const d=unique(j.qualificationPaths.flatMap(p=>p.degrees));return d.length?d.join(' / '):'Degree not stated';}
export function csvCell(v){let s=v===null||v===undefined?'':String(v);if(/^[=+@\-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function toCSV(jobs){const cols=['id','company','title','role_family','newgrad_status','review_level','review_note','locations','workplace','degree_pathways','graduation_windows','start_window','salary_ranges','skills','sponsorship','source','source_url','verified_at'];const rows=jobs.map(j=>[j.id,j.company,j.title,j.roleFamily,j.newgradStatus,j.reviewLevel||'curated-source-review',j.reviewNote||'',locationText(j),j.workplace,JSON.stringify(j.qualificationPaths),j.qualificationPaths.map(p=>p.graduation).join('; '),j.startWindow,JSON.stringify(j.salary),j.skills.map(s=>`${s.name} (${s.level})`).join('; '),j.sponsorship,j.source,j.url,j.verifiedAt]);return '\uFEFF'+[cols,...rows].map(row=>row.map(csvCell).join(',')).join('\r\n');}
export function filtersFromSearch(search){const f=freshFilters();const p=new URLSearchParams(search);for(const k of Object.keys(f)){if(!p.has(k))continue;const v=p.get(k);if(Array.isArray(f[k]))f[k]=v.split('|').filter(Boolean);else if(typeof f[k]==='boolean')f[k]=v==='true';else f[k]=v;}f.degrees=f.degrees.filter(d=>DEGREES.includes(d));f.roles=f.roles.filter(r=>ROLE_FAMILIES.includes(r));if(!['company','title','published','salary','deadline'].includes(f.sort))f.sort='company';return f;}
export function filtersToSearch(f){const p=new URLSearchParams();for(const k of Object.keys(DEFAULT_FILTERS)){if(k==='savedOnly')continue;const v=f[k];if(Array.isArray(v)){if(v.length)p.set(k,v.join('|'));}else if(v!==DEFAULT_FILTERS[k])p.set(k,String(v));}return p.toString();}
