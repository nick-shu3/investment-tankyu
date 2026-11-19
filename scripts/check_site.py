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
    if company.get('research_url'):
        route = company['research_url']
        assert base+route in listing, f'Missing research link: {company["id"]}'
        research = site/route.lstrip('/')
        assert research in pages, f'Missing research page: {route}'
        for folder, url_folder in (('_articles', 'articles'), ('_columns', 'columns')):
            for source in (root/folder).glob('*.md'):
                if re.search(r'^company_id: '+re.escape(company['id'])+r'$', source.read_text(), re.M):
                    url = base+'/'+url_folder+'/'+source.stem+'.html'
                    assert url in research.read_text(), f'Missing research history: {source}'
                    assert base+route in (site/url_folder/(source.stem+'.html')).read_text(), f'Missing research backlink: {source}'
assert home.count('class="status">更新予定')==len(companies)-len(company_ids)
for path in article_files:
    dest=site/'articles'/(path.stem+'.html')
    assert dest in pages and '業績評価：' in dest.read_text(), path
for path in (root/'_columns').glob('*.md'):
    dest=site/'columns'/(path.stem+'.html')
    assert dest in pages, f'Missing column page: {path}'
    assert '/columns/'+path.stem+'.html' in home, f'Missing column link: {path}'
documents = {}
for folder, route in (('_articles', 'articles'), ('_columns', 'columns')):
    for path in (root/folder).glob('*.md'):
        front = path.read_text().split('---', 2)[1]
        dates = {key: re.search(r'^'+key+r': "(\d{4}-\d{2}-\d{2})"$', front, re.M)[1]
                 for key in ('published', 'updated')}
        documents[f'{base}/{route}/{path.stem}.html'] = (dates, route)
updates = re.findall(r'<li class="update-item">(.*?)</li>', home, re.S)
assert len(updates) == min(5, len(documents)), 'Missing recent update records'
assert home.index('id="updates"') < home.index('id="archive"'), 'Updates must precede the archive'
rendered_dates = []
rendered_links = []
for record in updates:
    link = re.search(r'<a href="([^"]+)"', record)[1]
    date = re.search(r'<time datetime="([^"]+)"', record)[1]
    assert link in documents, f'Unknown update record: {link}'
    dates, route = documents[link]
    assert date == dates['updated'], f'Stale update date: {link}'
    assert ('改訂' if dates['updated'] > dates['published'] else '新規公開') in record, f'Wrong update status: {link}'
    assert ('コラム' if route == 'columns' else '決算分析') in record, f'Wrong document type: {link}'
    rendered_dates.append(date)
    rendered_links.append(link)
assert len(set(rendered_links)) == len(rendered_links), 'Duplicate update records'
assert rendered_dates == sorted(rendered_dates, reverse=True), 'Updates are not in revision-date order'
latest = max((dates['updated'], dates['published']) for dates, _ in documents.values())
assert (rendered_dates[0], documents[rendered_links[0]][0]['published']) == latest, 'Newest publication/revision is missing'
print('PASS: recent records include current publication/revision dates, types and article links')
for p in pages:
    assert not re.search(r'IDホールディングス|id-holdings|(?<!\d)4709(?!\d)',p.read_text()), p
print(f'PASS: Jekyll output, internal links/fragments/CSS, {len(companies)} companies / {len(article_files)} articles / {len(companies)-len(company_ids)} planned, exclusions')

