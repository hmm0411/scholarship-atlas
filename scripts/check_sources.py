#!/usr/bin/env python3
"""Read-only monitor for curated official sources. No unreviewed scholarship field edits."""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
SOURCES = DATA / 'sources.json'
STATE = DATA / 'source_state.json'
REPORT = DATA / 'updates.json'
MAX_SIZE = 1_200_000
UA = 'ScholarshipAtlasResearchMonitor/2.0 (daily academic scholarship updates; contact repository owner)'


def load_json(path: Path, fallback):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, type(fallback)) else fallback
    except (OSError, ValueError):
        return fallback


def clean_html(page: str) -> str:
    page = re.sub(r'<!--.*?-->', ' ', page, flags=re.S)
    page = re.sub(r'<(script|style|svg|nav|footer|header|noscript)\b[^>]*>.*?</\1>', ' ', page, flags=re.S | re.I)
    page = re.sub(r'<[^>]*>', ' ', page)
    page = html.unescape(page)
    return re.sub(r'\s+', ' ', page).strip()


def excerpt(text: str, count=5):
    found = []
    regex = re.compile(r'(?i)(2027|2028|deadline|application(?:s)?|scholarship|eligib|admission|funding|closing date)')
    for match in regex.finditer(text):
        item = text[max(0, match.start() - 85): min(len(text), match.end() + 140)].strip()
        if len(item) >= 30 and item not in found:
            found.append(item)
        if len(found) >= count:
            break
    return found


def fetch(url: str):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml'})
    with urllib.request.urlopen(req, timeout=16) as resp:
        content_type = resp.headers.get('Content-Type', '').lower()
        if 'html' not in content_type:
            raise ValueError('Not an HTML page (' + content_type[:60] + ')')
        raw = resp.read(MAX_SIZE + 1)
        if len(raw) > MAX_SIZE:
            raise ValueError('Page exceeds safe size limit')
        charset = resp.headers.get_content_charset() or 'utf-8'
        return clean_html(raw.decode(charset, errors='replace'))


def run():
    config = load_json(SOURCES, {})
    entries = config.get('sources', [])
    if not isinstance(entries, list):
        raise ValueError('sources.json requires sources array')
    state = load_json(STATE, {})
    previous_report = load_json(REPORT, {})
    history = previous_report.get('changes', [])
    if not isinstance(history, list):
        history = []
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    observations = []
    changes = []
    seen_ids = set()
    for entry in entries:
        if not entry.get('enabled', True):
            continue
        identifier, url = entry.get('id', ''), entry.get('url', '')
        if not identifier or not url.startswith('https://'):
            continue
        detail = dict(id=identifier, name=entry.get('name', identifier), region=entry.get('region',''), organization=entry.get('organization',''), url=url, priority=entry.get('priority','medium'), checked_at=now)
        try:
            content = fetch(url)
            if len(content) < 100:
                raise ValueError('Insufficient readable text; verify the page manually')
            digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
            old = state.get(identifier, {})
            changed = bool(old.get('hash') and old['hash'] != digest)
            detail.update(status='changed' if changed else 'ok', changed=changed, excerpts=excerpt(content), last_success=now)
            state[identifier] = dict(hash=digest, name=detail['name'], url=url, last_success=now)
            if changed:
                changes.append(dict(id=hashlib.sha256((identifier+digest).encode()).hexdigest()[:16], name=detail['name'], url=url, kind='Phát hiện thay đổi trên nguồn', checked_at=now, summary='Nguồn chính thức có thay đổi văn bản. Cần mở trang để tự xác minh deadline, học phí, điều kiện và kỳ tuyển trước khi cập nhật hồ sơ.'))
        except Exception as exc:
            detail.update(status='error', changed=False, error=str(exc)[:180], last_success=state.get(identifier, {}).get('last_success'))
        observations.append(detail)
        # Avoid hammering hosts; only a single request per URL each run.
        if os.getenv('ATLAS_NO_DELAY') != '1':
            time.sleep(0.35)
    merged=[]
    for item in changes + history:
        identity=item.get('id')
        if identity and identity not in seen_ids:
            merged.append(item)
            seen_ids.add(identity)
    report=dict(schema_version=2,generated_at=now,policy='Read-only signals; manual verification required for dates and eligibility.',summary={'monitored':len(observations),'ok':sum(i['status']=='ok' for i in observations),'changed':sum(i['status']=='changed' for i in observations),'errors':sum(i['status']=='error' for i in observations)},sources=observations,changes=merged[:150])
    DATA.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Sources',len(observations),'changed',report['summary']['changed'],'errors',report['summary']['errors'])
    # Fail only for invalid configuration, not individual website access failures.

if __name__ == '__main__':
    run()
