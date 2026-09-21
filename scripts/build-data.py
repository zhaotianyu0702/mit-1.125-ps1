#!/usr/bin/env python3
"""Build a deterministic public snapshot from curated and automated-discovery partitions."""
import csv
import io
import json
import re
import importlib.util
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parents[1]
_experience_spec = importlib.util.spec_from_file_location('experience', ROOT / 'scripts/experience.py')
_experience = importlib.util.module_from_spec(_experience_spec)
_experience_spec.loader.exec_module(_experience)
PARTITIONS = ['greenhouse', 'large_employers', 'other_employers', 'expanded_enterprise', 'expanded_ats', 'broad_greenhouse', 'broad_ashby']
FAMILIES = {'Machine Learning Engineering': 'ML Engineering', 'Research Scientist / Research Engineer': 'Research', 'Research Engineer': 'Research', 'AI / LLM Application Engineering': 'AI Applications', 'ML Infrastructure / MLOps': 'ML Infrastructure'}
STATES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY'.split())
CITY_STATES = {'San Francisco':'CA','San Francisco Bay Area':'CA','San Mateo':'CA','Sunnyvale':'CA','Palo Alto':'CA','Redwood City':'CA','Foster City':'CA','Mountain View':'CA','Santa Clara':'CA','San Jose':'CA','Seattle':'WA','Bellevue':'WA','Kirkland':'WA','New York':'NY','Boston':'MA','Cambridge':'MA','Westford':'MA','Pittsburgh':'PA','Las Vegas':'NV','Chicago':'IL','Austin':'TX','Atlanta':'GA','Raleigh':'NC','Durham':'NC','Madison':'WI','San Diego':'CA','Los Angeles':'CA'}
SKILL_NAMES = {'python':'Python','c++':'C++','c':'C','java':'Java','javascript':'JavaScript','go':'Go','sql':'SQL','pytorch':'PyTorch','tensorflow':'TensorFlow','jax':'JAX','llm':'LLMs','llms':'LLMs','nlp':'NLP','cv':'Computer vision','computer vision':'Computer vision','machine learning':'Machine learning','deep learning':'Deep learning','aws':'AWS','gcp':'GCP','cuda':'CUDA','docker':'Docker','kubernetes':'Kubernetes','spark':'Spark','ray':'Ray','airflow':'Airflow','distributed systems':'Distributed systems','mxnet':'MXNet','llvm':'LLVM','mlir':'MLIR'}
# Evidence reviewed by the integrating agent. Ambiguous role scope/experience is
# excluded, rather than weakening the public inclusion rule to increase count.
EXCLUSIONS = {
    'waymo-greenhouse-7488508': 'PhD New Grad title conflicts with 5+ years of ML experience in the requirements; excluded pending clarification.',
    'mach-industries-greenhouse-4390274009': 'Autonomy/GNC and general software responsibilities do not establish core AI/ML work under this project definition.',
    'mach-industries-greenhouse-4401441009': 'Classical GNC, navigation and simulation are not sufficient evidence of core AI/ML responsibilities.',
}

def clean_url(value):
    u = urlsplit(value)
    query = [(k, v) for k, v in parse_qsl(u.query) if not k.startswith('utm_') and k not in {'source', 'gh_src', 'spread', 'ref'}]
    return urlunsplit((u.scheme, u.netloc, u.path.rstrip('/'), urlencode(query), ''))

