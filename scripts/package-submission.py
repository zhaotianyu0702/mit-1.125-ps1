#!/usr/bin/env python3
"""Package the frozen site and all non-video PS1 deliverables without recollecting data."""
from __future__ import annotations
import csv
import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
DOWNLOADS=DIST/'downloads'
SITE='https://ai-career-compass-us-new-grad.zhaotianyu0702.chatgpt.site'
REPO='https://github.com/zhaotianyu0702/mit-1.125-ps1'
ZIP_NAME='ai-career-compass-ps1.zip'
PACK_ROOT='mit-1.125-ps1-submission'


def sha(data): return hashlib.sha256(data).hexdigest()
def esc(value): return html.escape(str(value),quote=True)


def main():
    raw=(DIST/'data.json').read_bytes(); data=json.loads(raw); jobs=data['jobs']
    study=json.loads((ROOT/'research/skill-threshold-study.json').read_text())
    note=json.loads((ROOT/'research/submission-content.json').read_text())
    assert study['dataSha256']==note['data_sha256']==sha(raw),'Freeze and review the new snapshot first.'
    assert study['selectedTarget']==70
    for name in ['methodology.pdf','methodology.md','reflection.pdf','reflection.md','demo-script.md','data-dictionary.md']:
        shutil.copyfile(ROOT/'research/artifacts'/name,DOWNLOADS/name)
    shutil.copyfile(ROOT/'research/artifacts/presentation.html',DIST/'presentation.html')
    shutil.copyfile(ROOT/'research/skill-threshold-study.md',DOWNLOADS/'skill-target-study.md')
    shutil.copyfile(ROOT/'research/skill-threshold-study.json',DOWNLOADS/'skill-target-study.json')
    n=len(jobs); companies=len({j['company'] for j in jobs})
    non_ca=sum(any(l.get('state') and l['state']!='CA' for l in j['locations']) for j in jobs)
    explicit=sum(j['newgradStatus']=='explicit' for j in jobs)
    ds=[j for j in jobs if j['roleFamily']=='Applied Data Science']
    infra=[j for j in jobs if j['roleFamily']=='ML Infrastructure']
    skill_count=lambda rows,name:sum(name in {s['name'] if isinstance(s,dict) else s for s in j['skills']} for j in rows)
    sql=skill_count(ds,'SQL'); k8s=skill_count(infra,'Kubernetes')
    base=next(r for r in study['rows'] if r['slice']=='All' and r['profile']=='Python + ML' and r['threshold']==70)
    llms=next(r for r in base['recommendations'] if r['skill']=='LLMs')
    findings=[
        ('Look beyond one region',f'{non_ca}/{n} postings ({non_ca/n:.1%}) name at least one location outside California. New York appears in 225 and Washington in 86. Location counts overlap.'),
        ('Graduate evidence needs its own filter',f'{explicit}/{n} postings explicitly identify a graduate pathway. The 66 Entry labels also include inferred experience; they do not all establish graduate eligibility.'),
        ('Learning priorities differ by direction',f'SQL appears in {sql}/{len(ds)} Data Science postings ({sql/len(ds):.1%}). Kubernetes appears in {k8s}/{len(infra)} ML Infrastructure postings ({k8s/len(infra):.1%}). These are mentions in the sample.')
    ]
    recommendations=[
        ('Broaden location comparisons',f'Students and career groups should compare non-California locations before narrowing their exploration. The {non_ca} postings with a non-California location provide a concrete starting set; inspect the actual location and remote restrictions.'),
        ('Use separate learning tracks',f'Career groups can offer a SQL-focused Data Science session and a Kubernetes-focused infrastructure session, based on the {sql}/{len(ds)} and {k8s}/{len(infra)} mention counts. Students can then use Skill lab to choose one project suited to their existing skills; mention frequency alone does not establish a course prerequisite.')
    ]
    methods='Counts refer to unique postings in the 2026-09-21 snapshot, not hires. State and skill counts can overlap. The sample is purposive; 795 postings are automated discovery and 57 have curated source review.'
    lines=['# Findings and recommendations','',methods,'','## Findings','']
    for title,body in findings: lines.extend(['### '+title,'',body,''])
    lines+=['## Two practical recommendations','']
    for title,body in recommendations: lines.extend(['### '+title,'',body,''])
    lines+=['## Reproducible skill example','',f'With all filters reset, Python + Machine learning cover {base["covered"]}/{base["scored"]} postings at the fixed 70% target. Adding LLMs adds {llms["gain"]}, reaching {base["covered"]+llms["gain"]}/{base["scored"]}. Another {llms["closerCount"]} postings move closer while staying below target. This is a hypothetical selection, not a measured student outcome.','',f'Source: [frozen dataset]({SITE}/downloads/jobs.csv), [locations]({SITE}/downloads/job_locations.csv), [skill mentions]({SITE}/downloads/job_skills.csv), [source checks]({SITE}/downloads/source_coverage.csv).','',f'Dataset SHA-256: `{sha(raw)}`.']
    (DOWNLOADS/'findings.md').write_text('\n'.join(lines)+'\n')
    csv_names={
        'jobs.csv':'One row per posting, with source URL, timestamps, evidence and review labels',
        'job_skills.csv':'One row per tracked skill mention; join job_id to jobs.id',
        'job_locations.csv':'One row per location; multi-location postings repeat',
        'qualification_paths.csv':'Degree and experience alternatives; unknown stays unknown',
        'salary_ranges.csv':'Only disclosed ranges, with currency, period and scope',
        'source_coverage.csv':'Employer/endpoint checks, dates, access outcomes and notes'
    }
    counts={}
    for name in csv_names:
        with (DOWNLOADS/name).open(encoding='utf-8-sig',newline='') as f: counts[name]=sum(1 for _ in csv.DictReader(f))
    assert counts['jobs.csv']==n
    artifacts=[
        ('methodology.pdf','One-page data and methodology note','PDF'),
        ('reflection.pdf','What the data supports and cannot prove','PDF'),
        ('demo-script.md','Five-minute demonstration script','MD'),
        ('findings.md','Findings and practical recommendations','MD'),
        ('data-dictionary.md','Units, fields and definitions','MD'),
        ('skill-target-study.md','Why the skill target is fixed at 70%','MD')
    ]
    link=lambda path,label:f'<a href="{esc(path)}">{esc(label)}</a>'
    data_rows=''.join(f'<tr><th scope="row">{link("./downloads/"+name,name)}</th><td>{counts[name]:,}</td><td>{esc(desc)}</td></tr>' for name,desc in csv_names.items())
    artifact_rows=''.join(f'<li>{link("./downloads/"+name,label)}<span>{kind}</span></li>' for name,label,kind in artifacts)
    fact_html=''.join(f'<article><h3>{esc(title)}</h3><p>{esc(body)}</p></article>' for title,body in findings)
    rec_html=''.join(f'<li><strong>{esc(title)}.</strong> {esc(body)}</li>' for title,body in recommendations)
    page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PS1 submission materials · AI Career Compass</title><meta name="description" content="Dataset, methodology, findings, reflection and demonstration materials for MIT 1.125 PS1."><link rel="icon" href="./favicon.svg" type="image/svg+xml">
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f7f8f3;color:#172c37;font:16px/1.6 system-ui,sans-serif}}main{{max-width:900px;margin:auto;padding:30px 24px 60px}}a{{color:#176d61;text-underline-offset:3px}}a:focus-visible{{outline:3px solid #176d61;outline-offset:4px}}header{{padding:24px 0;border-bottom:1px solid #dce2da}}h1{{font-size:clamp(2rem,5vw,2.7rem);line-height:1.12;margin:16px 0}}h2{{font-size:1.35rem;margin:0 0 16px}}h3{{font-size:1rem;margin:0 0 5px}}p{{margin:0 0 15px}}.meta{{color:#52635e;font-size:14px}}.actions{{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0 0}}.download{{display:inline-block;background:#1f7568;color:white;border-radius:6px;padding:10px 15px;text-decoration:none;font-weight:600}}section{{padding:28px 0;border-bottom:1px solid #dce2da}}.file-list{{list-style:none;margin:0;padding:0}}.file-list li{{display:flex;justify-content:space-between;gap:20px;padding:11px 0;border-bottom:1px solid #e6eae3}}.file-list span{{color:#52635e;font-size:13px;white-space:nowrap}}.table-wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px 12px 10px 0;border-bottom:1px solid #e0e6dd;text-align:left;vertical-align:top}}th{{font-weight:500}}td:nth-child(2){{white-space:nowrap;font-variant-numeric:tabular-nums}}article+article{{margin-top:18px}}ol{{padding-left:21px}}ol li{{margin-bottom:14px}}code{{font-size:12px;overflow-wrap:anywhere}}footer{{padding-top:25px}}@media(max-width:600px){{main{{padding:20px 18px 40px}}th,td{{font-size:13px}}.table-wrap table{{min-width:620px}}.file-list li{{gap:12px}}}}@media print{{body{{background:white}}.actions{{display:none}}section{{break-inside:avoid}}}}</style></head>
<body><main><a href="./#landscape">← AI Career Compass</a><header><p class="meta">MIT 1.125 · PS1 · Tianyu Zhao</p><h1>Submission materials</h1><p>{n:,} US AI postings · {companies} companies · Snapshot 21 September 2026</p><p>For students beginning to explore AI careers, and university career services or student groups helping them choose a direction and next learning project.</p><div class="actions"><a class="download" href="{SITE}/downloads/{ZIP_NAME}" download>Download submission pack</a><a class="download" href="./presentation.html">Open five-minute presentation</a></div><p class="meta" style="margin-top:12px">Includes all written materials and presentation notes. Video recording is not included.</p></header>
<section aria-labelledby="documents"><h2 id="documents">Documents</h2><ul class="file-list">{artifact_rows}<li>{link('./presentation.html','Five-slide presentation')}<span>HTML</span></li><li>{link(REPO,'Submission repository')}<span>GITHUB</span></li></ul></section>
<section aria-labelledby="dataset"><h2 id="dataset">Collected dataset</h2><p class="meta">UTF-8 CSVs. Join related tables using job_id = jobs.id. One posting can have several locations, skills or qualification paths.</p><div class="table-wrap"><table><thead><tr><th>File</th><th>Rows</th><th>Unit / contents</th></tr></thead><tbody>{data_rows}</tbody></table></div><p style="margin-top:14px">{link('./data.json','Canonical JSON snapshot')} · {link('./downloads/skill-target-study.json','Full threshold test results')}</p></section>
<section aria-labelledby="findings"><h2 id="findings">Main findings</h2>{fact_html}<p class="meta">{esc(methods)}</p></section>
<section aria-labelledby="recommendations"><h2 id="recommendations">Two decisions the data can inform</h2><ol>{rec_html}</ol></section>
<section aria-labelledby="limits"><h2 id="limits">Interpretation</h2><p>198 postings have unspecified experience, 101 have no named US state, and 36 have no tracked skills. Skill lab scores 816 postings and uses the same fixed 70% target throughout. Missing data is not evidence of no requirements.</p><p>This sample cannot establish national demand, proficiency, eligibility or hiring probability. The methodology note explains collection, bias, definitions and the source trail. Skill selections stay in your browser.</p></section>
<footer><p>{link('./#skills','Open Skill lab')} · {link('./#postings','Inspect job postings and sources')}</p><p class="meta">Frozen dataset SHA-256<br><code>{sha(raw)}</code></p></footer></main></body></html>'''
    (DIST/'submission.html').write_text(page)
    readme=f'''# MIT 1.125 PS1 — AI Career Compass

