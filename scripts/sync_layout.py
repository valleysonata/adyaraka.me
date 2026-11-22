"""Render shared navigation, real contribution snapshot and existing project cards.

Output is committed HTML: Pages does not need a framework or JavaScript to serve it.
"""
import calendar
import hashlib
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'about.html', 'projects.html', 'news.html',
         'research/index.html', 'research/coffee-shop-operational-waste.html']


def plain(markup):
    return html.unescape(re.sub('<[^>]+>', '', markup)).strip()


def featured_projects():
    # The Projects page remains the source of truth; no duplicated project data.
    source = (ROOT/'projects.html').read_text(encoding='utf-8')
    cards = re.findall(r'<a class="project-card".*?</a>', source, re.S)[:3]
    assert len(cards) >= 2, 'Featured section needs at least two existing projects'
    output = []
    for card in cards:
        href = re.search(r'href="([^"]+)"', card)[1]
        image, alt = re.search(r'<img src="([^"]+)" alt="([^"]*)"', card).groups()
        title = plain(re.search(r'<h3\b[^>]*>(.*?)<span', card, re.S)[1])
        description = plain(re.search(r'<p class="card-desc"[^>]*>(.*?)</p>', card, re.S)[1])
        tags = re.search(r'<div class="card-tags">(.*?)</div>', card, re.S)[1]
        output.append(f'''<a class="featured-project reveal" href="{html.escape(href)}" target="_blank" rel="noreferrer">
  <img src="/{image}" alt="{html.escape(alt)}" loading="lazy" width="480" height="260">
  <div class="featured-project-body"><h3>{html.escape(title)}</h3><p>{html.escape(description)}</p><div class="featured-tags">{tags}</div></div>
</a>''')
    return '\n'.join(output)


def github_activity():
    data = json.loads((ROOT/'assets/github-contributions.json').read_text(encoding='utf-8'))
    weeks = data['weeks']
    cells, months = [], []
    last_month = None
    for column, week in enumerate(weeks, 1):
        for day in week['contributionDays']:
            parsed = date.fromisoformat(day['date'])
            if parsed.day <= 7 and parsed.month != last_month:
                months.append(f'<span style="grid-column:{column}">{calendar.month_abbr[parsed.month]}</span>')
                last_month = parsed.month
            count = day['contributionCount']
            label = f"{count:,} {'contribution' if count == 1 else 'contributions'} on {parsed.strftime('%B')} {parsed.day}, {parsed.year}"
            level = ['NONE','FIRST_QUARTILE','SECOND_QUARTILE','THIRD_QUARTILE','FOURTH_QUARTILE'].index(day['contributionLevel'])
            cells.append(f'<button class="gh-day" type="button" tabindex="-1" data-level="{level}" data-date="{parsed}" data-count="{count}" aria-label="{label}" style="grid-column:{column};grid-row:{day["weekday"] + 1}"></button>')
    cells[-1] = cells[-1].replace('tabindex="-1"', 'tabindex="0"')
    updated = date.fromisoformat(data['updated_at'][:10])
    return f'''<section class="home-section reveal" aria-labelledby="github-title">
  <div class="home-section-heading"><h2 id="github-title">GitHub</h2><a class="github-profile" href="https://github.com/valleysonata" target="_blank" rel="noreferrer" aria-label="valleysonata on GitHub"><svg width="17" height="17" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 .5a11.5 11.5 0 0 0-3.6 22.4c.6.1.8-.3.8-.6v-2c-3 .7-3.8-1.4-3.8-1.4-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 1.7 2.7 1.2 3.4.9.1-.7.4-1.2.7-1.5-2.5-.3-5.2-1.3-5.2-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.5.2 2.7.1 3 .8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.2 5.7.4.4.8 1 .8 2.1v3.1c0 .3.2.7.8.6A11.5 11.5 0 0 0 12 .5Z"/></svg><span>valleysonata</span><svg width="14" height="14" class="external-link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg></a></div>
  <div class="github-card">
    <p class="github-count"><strong>{data['totalContributions']:,}</strong> contributions in the last year</p>
    <div class="github-scroll" role="region" aria-label="GitHub contribution calendar; scroll horizontally on small screens" tabindex="0">
      <div class="github-calendar" style="--weeks:{len(weeks)}">
        <div class="github-months" aria-hidden="true">{''.join(months)}</div>
        <div class="github-body"><div class="github-weekdays" aria-hidden="true"><span>Mon</span><span>Wed</span><span>Fri</span></div><div class="github-grid" role="group" aria-label="Daily contributions; use arrow keys to explore">{''.join(cells)}</div></div>
        <div class="github-meta"><span>Updated <time datetime="{updated}">{updated.strftime('%b')} {updated.day}, {updated.year}</time> · GitHub</span><span class="github-legend" aria-label="Less to more contributions">Less <i></i><i></i><i></i><i></i><i></i> More</span></div>
      </div>
    </div>
  </div>
</section>'''


