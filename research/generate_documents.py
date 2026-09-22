#!/usr/bin/env python3
"""Generate concise AI Career Compass course artifacts from the frozen snapshot."""
from __future__ import annotations
import argparse, html, json, hashlib
from collections import Counter
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT=Path(__file__).resolve().parents[1]; ARTIFACTS=ROOT/'research'/'artifacts'
NAVY=colors.HexColor('#10233f'); BLUE=colors.HexColor('#1f6feb'); LIME=colors.HexColor('#b7e35f'); MUTED=colors.HexColor('#55657a'); PALE=colors.HexColor('#edf4fb')
US_STATES=set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())

def clean(v,f='Not stated'):
    if v is None or v=='': return f
    if isinstance(v,list): return ', '.join(clean(x,'') for x in v if x is not None)
    return str(v).replace('\u2013','-').replace('\u2014','-').replace('\u2011','-')

def load(p):
    if not p.exists(): raise SystemExit(f'Input snapshot not found: {p}')
    d=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(d,dict) or not isinstance(d.get('jobs'),list) or not isinstance(d.get('coverage'),list): raise SystemExit('Snapshot must contain jobs and coverage lists.')
    return d

def stats(d):
    jobs=d['jobs']; companies={clean(j.get('company'),'Unknown') for j in jobs}; roles=Counter(clean(j.get('roleFamily')) for j in jobs); levels=Counter(clean(j.get('experienceLevel'),'unspecified') for j in jobs); regions=Counter(); skills=Counter(); skill_companies={}; sources=Counter(clean(j.get('source')) for j in jobs)
    for j in jobs:
        labels={str(x.get('state') or '').strip().upper() for x in j.get('locations',[])} & US_STATES
        if j.get('remote'): labels.add('Remote - US')
        for x in labels: regions[x]+=1
        for n in {clean(x.get('name') if isinstance(x,dict) else x, '') for x in j.get('skills',[]) or []}:
            if n: skills[n]+=1; skill_companies.setdefault(n,set()).add(clean(j.get('company'),'Unknown'))
    return {'jobs':jobs,'companies':companies,'roles':roles,'levels':levels,'regions':regions,'skills':skills,'skill_companies':skill_companies,'coverage':d['coverage'],'sources':sources,'salary_count':sum(bool(j.get('salary')) for j in jobs)}

def styles():
    b=getSampleStyleSheet()
    return {'title':ParagraphStyle('T',parent=b['Title'],fontName='Helvetica-Bold',fontSize=19,leading=22,textColor=NAVY,spaceAfter=4),'sub':ParagraphStyle('S',parent=b['Normal'],fontSize=8.2,leading=10,textColor=MUTED,spaceAfter=6),'h':ParagraphStyle('H',parent=b['Heading2'],fontName='Helvetica-Bold',fontSize=9.7,leading=11.2,textColor=BLUE,spaceBefore=4,spaceAfter=2),'body':ParagraphStyle('B',parent=b['BodyText'],fontSize=9.2,leading=11.4,textColor=NAVY,spaceAfter=2),'small':ParagraphStyle('Sm',parent=b['BodyText'],fontSize=7.7,leading=9.1,textColor=NAVY)}

def footer(c,doc):
    c.saveState(); c.setStrokeColor(LIME); c.setLineWidth(2); c.line(doc.leftMargin,.43*inch,letter[0]-doc.rightMargin,.43*inch); c.setFont('Helvetica',6.6); c.setFillColor(MUTED); c.drawString(doc.leftMargin,.27*inch,'AI Career Compass | Project files'); c.drawRightString(letter[0]-doc.rightMargin,.27*inch,f'Page {doc.page}'); c.restoreState()

def pdf(path,title,subtitle,sections,d,links=()):
    st=styles(); s=stats(d); doc=SimpleDocTemplate(str(path),pagesize=letter,leftMargin=.56*inch,rightMargin=.56*inch,topMargin=.46*inch,bottomMargin=.56*inch)
    story=[Paragraph(html.escape(title),st['title']),Paragraph(html.escape(subtitle),st['sub'])]
    t=Table([[Paragraph('Snapshot',st['small']),Paragraph(clean(d.get('meta',{}).get('snapshotDate')),st['small'])],[Paragraph('Postings / companies',st['small']),Paragraph(f"{len(s['jobs'])} / {len(s['companies'])}",st['small'])],[Paragraph('Source checks',st['small']),Paragraph(str(len(s['coverage'])),st['small'])]],colWidths=[1.45*inch,1.9*inch],hAlign='LEFT'); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.35,colors.HexColor('#c9d9ea')),('INNERGRID',(0,0),(-1,-1),.2,colors.white),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)])); story += [t,Spacer(1,4)]
    for h,b in sections: story += [Paragraph(html.escape(h),st['h']),Paragraph(html.escape(b).replace('\n','<br/>'),st['body'])]
    if links:
        story += [Paragraph('Sources',st['h'])]
        for label,url in links:
            story += [Paragraph(f'<link href="{html.escape(url,quote=True)}" color="#1f6feb">{html.escape(label)}</link>',st['small'])]
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def submission_content(d):
    content=json.loads((ROOT/'research/submission-content.json').read_text())
    current=hashlib.sha256((ROOT/'dist/data.json').read_bytes()).hexdigest()
    if current != content['data_sha256'] or d != json.loads((ROOT/'dist/data.json').read_text()):
        raise ValueError('The submission note must be reviewed against the new frozen snapshot before generation.')
    return content