Author: Tianyu Zhao. Frozen snapshot: 2026-09-21. Skill target: fixed 70%.

Published site: {SITE}
Submission materials: {SITE}/submission.html
GitHub submission repository: {REPO}

## Deliverables (excluding the recording)

1. Complete static site: `site/`. Start with `site/submission.html` for documents.
2. Dataset: `site/downloads/jobs.csv` ({n} postings) plus five related CSVs.
3. One-page data and methodology note: `site/downloads/methodology.pdf` and editable Markdown.
4. Five-slide presentation: `site/presentation.html`; timed demonstration script: `site/downloads/demo-script.md`. Slides and script are prepared. No video file is included.
5. Short reflection: `site/downloads/reflection.pdf` and editable Markdown.
6. Findings, two recommendations, definitions, sources and the fixed-target study: `site/downloads/`.

The GitHub repository contains the collection partitions, scripts and tests. This pack includes the complete static website source and frozen data. There is no applicant profile data, local browser state or credential material.

## Run the packaged site locally

From this extracted folder:

    python3 -m http.server 8767 --directory site --bind 127.0.0.1

Open http://127.0.0.1:8767/. Use HTTP because the dashboard fetches data.json.

## Verify the snapshot

Dataset SHA-256: `{sha(raw)}`. `manifest.json` contains each packaged file's SHA-256 and CSV row counts. This is a dated purposive sample, not a labor-market census. The original brief asks for a five-minute demonstration without specifying a recording format. Video remains outside this package.