def sync():
    template = (ROOT/'templates/header.html').read_text(encoding='utf-8').strip()
    versions = {name: hashlib.sha256((ROOT/'assets'/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:12]
                for name in ('site.css', 'site.js')}
    for name in PAGES:
        path = ROOT/name
        source = path.read_text(encoding='utf-8')
        # One shared observer controls reveals; retain each page's other scripts.
        source = re.sub(r'    const reveals = document.querySelectorAll\(\'.reveal\'\);.*?(?=  </script>)', '', source, flags=re.S)
        favicon_version = hashlib.sha256((ROOT/'assets/favicon.svg').read_bytes()).hexdigest()[:12]
        source = re.sub(r'<link rel="icon"[^>]*>', f'<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg?v={favicon_version}">', source)
        # Retire the old nav-only CSS without disturbing page content styles.
        source = re.sub(r'<style>(.*?)</style>', lambda m: '<style>'+clean_css(m[1])+'</style>', source, flags=re.S)
        # Remove the previous in-content nav and its now-unused hover script.
        source = re.sub(r'\s*<nav class="mac-nav\b.*?</nav>', '', source, flags=re.S)
        source = re.sub(r'\s*const hl=document.getElementById\(\'mac-highlight\'\);.*?\n  </script>', '\n  </script>', source, flags=re.S)
        source = re.sub(r'    // primary nav.*?(?=    const hint =)', '', source, flags=re.S)
        active = '/research/' if name.startswith('research/') else '/' + name.removesuffix('.html')
        if name == 'index.html':
            active = '/'
        header = template.replace(f'href="{active}"', f'href="{active}" aria-current="page"', 1)
        if '<!-- site-header:start -->' in source:
            source = re.sub(r'<!-- site-header:start -->.*?<!-- site-header:end -->', lambda _: header, source, flags=re.S)
        else:
            source = source.replace('<body>', '<body>\n'+header, 1)
        if '/assets/site.css' not in source:
            source = source.replace('</head>', '  <link rel="stylesheet" href="/assets/site.css">\n  <script src="/assets/site.js" defer></script>\n</head>')
        # New markup must never load a previous deployment's CSS or JavaScript.
        # Normalize LF before hashing so Windows and Actions generate the same URL.
        for asset, version in versions.items():
            source = re.sub(r'(/assets/'+re.escape(asset)+r')(?:\?v=[a-f0-9]+)?(?=")',
                            lambda m: m[1]+'?v='+version, source)
        if name == 'index.html':
            source = source.replace('<body>', '<body class="home-page">', 1)
            source = re.sub(r'\s*<nav class="hero-links".*?</nav>', '', source, flags=re.S)
            source = re.sub(r'\s*<div class="np-embed-wrap">.*?</div>', '', source, flags=re.S)
            source = re.sub(r'\s*\.np-embed[^\n]*', '', source)
            section = '<!-- home-work:start -->\n' + github_activity() + f'''
<section class="home-section" aria-labelledby="featured-title">
  <div class="home-section-heading reveal"><h2 id="featured-title">Featured Projects</h2><a href="/projects">View all projects</a></div>
  <div class="featured-grid">{featured_projects()}</div>
</section>
<!-- home-work:end -->'''
            if '<!-- home-work:start -->' in source:
                source = re.sub(r'<!-- home-work:start -->.*?<!-- home-work:end -->', lambda _: section, source, flags=re.S)
            else:
                source = source.replace('    <footer', section+'\n\n    <footer', 1)
        path.write_text(source, encoding='utf-8', newline='\n')
    research_css = ROOT/'assets/research.css'
    research_css.write_text(clean_css(research_css.read_text(encoding='utf-8')), encoding='utf-8')


def clean_css(source):
    source = re.sub(r'[^{}]*\.(?:mac-nav|mac-links|mac-highlight|hero-links)[^{}]*\{[^{}]*\}', '', source)
    source = re.sub(r'@media[^{}]*\{\s*\}', '', source)
    return '\n'.join(line.rstrip() for line in source.splitlines()).rstrip()+'\n'


if __name__ == '__main__':
    sync()
