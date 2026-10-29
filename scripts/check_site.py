#!/usr/bin/env python3
"""Check generated Jekyll output, fragments, navigation and dynamic counts."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
root = Path(__file__).resolve().parents[1]
site = root / '_site'
base = '/investment-tankyu'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links=[]; self.ids=set(); self.feed(text)
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if 'id' in d: self.ids.add(d['id'])
        for attr in ('href','src'):
            if attr in d: self.links.append(d[attr])
pages={p:Page(p.read_text()) for p in site.rglob('*.html')}
assert site/'index.html' in pages
for p, page in pages.items():
    text=p.read_text()
    assert not re.search(r'\{%|\{\{', text), f'Unrendered Liquid: {p}'
    for link in page.links:
        u=urlsplit(link)
        if u.scheme or u.netloc: continue
        target=unquote(u.path)
        if target.startswith(base+'/'): target=target[len(base)+1:]; dest=site/target
        elif target.startswith('/'): raise AssertionError(f'Wrong baseurl {p}: {link}')
        else: dest=p.parent/target if target else p
        if dest.is_dir(): dest=dest/'index.html'
        assert dest.exists(), f'Broken link {p}: {link}'
        if u.fragment and dest in pages:
            assert unquote(u.fragment) in pages[dest].ids, f'Broken anchor {p}: {link}'
home=(site/'index.html').read_text()
companies=json.loads((root/'_data/companies.json').read_text())
article_files=list((root/'_articles').glob('*.md'))
company_ids={re.search(r'^company_id: (.+)$',p.read_text(),re.M)[1] for p in article_files}
assert company_ids <= {c['id'] for c in companies}
assert len(re.findall('class="archive-item"',home))==min(3,len(article_files))
listing=(site/'companies.html').read_text()
for path in article_files:
    assert '/articles/'+path.stem+'.html' in listing, f'Missing company history: {path}'
for company in companies:
    assert 'id="company-'+company['id']+'"' in listing, f'Missing company anchor: {company["id"]}'
assert home.count('class="status">更新予定')==len(companies)-len(company_ids)
for path in article_files:
    dest=site/'articles'/(path.stem+'.html')
    assert dest in pages and '業績評価：' in dest.read_text(), path
for p in pages:
    assert not re.search(r'IDホールディングス|id-holdings|(?<!\d)4709(?!\d)',p.read_text()), p
print(f'PASS: Jekyll output, internal links/fragments/CSS, {len(companies)} companies / {len(article_files)} articles / {len(companies)-len(company_ids)} planned, exclusions')
