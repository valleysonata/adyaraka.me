#!/usr/bin/env python3
"""Check static research content, or unauthenticated production HTTP responses."""
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://adyaraka.me'
ARTICLE = '/research/coffee-shop-operational-waste'
TITLE = 'Quantitative Analysis of Coffee Shop Operational Waste Using Python'
AUTHORS = ['Adyaraka Banyu Langit', 'Rai Ikhsan Wiratama']
PDF_SHA256 = 'fdfbc55b78e857e13e9db6d3690dba98505c3d8870c6ef13caa27dd5c24173e9'


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.meta, self.links, self.canonicals = {}, [], []
        self.text, self.headings, self.structured, self.abstract = [], [], [], []
        self.in_head = self.in_h1 = self.in_json = self.in_abstract = False
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'head':
            self.in_head = True
        if tag == 'h1':
            self.in_h1 = True
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.in_json = True
        if tag == 'p' and a.get('class') == 'abstract':
            self.in_abstract = True
        if tag == 'meta' and self.in_head:
            key = a.get('name', a.get('property'))
            self.meta.setdefault(key, []).append(a.get('content'))
        if tag == 'link' and a.get('rel') == 'canonical' and self.in_head:
            self.canonicals.append(a['href'])
        if tag == 'a':
            self.links.append(a.get('href'))

    def handle_endtag(self, tag):
        if tag == 'head':
            self.in_head = False
        if tag == 'h1':
            self.in_h1 = False
        if tag == 'script':
            self.in_json = False
        if tag == 'p':
            self.in_abstract = False

    def handle_data(self, data):
        if self.in_json:
            self.structured.append(data)
        elif not self.in_head:
            self.text.append(data)
        if self.in_h1:
            self.headings.append(data)
        if self.in_abstract:
            self.abstract.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', help='Check deployed HTTP without running JavaScript')
    args = parser.parse_args()

    def fetch(path):
        if args.base_url:
            request = urllib.request.Request(args.base_url.rstrip('/') + path,
                                            headers={'User-Agent': 'ResearchAccessibilityCheck/1.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                assert response.status == 200, (path, response.status)
                assert 'noindex' not in response.headers.get('X-Robots-Tag', '').lower()
                expected = 'application/pdf' if path.endswith('.pdf') else (
                    'text/html' if path.endswith('/') or path.endswith('.html') or '.' not in path else None)
                if expected:
                    assert response.headers.get_content_type() == expected, (path, response.headers)
                return response.read()
        local = ROOT / ('index.html' if path == '/' else path.lstrip('/'))
        if path.endswith('/'):
            local = local / 'index.html' if path != '/' else local
        if not local.suffix:
            local = local.with_suffix('.html')
        return local.read_bytes()

    docs = {p: Document(fetch(p).decode('utf-8')) for p in ['/research/', ARTICLE]}
    for path, doc in docs.items():
        assert doc.canonicals == [ORIGIN + path], (path, doc.canonicals)
        assert doc.meta['robots'] == ['index, follow']
        assert len(doc.meta['description']) == 1
        assert doc.meta['og:url'] == [ORIGIN + path]
        if args.base_url:
            alias = Document(fetch(path + 'index.html' if path.endswith('/') else path + '.html').decode('utf-8'))
            assert alias.canonicals == doc.canonicals
    article = docs[ARTICLE]
    expected = {'citation_title': [TITLE], 'citation_author': AUTHORS,
                'citation_publication_date': ['2026/07/10'],
                'citation_journal_title': ['COMSERVA : Jurnal Penelitian dan Pengabdian Masyarakat'],
                'citation_volume': ['6'], 'citation_issue': ['3'],
                'citation_firstpage': ['145'], 'citation_lastpage': ['155'],
                'citation_doi': ['10.59141/comserva.v6i3.3590'],
                'citation_issn': ['2798-5210'], 'citation_language': ['en'],
                'citation_pdf_url': [ORIGIN + ARTICLE + '.pdf'],
                'citation_abstract_html_url': [ORIGIN + ARTICLE]}
    for key, value in expected.items():
        assert article.meta[key] == value, (key, article.meta.get(key))
    assert article.headings == [TITLE]
    visible = ' '.join(article.text)
    assert all(name in visible for name in AUTHORS)
    abstract = ''.join(article.abstract)
    assert hashlib.sha256(abstract.encode('utf-8')).hexdigest() == '73590094637920a87af7590c69c3ef9b17a37b11aaf9c910e0fe2fd8cb52d3a8', 'Publisher abstract changed'
    data = json.loads(''.join(article.structured))
    assert data['@type'] == 'ScholarlyArticle'
    assert data['headline'] == TITLE and data['abstract'] == abstract
    assert [a['name'] for a in data['author']] == AUTHORS
    assert data['datePublished'] == '2026-07-10'
    assert data['encoding']['contentUrl'] == expected['citation_pdf_url'][0]
    assert data['license'] in article.links
    homepage = Document(fetch('/').decode('utf-8'))
    assert '/research/' in homepage.links
    assert ARTICLE in docs['/research/'].links
    assert ARTICLE + '.pdf' in docs['/research/'].links
    assert ARTICLE + '.pdf' in article.links
    payload = fetch(ARTICLE + '.pdf')
    assert payload.startswith(b'%PDF-') and b'%%EOF' in payload[-1024:]
    assert len(payload) < 5_000_000
    assert hashlib.sha256(payload).hexdigest() == PDF_SHA256, 'Original PDF bytes changed'
    robots = fetch('/robots.txt').decode('utf-8').replace('\r\n', '\n')
    assert 'User-agent: *\nAllow: /' in robots
    assert 'Disallow:' not in robots
    assert 'Sitemap: ' + ORIGIN + '/sitemap.xml' in robots
    sitemap = ET.fromstring(fetch('/sitemap.xml'))
    urls = [e.text for e in sitemap.findall('{*}url/{*}loc')]
    assert len(urls) == len(set(urls))
    assert all(ORIGIN + p in urls for p in docs)
    print('PASS: raw HTML, citation tags, JSON-LD, canonical aliases, discovery links,')
    print('      original PDF hash/signature/size, robots.txt, and XML sitemap.')
    print('Mode:', args.base_url or 'local static files (no build step or JavaScript required)')


if __name__ == '__main__':
    main()
