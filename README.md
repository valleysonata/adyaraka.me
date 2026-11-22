# adyaraka.me

## Layout and GitHub activity

The existing static site now shares a fixed header across all six content pages.
Edit `templates/header.html`, then run `python scripts/sync_layout.py` to update
the committed HTML. Shared styles and dropdown/calendar behavior are in
`assets/site.css` and `assets/site.js`. The native social dropdown and all
navigation links work without JavaScript.

The homepage's featured cards are rendered from the existing `projects.html`
cards by the same script. That page remains the project source of truth.
The hero currently tries the existing ASCII portrait beside a larger title;
the original black-hole video remains in `assets` for switching back. Original
hero social links, CV and research routes are retained. The scroll cue hides
below the top and returns on every trip back; it is never removed from the DOM.
The navigation's moving highlight handles pointer hover and keyboard focus;
portrait and highlight motion respect reduced-motion preferences.

The contribution calendar uses GitHub's GraphQL `contributionCalendar` for
`valleysonata`, including actual counts, dates and GitHub contribution levels.
The last successful response is stored in `assets/github-contributions.json`;
its date is displayed on the page. No credentials are shipped to visitors and
no third-party calendar service is required. Failed refreshes leave the dated
snapshot intact. Counts follow GitHub's contribution attribution and visibility
rules and can differ from raw commit counts.

To refresh locally with an authenticated GitHub CLI:

```sh
python scripts/refresh_github.py
python scripts/check_site.py
python scripts/check_research.py
node --check assets/site.js
```

`.github/workflows/refresh-contributions.yml` runs daily at 06:17 UTC and can be
run manually. It uses the repository's built-in Actions token, validates the
HTML, commits the refreshed snapshot and requests a build of the existing
branch-based GitHub Pages site. No framework or hosting migration is needed.
GitHub can delay scheduled runs or disable schedules on inactive repositories;
the visible update date makes stale data identifiable.

Personal website, served by GitHub Pages from `main` at `/`, with the custom domain in `CNAME` and HTTPS enforced. The site uses hand-written HTML, inline CSS and vanilla JavaScript; it has no framework, client-side router, package dependencies, or build/test command. GitHub Pages serves extensionless routes from `.html` files.

## Research

- `/research/` → `research/index.html` (the `/research` request redirects to this directory URL)
- `/research/coffee-shop-operational-waste` → `research/coffee-shop-operational-waste.html`
- `/research/coffee-shop-operational-waste.pdf` → the unchanged publisher PDF

Both research pages are static HTML, including their visible content, navigation, and metadata. JavaScript is not required. New styles are scoped to those pages in `assets/research.css`. The homepage links to the research listing, which links to the article and PDF. Each research HTML page uses its preferred HTTPS URL as its sole canonical, including when served through an HTML-file alias. The listing uses `/research/`; the article uses the extensionless URL. Do not add competing canonicals or a `research.html` route.

`robots.txt` allows crawling and advertises `sitemap.xml`. There was no sitemap generator; the small sitemap is maintained directly and includes the existing public pages and both research URLs. Add future papers to the listing and sitemap, each with a separate HTML page and PDF beside it.

### Bibliographic source and license

Verified on November 12, 2026 against the [publisher article](https://comserva.publikasiindonesia.id/index.php/comserva/article/view/3590), its Highwire metadata, and the [original PDF](https://comserva.publikasiindonesia.id/index.php/comserva/article/download/3590/2708/22448):

- Quantitative Analysis of Coffee Shop Operational Waste Using Python
- Adyaraka Banyu Langit; Rai Ikhsan Wiratama
- COMSERVA : Jurnal Penelitian dan Pengabdian Masyarakat, volume 6, issue 3, pages 145–155
- Published July 10, 2026; DOI `10.59141/comserva.v6i3.3590`

The publisher's visible publication date and `citation_date` both say July 10. Its `DC.Date.issued` field instead says July 8; this site follows the visible date and citation metadata consistently. The abstract is reproduced verbatim from the publisher's HTML, with whitespace in the second author's name normalized in author fields.

The publisher identifies the work as © 2026 the two authors, licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), which permits redistribution with attribution. The article page credits the authors and publisher, links to the original and license, and states that the PDF is unchanged. No PDF content, metadata, or layout has been rewritten. The original PDF is 11 searchable pages, 484572 bytes, with SHA-256:

```
fdfbc55b78e857e13e9db6d3690dba98505c3d8870c6ef13caa27dd5c24173e9
```

### Checks and deployment

Requires only Python 3. Standard library checks read HTML directly, without running JavaScript:

```sh
python scripts/check_research.py
```

This checks citation tags, the complete publisher abstract, JSON-LD, canonicals, homepage/listing/article links, the unchanged PDF signature/hash/size, robots.txt, and sitemap XML. No existing project test suite or local build process preceded these changes.

Deploy by pushing the checked source to the configured Pages branch:

```sh
git add index.html research assets/research.css robots.txt sitemap.xml scripts/check_research.py README.md
git commit -m "Add static research pages and scholarly metadata"
git push origin main
```

Wait for the GitHub Pages build and deployment to succeed. Inspect with GitHub's repository Actions tab or:

```sh
gh api repos/valleysonata/valleysonata.github.io/pages/builds/latest
python scripts/check_research.py --base-url https://adyaraka.me
```

The HTTP check verifies unauthenticated 200 responses, HTML/PDF content types, absence of an HTTP `noindex`, consistent canonicals through HTML-file aliases, the served PDF bytes, and all content checks above. GitHub Pages owns HTTP-to-HTTPS and repository-domain redirects; confirm those when changing domain settings.

These pages follow [Google Scholar's inclusion guidelines](https://scholar.google.com/intl/en/scholar/inclusion.html), including one abstract per HTML page, individual author tags, a same-directory `citation_pdf_url`, and simple HTML discovery links. Indexing and timing remain Google's decision. Scholar may group this copy with the publisher version rather than show it separately.

After deployment, the domain owner can submit `https://adyaraka.me/sitemap.xml` in Google Search Console and request indexing for both research HTML URLs. Search Console helps regular Google Search; it does not guarantee or directly submit a paper to Scholar.
