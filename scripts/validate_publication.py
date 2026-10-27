#!/usr/bin/env python3
"""公開前の除外ポリシー・銘柄参照・日程データ検証。標準ライブラリのみ。"""
import datetime as dt
import json
import re
from pathlib import Path
root = Path(__file__).resolve().parents[1]
policy = json.loads((root / '_data/publication_policy.json').read_text())
companies = json.loads((root / '_data/companies.json').read_text())
calendar = json.loads((root / '_data/earnings_calendar.json').read_text())
blocked_ids = set(policy['excluded_company_ids'])
blocked_tickers = set(policy['excluded_tickers'])
ids = {c['id'] for c in companies}
assert len(ids) == len(companies), '銘柄IDの重複'
assert not ids & blocked_ids, '公開対象外の銘柄ID'
assert not {c['ticker'] for c in companies} & blocked_tickers, '公開対象外のコード'
as_of = dt.date.fromisoformat(calendar['as_of'])
seen = set()
for event in calendar['events']:
    cid = event['company_id']
    assert cid in ids and cid not in blocked_ids, f'対象外または不明な銘柄: {cid}'
    assert cid not in seen, f'次回日程の重複: {cid}'
    seen.add(cid)
    status = event['status']
    assert status in {'scheduled', 'month_only', 'unknown', 'fund'}
    assert dt.date.fromisoformat(event['checked']) <= as_of
    if status == 'scheduled':
        assert dt.date.fromisoformat(event['date']) >= as_of, '確認基準日前の予定を要再確認'
        assert event['period'] and event['source'].startswith('https://')
    elif status == 'month_only':
        assert re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', event['month'])
        assert event['month'] >= calendar['as_of'][:7]
        assert event['source'].startswith('https://')
    else:
        assert not event.get('date'), '未確認の確定日付'
    if event.get('time'):
        assert 'JST' in event['time'], '日本時間を明記'
assert seen == ids, 'カレンダーの対象銘柄に漏れ'
for article in (root / '_articles').glob('*.md'):
    body = article.read_text()
    assert not re.search(r'IDホールディングス|id-holdings|(?<!\d)4709(?!\d)', body), f'対象外銘柄の公開記事: {article.name}'
print(f'PASS: 公開{len(companies)}銘柄、日付付き{sum(e["status"] == "scheduled" for e in calendar["events"])}件、除外ポリシー・参照・日付・時刻を確認')