def scalar(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return '' if value is None else value

def write_csv(name, rows, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        safe = {}
        for key in fields:
            value = scalar(row.get(key))
            if isinstance(value, str) and value and value[:1] in '=+@-':
                value = "'" + value
            safe[key] = value
        writer.writerow(safe)
    (ROOT / 'dist/downloads' / name).write_text(out.getvalue(), encoding='utf-8-sig')

def build():
    jobs, coverage, excluded = [], [], []
    for part in PARTITIONS:
        path = ROOT / 'research' / f'{part}.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        jobs.extend(data['jobs'])
        coverage.extend(data.get('coverage', []))
    correction_path = ROOT / 'research/verified-corrections.json'
    corrections = json.loads(correction_path.read_text()).get('jobs', {}) if correction_path.exists() else {}
    experience_path = ROOT / 'research/experience-evidence.json'
    experience_evidence = json.loads(experience_path.read_text()).get('jobs', {}) if experience_path.exists() else {}
    output, seen, seen_urls, seen_ids = [], set(), set(), set()
    for j in jobs:
        if j['id'] in EXCLUSIONS:
            excluded.append({'id': j['id'], 'company': j['company'], 'url': j['url'], 'reason': EXCLUSIONS[j['id']]})
            continue
        correction = corrections.get(str(j.get('sourceId')))
        if correction and correction.get('verification') == 'live_ashby_api' and correction.get('fields'):
            j.update(correction['fields'])
            j['verifiedAt'] = correction['verifiedAt']
            note = correction.get('verificationNote', '')
            j['qualificationNote'] = note
            j['newgradEvidence'] = note
            j['reviewNote'] = 'Rechecked the complete live official Ashby posting. ' + note
            for path in j['qualificationPaths']:
                path.setdefault('evidence', note)
            if j['company'] == 'Netic':
                j['startWindow'], j['startYears'] = 'Winter 2026 through Summer 2027', [2026, 2027]
                for path in j['qualificationPaths']:
                    path['graduation'], path['graduationYears'] = 'Not stated; source gives a start window', []
            if j['company'] == 'Fireworks AI':
                j['startWindow'], j['startYears'] = 'Not stated; degree-completion windows are recorded separately', []
            if j['company'] == 'Decagon':
                j['startWindow'], j['startYears'] = '2027 start', [2027]
                for path in j['qualificationPaths']:
                    path['degrees'] = ['Bachelor', 'Master', 'PhD']
        j['company'] = j['company'].strip()
        j['company'] = {'ByteDance/TikTok': 'TikTok/ByteDance', 'Databricks AI':'Databricks','Scale AI Research':'Scale AI','The Allen Institute':'AI2', 'Mistral':'Mistral AI'}.get(j['company'], j['company'])
        j['title'] = j['title'].strip()
        j['roleFamily'] = FAMILIES.get(j['roleFamily'], j['roleFamily'])
        j['url'] = clean_url(j['url'])
        j['applyUrl'] = j.get('applyUrl') or j['url']
        key = (j['company'].lower(), j.get('requisitionId') or j.get('sourceId') or j['url'])
        if key in seen or j['url'] in seen_urls or j['id'] in seen_ids:
            continue
        seen.add(key)
        seen_urls.add(j['url'])
        seen_ids.add(j['id'])
        for field in ['skills', 'tags', 'salary', 'startYears', 'qualificationPaths', 'locations']:
            j.setdefault(field, [])
        for field in ['publishedAt', 'deadline']:
            j.setdefault(field, None)
        for field in ['startWindow', 'sponsorship', 'sponsorshipNote', 'workplace']:
            j.setdefault(field, 'Not stated')
        locations = [l for l in j['locations'] if l.get('country') == 'US' and l.get('state') in STATES]
        # Resolve explicitly named US cities; country-level placeholders are
        # never counted as a state. Preserve source location text alongside it.
        loc_text = j.get('locationText', '')
        for city, state in (CITY_STATES.items() if j.get('reviewLevel') != 'automated-discovery' else []):
            if re.search(r'\b' + re.escape(city) + r'\b', loc_text, re.I) and not any(l['city'].lower() == city.lower() for l in locations):
                locations.append({'city': city, 'state': state, 'country': 'US'})
        j['locations'] = locations or [{'city': 'US location not specified', 'state': '', 'country': 'US'}]
        j['tags'] = list(dict.fromkeys(j['tags']))
        skills = []
        for skill in j['skills']:
            name = skill['name'].strip()
            parts = name.split('/')
            # A combined technology label supports mentions, but by itself
            # does not establish whether the original condition was AND/OR.
            if len(parts) > 1 and all(p.lower().strip() in SKILL_NAMES for p in parts):
                for p in parts:
                    skills.append({'name': SKILL_NAMES[p.lower().strip()], 'level': 'mentioned', 'alternativeGroup': None})
            else:
                skills.append({**skill, 'name': SKILL_NAMES.get(name.casefold(), name)})
        skill_levels = {'required': 3, 'preferred': 2, 'mentioned': 1}
        skills.sort(key=lambda s: skill_levels.get(s['level'], 0))
        j['skills'] = list({s['name'].casefold(): s for s in skills}.values())
        if j.get('remote'):
            j['remoteScope'] = 'state-limited' if re.search(r'(?:US,?\s*)?[A-Z]{2},?\s*Remote|Remote[, -]+(?:California|CA)\b', loc_text) else 'unspecified'
        j['remote'] = bool(j.get('remote'))
        j.setdefault('reviewLevel', 'curated-source-review')
        j['statusAtCheck'] = 'Listed on official public board; full terms need review' if j['reviewLevel'] == 'automated-discovery' else 'Official posting checked on the recorded date'
        if j.get('sponsorship') == 'Conditional' and 'no sponsorship promise' in j.get('sponsorshipNote', '').lower():
            j['sponsorship'] = 'Not stated'
        if j['company'] == 'NVIDIA':
            j['qualificationNote'] = re.sub(r'No full-time industry-years floor is stated; minYears 0 means zero industry experience, while research or project evidence remains a separate requirement\. ?', 'The graduate pathway has no stated minimum of full-time industry experience. Research and project requirements still apply. ', j.get('qualificationNote', ''))
        if j['company'] == 'ID.me':
            j['tags'] = ['fraud detection', 'evaluation']
        for p in j['qualificationPaths']:
            if j['company'] == 'NVIDIA' and p.get('minYears') == 0:
                p['minYears'] = None  # A graduate title does not state a numeric experience floor.
            p.setdefault('graduationYears', [])
            p.setdefault('graduation', 'Not stated')
            p.setdefault('minYears', None)
            p.setdefault('experienceType', 'not stated')
            p['graduationYears'] = [int(y) for y in p['graduationYears']]
            p.setdefault('evidence', j.get('qualificationNote') or j['newgradEvidence'])
        if j['newgradStatus'] == 'early-career' and not any(p.get('minYears') is not None and p['minYears'] <= 2 for p in j['qualificationPaths']):
            j['newgradStatus'] = 'unclear'
        # A minimum review/acceptance date is not a closing deadline. Collector
        # corrections override this safeguard once the source gives a real end.
        if j['company'] == 'NVIDIA':
            j['deadline'] = None
            if not re.search(r'\b(start|onboard|join)\b.*20\d{2}', j.get('startWindow', ''), re.I):
                j['startYears'] = []
                j['startWindow'] = 'Not stated'
        if j['company'] == 'TikTok/ByteDance':
            for p in j['qualificationPaths']:
                if 'onboard' in p['graduation'].lower() or 'start' in p['graduation'].lower():
                    p['graduationYears'] = []
        j.setdefault('experienceReferences', sorted({p['minYears'] for p in j['qualificationPaths'] if p.get('minYears') is not None}))
        label = _experience.classify_experience(j['title'], j['newgradStatus'], j['experienceReferences'])
        evidence = experience_evidence.get(j['id'], {})
        evidence_matches = (
            str(evidence.get('sourceId')) == str(j.get('sourceId'))
            and evidence.get('sourceTitle') == j['title']
            and evidence.get('sourceVerifiedAt') == j.get('verifiedAt')
            and clean_url(evidence.get('sourceUrl', '')) == j['url']
        )
        if label['experienceLevel'] == 'unspecified' and evidence_matches:
            label = {k: evidence[k] for k in ('experienceLevel', 'experienceLevelBasis', 'experienceLevelEvidence')}
            j['experienceEvidenceSource'] = {
                'url': evidence['sourceUrl'], 'verifiedAt': evidence['sourceVerifiedAt'],
                'type': evidence['evidenceType'], 'excerpt': evidence.get('excerpt')
            }
            if evidence.get('requirementYears') is not None:
                j['requirementYears'] = evidence['requirementYears']
        if label['experienceLevelBasis'] == 'requirements' and evidence_matches and evidence.get('classifiedRequirementYears') is not None:
            j['classifiedRequirementYears'] = evidence['classifiedRequirementYears']
        j.update(label)
        output.append(j)
    output.sort(key=lambda j: (j['company'].lower(), j['title'].lower()))
    counts = Counter(j['company'] for j in output)
    for c in coverage:
        c['company'] = c['company'].strip()
        c['company'] = {'ByteDance/TikTok':'TikTok/ByteDance', 'Databricks AI':'Databricks', 'Scale AI Research':'Scale AI', 'The Allen Institute':'AI2', 'Mistral':'Mistral AI'}.get(c['company'], c['company'])
        c['snapshotCompanyCount'] = counts.get(c['company'], 0)
        if c.get('note', '').startswith('Automated') and c.get('status') != 'inaccessible':
            c['status'] = 'discovery leads' if c.get('qualifyingCount') else 'no leads passed screen'
        if c.get('status') == 'verified roles' and not c['snapshotCompanyCount']:
            c['status'] = 'no qualifying roles'
            c['note'] = c.get('note', '') + ' Integrating review excluded the candidate roles under the stricter published scope.'
    # Keep one latest check per employer/source endpoint. Repeated requests
    # across collectors are not additional sources or additional employers.
    latest = {}
    for c in coverage:
        key = (c['company'].casefold(), clean_url(c['url']))
        if key not in latest or str(c.get('checkedAt', '')) >= str(latest[key].get('checkedAt', '')):
            latest[key] = c
    coverage = sorted(latest.values(), key=lambda c: (c['company'].casefold(), c['url']))
    old_path = ROOT / 'dist/data.json'
    old_meta = json.loads(old_path.read_text()).get('meta', {}) if old_path.exists() else {}
    meta = {'snapshotDate': '2026-09-21', 'generatedAt': datetime.now(timezone.utc).isoformat(), 'version': '3.2', 'unit': 'unique public job posting', 'geography': 'United States', 'scope': 'US AI technical roles across experience levels; graduate eligibility is independent of title and source-inferred experience buckets', 'review': 'Curated source review plus separately labeled automated discovery; not employer-certified', 'githubUrl': 'https://github.com/zhaotianyu0702/mit-1.125-ps1', 'sourcePartitions': PARTITIONS, 'excludedCount': len(excluded)}
    result = {'meta': meta, 'jobs': output, 'coverage': coverage, 'excluded': excluded}
    old_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'research/integration-exclusions.json').write_text(json.dumps(excluded, ensure_ascii=False, indent=2) + '\n')
    common = ['id', 'company', 'title', 'url', 'applyUrl', 'source', 'sourceId', 'roleFamily', 'newgradStatus', 'experienceLevel', 'experienceLevelBasis', 'experienceLevelEvidence', 'experienceEvidenceSource', 'requirementYears', 'classifiedRequirementYears', 'locationText', 'workplace', 'remote', 'remoteScope', 'reviewLevel', 'experienceReferences', 'qualificationPaths', 'startWindow', 'startYears', 'skills', 'salary', 'sponsorship', 'sponsorshipNote', 'summary', 'newgradEvidence', 'aiEvidence', 'qualificationNote', 'publishedAt', 'deadline', 'verifiedAt', 'reviewNote']
    write_csv('jobs.csv', output, common)
    write_csv('qualification_paths.csv', [{'job_id': j['id'], 'path_id': f"{j['id']}-{i+1}", **p} for j in output for i, p in enumerate(j['qualificationPaths'])], ['job_id', 'path_id', 'degrees', 'minYears', 'experienceType', 'graduation', 'graduationYears', 'evidence'])
    write_csv('job_locations.csv', [{'job_id': j['id'], **l, 'workplace': j['workplace'], 'remote': j['remote']} for j in output for l in j['locations']], ['job_id', 'city', 'state', 'country', 'workplace', 'remote'])
    write_csv('job_skills.csv', [{'job_id': j['id'], **s} for j in output for s in j['skills']], ['job_id', 'name', 'level', 'alternativeGroup'])
    write_csv('salary_ranges.csv', [{'job_id': j['id'], **s} for j in output for s in j['salary']], ['job_id', 'min', 'max', 'currency', 'period', 'scope'])
    write_csv('source_coverage.csv', coverage, ['company', 'url', 'checkedAt', 'status', 'qualifyingCount', 'snapshotCompanyCount', 'note'])
    print(json.dumps({'jobs': len(output), 'companies': len(counts), 'coverage': len(coverage), 'excluded': len(excluded), 'byCompany': dict(counts)}))

if __name__ == '__main__':
    build()
