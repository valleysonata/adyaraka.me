"""Check shared navigation, homepage preservation and generated real-data integrity."""
import argparse
import json
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from sync_layout import PAGES, featured_projects

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links, self.days, self.headers = [], [], 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.links.append(attrs.get('href'))
        if tag == 'header' and attrs.get('class') == 'site-header':
            self.headers += 1
        if tag == 'button' and attrs.get('class') == 'gh-day':
            self.days.append(attrs)
        for attribute in ('src', 'href'):
            value = attrs.get(attribute, '')
            if value.startswith('/assets/'):
                assert (ROOT/value.lstrip('/')).is_file(), value


def check(base_url=None):
    def read(name):
        if not base_url:
            return (ROOT/name).read_text(encoding='utf-8')
        route = '/' if name == 'index.html' else '/research/' if name == 'research/index.html' else '/'+name.removesuffix('.html') if name.endswith('.html') else '/'+name
        with urllib.request.urlopen(base_url.rstrip('/')+route, timeout=30) as response:
            assert response.status == 200, route
            return response.read().decode('utf-8')

    social = ['https://github.com/valleysonata',
              'https://www.linkedin.com/in/adyaraka-banyu-langit-63456a317/',
              'https://www.researchgate.net/profile/Adyaraka-Banyu-Langit',
              'mailto:adyaraka.cs15@nycu.edu.tw']
    for name in PAGES:
        source = read(name)
        page = Page(source)
        assert page.headers == 1, name
        assert all(link in page.links for link in ['/', '/about', '/projects', '/research/', '/news', *social]), name
        assert source.count('/assets/site.css') == 1
        assert source.count('/assets/site.js') == 1
        assert '<nav class="mac-nav' not in source
    home = read('index.html')
    assert 'open.spotify.com' not in home and 'np-embed' not in home
    assert '<h2 class="bio-header">Hi!</h2>' in home
    assert 'assets/ascii-art.svg' in home
    assert 'assets/BH_Accretion_Disk_Sim_360_1080.webm' in home
    assert 'Computer Science @ NYCU' in home
    assert home.index('bio-header') < home.index('id="github-title"') < home.index('id="featured-title"') < home.index('<footer')
    assert featured_projects() in home
    snapshot = json.loads(read('assets/github-contributions.json'))
    days = [day for week in snapshot['weeks'] for day in week['contributionDays']]
    rendered = Page(home).days
    assert len(rendered) == len(days)
    assert sum(int(cell['data-count']) for cell in rendered) == snapshot['totalContributions']
    assert [cell['data-date'] for cell in rendered] == [day['date'] for day in days]
    assert sum(cell['tabindex'] == '0' for cell in rendered) == 1
    assert snapshot['source'] == 'https://api.github.com/graphql'
    assert '.site-header' in read('assets/site.css')
    assert 'github-calendar' in read('assets/site.js')
    print('PASS: six static headers and existing links; hero/ASCII preserved; Spotify absent; project reuse; real calendar snapshot/render integrity.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url')
    check(parser.parse_args().base_url)
