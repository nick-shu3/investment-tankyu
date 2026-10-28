#!/usr/bin/env python3
"""Validate publication-critical article metadata without external dependencies."""
import datetime as dt
import json
import re
from pathlib import Path
root = Path(__file__).resolve().parents[1]
ids = {c['id'] for c in json.loads((root / '_data/companies.json').read_text())}
seen = set()
for path in sorted((root / '_articles').glob('*.md')):
    parts = path.read_text().split('---', 2)
    assert len(parts) == 3 and not parts[0].strip(), path
    meta = dict(re.findall(r'^([a-z_]+):\s*([^\n]+)$', parts[1], re.M))
    meta = {k: v.strip().strip('"') for k, v in meta.items()}
    required = {'title','company_id','period','published','updated','announcement',
                'rating','rating_date','rating_reason','summary','review_status'}
    assert required <= meta.keys(), f'{path.name}: missing {required-meta.keys()}'
    assert meta['company_id'] in ids, path
    key = (meta['company_id'], meta['period'])
    assert key not in seen, f'Duplicate company/period: {key}'
    seen.add(key)
    assert meta['rating'] in {'好調','横ばい','注意','未評価'}, path
    dates = {k: dt.date.fromisoformat(meta[k]) for k in ('published','updated','announcement','rating_date')}
    assert dates['announcement'] <= dates['published'] <= dates['updated'], path
    assert dates['announcement'] <= dates['rating_date'] <= dates['updated'], path
    assert len(re.findall(r'^  - ', parts[1], re.M)) >= 3, f'{path}: missing conclusions'
    assert 'https://' in parts[2] and '更新履歴' in parts[2], path
    assert not re.search(r'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN .*PRIVATE KEY', path.read_text()), path
    print(f'PASS: {path.name} / {meta["rating"]} / {meta["rating_date"]}')
print(f'PASS: {len(seen)} unique earnings articles')
