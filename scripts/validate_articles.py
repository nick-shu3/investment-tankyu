#!/usr/bin/env python3
"""Validate publication-critical article metadata."""
import datetime as dt
import json
import re
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit('Install validation dependencies: python3 -m pip install -r scripts/requirements.txt')


def read_article(path):
    source = path.read_text(encoding='utf-8')
    parts = re.split(r'^---[ \t]*$', source, maxsplit=2, flags=re.M)
    assert len(parts) == 3 and not parts[0].strip(), f'{path}: missing YAML front matter'
    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError as error:
        raise SystemExit(f'{path}: invalid YAML front matter: {error}')
    assert isinstance(metadata, dict), f'{path}: front matter must be a mapping'
    return metadata, parts[2], source


def read_date(metadata, key, path):
    value = metadata[key]
    assert isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), (
        f'{path}: quote {key} as YYYY-MM-DD'
    )
    return dt.date.fromisoformat(value)


root = Path(__file__).resolve().parents[1]
ids = {c['id'] for c in json.loads((root / '_data/companies.json').read_text())}
seen = set()
for path in sorted((root / '_articles').glob('*.md')):
    meta, body, source = read_article(path)
    required = {'title','company_id','period','published','updated','announcement',
                'rating','rating_date','rating_reason','summary','review_status'}
    assert required <= meta.keys(), f'{path.name}: missing {required-meta.keys()}'
    assert meta['company_id'] in ids, path
    key = (meta['company_id'], meta['period'])
    assert key not in seen, f'Duplicate company/period: {key}'
    seen.add(key)
    assert meta['rating'] in {'好調','横ばい','注意','未評価'}, path
    dates = {k: read_date(meta, k, path) for k in ('published','updated','announcement','rating_date')}
    assert dates['announcement'] <= dates['published'] <= dates['updated'], path
    assert dates['announcement'] <= dates['rating_date'] <= dates['updated'], path
    conclusions = meta.get('conclusions')
    assert (
        isinstance(conclusions, list)
        and len(conclusions) >= 3
        and all(isinstance(item, str) and item.strip() for item in conclusions)
    ), f'{path}: conclusions must contain at least three non-empty text items'
    assert 'https://' in body and '更新履歴' in body, path
    assert not re.search(r'AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN .*PRIVATE KEY', source), path
    print(f'PASS: {path.name} / {meta["rating"]} / {meta["rating_date"]}')
print(f'PASS: {len(seen)} unique earnings articles')
columns = sorted((root / '_columns').glob('*.md'))
for path in columns:
    meta, body, _ = read_article(path)
    assert {'title', 'published', 'updated', 'summary'} <= meta.keys(), f'{path.name}: missing column metadata'
    if 'company_id' in meta:
        cid = meta['company_id']
        assert cid in ids, f'{path.name}: unknown company_id {cid}'
    published = read_date(meta, 'published', path)
    updated = read_date(meta, 'updated', path)
    assert published <= updated, f'{path.name}: update before publication'
    assert '更新履歴' in body and 'https://' in body, f'{path.name}: missing history or source'
print(f'PASS: {len(columns)} columns with publication/revision dates and histories')

