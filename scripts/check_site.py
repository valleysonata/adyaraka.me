"""Check shared navigation, homepage preservation and generated real-data integrity."""
import json
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


def check():
    social = ['https://github.com/valleysonata',
              'https://www.linkedin.com/in/adyaraka-banyu-langit-63456a317/',
              'https://www.researchgate.net/profile/Adyaraka-Banyu-Langit',
              'mailto:adyaraka.cs15@nycu.edu.tw']
    for name in PAGES:
        source = (ROOT/name).read_text(encoding='utf-8')
        page = Page(source)
        assert page.headers == 1, name
        assert all(link in page.links for link in ['/', '/about', '/projects', '/research/', '/news', *social]), name
        assert source.count('/assets/site.css') == 1
        assert source.count('/assets/site.js') == 1
        assert '<nav class="mac-nav' not in source
    home = (ROOT/'index.html').read_text(encoding='utf-8')
    assert 'open.spotify.com' not in home and 'np-embed' not in home
    assert '<h2 class="bio-header">Hi!</h2>' in home
    assert 'assets/ascii-art.svg' in home
    assert 'assets/BH_Accretion_Disk_Sim_360_1080.webm' in home
    assert 'Computer Science @ NYCU' in home
    assert home.index('bio-header') < home.index('id="github-title"') < home.index('id="featured-title"') < home.index('<footer')
    assert featured_projects() in home
    snapshot = json.loads((ROOT/'assets/github-contributions.json').read_text(encoding='utf-8'))
    days = [day for week in snapshot['weeks'] for day in week['contributionDays']]
    rendered = Page(home).days
    assert len(rendered) == len(days)
    assert sum(int(cell['data-count']) for cell in rendered) == snapshot['totalContributions']
    assert [cell['data-date'] for cell in rendered] == [day['date'] for day in days]
    assert sum(cell['tabindex'] == '0' for cell in rendered) == 1
    assert snapshot['source'] == 'https://api.github.com/graphql'
    print('PASS: six static headers and existing links; hero/ASCII preserved; Spotify absent; project reuse; real calendar snapshot/render integrity.')


if __name__ == '__main__':
    check()