## Course submission locations

Enter the main published site URL in the course sheet's `PS1 Site URL` column and the repository URL in `PS1 Repo`. These are separate from the final-project columns.
'''
    (ROOT/'SUBMISSION.md').write_text(readme.replace('`site/`','`dist/`').replace('`site/','`dist/').replace('--directory site','--directory dist').replace('`manifest.json`','`dist/downloads/submission-manifest.json`'))
    public_files=sorted(p for p in DIST.rglob('*') if p.is_file() and p.name not in {ZIP_NAME,'submission-manifest.json'})
    allowed_suffixes={'.html','.css','.js','.json','.csv','.md','.pdf','.svg','.png','.jpg','.jpeg','.webp','.ico'}
    assert all(p.suffix.lower() in allowed_suffixes for p in public_files), 'Review an unexpected public file type before packaging.'
    members={'README.md':readme.encode(),**{'site/'+p.relative_to(DIST).as_posix():p.read_bytes() for p in public_files}}
    manifest={'project':'MIT 1.125 PS1 — AI Career Compass','snapshotDate':data['meta']['snapshotDate'],'skillCoverageTarget':70,'dataSha256':sha(raw),'siteUrl':SITE,'repositoryUrl':REPO,'videoIncluded':False,'csvRows':counts,'files':[{'path':name,'bytes':len(b),'sha256':sha(b)} for name,b in sorted(members.items())]}
    manifest_bytes=(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
    (DOWNLOADS/'submission-manifest.json').write_bytes(manifest_bytes)
    members['manifest.json']=manifest_bytes
    archive=DOWNLOADS/ZIP_NAME
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,b in sorted(members.items()):
            info=zipfile.ZipInfo(PACK_ROOT+'/'+name,date_time=(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,b)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,b in members.items(): assert z.read(PACK_ROOT+'/'+name)==b,name
    print(json.dumps({'package':str(archive),'files':len(members),'bytes':archive.stat().st_size,'csvRows':counts,'dataSha256':sha(raw)}))

if __name__=='__main__': main()