def note(d,out,key,title,subtitle):
    content=submission_content(d); sections=content[key]
    pdf(out/(key+'.pdf'),title,subtitle,sections,d,content['source_links'])
    lines=['# '+title,'',subtitle,'']
    for heading,body in sections: lines.extend(['## '+heading,'',body,''])
    lines+=['## Source links','']+[f'- [{label}]({url})' for label,url in content['source_links']]
    (out/(key+'.md')).write_text('\n'.join(lines)+'\n')

def methodology(d,out):
    note(d,out,'methodology','Data and methodology','Tianyu Zhao | MIT 1.125 PS1 | Snapshot: 2026-09-21')

def reflection(d,out):
    note(d,out,'reflection','Reflection','AI Career Compass | What the data supports and cannot prove')

def dictionary(d,out):
    s=stats(d); fields=[('id','Stable company-source identifier used for deduplication.'),('company / title / url','Employer, exact source title, and canonical official posting URL used by Job postings.'),('source / sourceId / verifiedAt','ATS or company-careers provenance and latest source check timestamp.'),('roleFamily / tags','Primary direction used for one-category charts, plus additional technical directions.'),('locations / locationText / remote / workplace','Source-listed US places and stated work arrangement; state and remote counts can overlap.'),('newgradStatus / newgradEvidence','Graduate evidence group: explicit, zero-experience, early-career, or unclear, with source explanation.'),('experienceLevel / experienceLevelBasis / experienceLevelEvidence','Four descriptive exploration buckets: 0–2 entry; experienced individual contributor with 3+ years, independent scope, or prior production track record, senior; explicit senior technical scope, staff; people-management scope, manager. Unsupported evidence remains unspecified.'),('experienceEvidenceSource / requirementYears / classifiedRequirementYears','Official excerpt, URL and check date; all parsed numbers and the numeric floor used for a requirements bucket. These do not establish eligibility.'),('experienceReferences','Raw year mentions from the full description; never a validated scalar minimum.'),('skills','Mentioned skill names with required, preferred, or mentioned level. Skill lab counts a posting when selected skills meet the fixed 70% fraction of its distinct tracked skills.'),('qualificationPaths','Degree and experience alternatives; unknown values stay unknown and are not converted to zero.'),('salary / sponsorship','Disclosed base-pay ranges and public sponsorship statement; missing disclosure is not a negative answer.'),('summary / aiEvidence / qualificationNote / reviewNote','Short factual evidence and review/provenance notes retained for source-grounded interpretation.'),('coverage','Company-level source check; inaccessible or incomplete sources are not treated as no qualifying jobs.'),('meta','Snapshot date, scope, unit, partitions, review description, and excluded count for reproducibility.')]
    lines=['# Data dictionary','',f"Generated from snapshot `{clean(d.get('meta',{}).get('snapshotDate'))}` with {len(s['jobs'])} postings and {len(s['companies'])} companies.",'','The unit is one unique public job posting. A posting may contain multiple locations, qualification paths, skills, or salary ranges.','','## Product measures','','- `direction distribution`: postings grouped by primary `roleFamily` or selected direction.','- `experience distribution`: postings grouped by four broad exploration buckets; unspecified remains visible when evidence is insufficient.','- `region distribution`: one count per listed state and a separate `Remote - US` bucket; totals can overlap.','- `skill-demand matrix`: postings mentioning a skill divided by filtered postings in the direction; one count per cell.','- `skill lab coverage`: filtered postings meeting a per-posting skill target (fixed at 70%), shown as count and fraction by role.','- `missing-skill recommendation`: unselected skills ranked by new target crossings, then summed 1/ceil(skill count * target) progress on unmet postings, then company breadth.','','## Snapshot fields','','| Field | Meaning |','| --- | --- |']
    lines += [f'| `{n}` | {m} |' for n,m in fields]; lines += ['','Unknown values remain explicit (`null`, empty arrays, `Not stated`, or `unclear`). Absence of a skill mention does not establish that the job does not require it.','','## Provenance','',f"The snapshot has {len(s['coverage'])} source checks and {s['salary_count']} postings with disclosed salary. Official URLs and review labels are preserved in `dist/downloads/jobs.csv` and the published data snapshot."]
    (out/'data-dictionary.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def demo(d,out):
    submission_content(d)
    (out/'demo-script.md').write_text((ROOT/'research/demo-script.md').read_text())

def presentation(d,out):
    (out/'presentation.html').write_bytes((ROOT/'research/video/presentation.html').read_bytes())

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',type=Path,default=ROOT/'dist'/'data.json'); p.add_argument('--output',type=Path,default=ARTIFACTS); a=p.parse_args(); d=load(a.input); a.output.mkdir(parents=True,exist_ok=True); methodology(d,a.output); reflection(d,a.output); dictionary(d,a.output); demo(d,a.output); presentation(d,a.output); print(f'Generated artifacts in {a.output}')
if __name__=='__main__': main()
