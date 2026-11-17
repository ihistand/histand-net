<!-- Format: references/prd-format.md, "Requirement blocks". -->

# Site

<!-- Area `site`: the pages (family.html and ivan.html), the hosting configuration (vercel.json, robots.txt, sitemap.xml, site.webmanifest, .gitignore, .vercelignore) and README.md. -->

### UJ-01 A reader looks up the Histand family name
Status: live (since 1.0.0)
Flow: 1. Someone looking up the Histand family name in Doylestown and Bucks County opens
      https://histand.net/, or an alias domain that redirects there (FR-006), and gets the family
      page (FR-001) → 2. reads its history under "Coming to Doylestown", "Places" and "William L.
      Histand, photographer" (FR-014) → 3a. follows a link of its Sources list to that source
      (FR-014)  3b. follows "ivan.histand.net" under "This site" to the name card (FR-014, FR-002).
      Empty state: none, the family page is static and shows the same content to every reader.
      Failure state: `/family.html` and `/family` redirect to `/` (AC-003.1, AC-004.1), and a path
      the site does not serve gets Vercel's default 404 page (§2 Out of scope)
[ASSUMPTION A-10: confirmed by the owner 2026-11-17: the journey is read from the confirmed requirements FR-004, FR-006 and FR-014,
  the approved FR-001, FR-002 and FR-003, and the personas of §2]
Traces: FR-001, FR-002, FR-003, FR-004, FR-006, FR-014

### UJ-02 A visitor finds the software Ivan Histand builds and how to reach him
Status: live (since 1.0.0)
Flow: 1. Someone looking for the software Ivan Histand builds opens https://ivan.histand.net/ and
      gets the name card (FR-002), or opens https://histand.net/ivan and is redirected there
      (FR-005) → 2. reads the Projects and Work lists and follows a link to a project or an
      employer (FR-018) → 3a. reaches him through a link of the Contact paragraph: an email
      address, GitHub or LinkedIn (FR-018)  3b. follows "histand.net" under "Elsewhere" to the
      family page (FR-018, FR-001).
      Empty state: none, the name card is static and shows the same content to every visitor.
      Failure state: `/ivan` redirects to `https://ivan.histand.net/` on both hosts (AC-005.1,
      AC-005.3), and a path the site does not serve gets Vercel's default 404 page (§2 Out of
      scope)
[ASSUMPTION A-11: confirmed by the owner 2026-11-17: the journey is read from the confirmed requirement FR-018, the approved FR-001,
  FR-002 and FR-005, and the personas of §2]
Traces: FR-001, FR-002, FR-005, FR-018

### FR-001 Serve the family page at the root of histand.net
Status: approved
Source: vercel.json:220 @6d67871
Flow: 1. A request for `/` arrives on a host other than `ivan.histand.net` → 2. the last rewrite of
      `vercel.json`, which has no host condition, serves `/family` in its place → 3. clean URLs
      serve `family.html` for `/family`
Acceptance (EARS):
- AC-001.1 When a client sends GET `/` to https://histand.net, the site shall answer 200 with
  content type `text/html; charset=utf-8` and the family page, whose `title` element reads
  "Histand — a family name in Doylestown, Bucks County".
- AC-001.2 The repository root shall hold the file `family.html` and no file `index.html`.
- AC-001.3 The repository's `README.md` shall describe the site as it is: it shall hold the texts
  `family.html`, `https://histand.net/` and `308`, and none of the texts `index.html`,
  `Single-page` and `301`.
Errors: -
Edge cases: Vercel checks the files before the rewrites, so an `index.html` at the root would be
  served for `/` on every host and the host rewrite of FR-002 would never run (commit 0636ed7)
  → AC-001.2; the README still describes the single page `index.html` and a 301 (E-005, open;
  Q-04, answered by the owner 2026-11-16: "yes, update README.md"; the 308 per E-002) → AC-001.3
Tests: T-001.1 [smoke], T-001.2 [integration], T-001.3 [integration]  (test-cases/site.yaml)
Traces: `hosting:root-elsewhere`; `pages:family`; E-005

### FR-002 Serve the name card at the root of ivan.histand.net
Status: approved
Source: vercel.json:210 @6d67871
Flow: 1. A request for `/` arrives on `ivan.histand.net` → 2. the first rewrite of `vercel.json`
      serves `/ivan` in its place → 3. clean URLs serve `ivan.html` for `/ivan`
Acceptance (EARS):
- AC-002.1 When a client sends GET `/` to https://ivan.histand.net, the site shall answer 200 with
  content type `text/html; charset=utf-8` and the name card, whose `title` element reads
  "Ivan Histand".
- AC-002.2 The `rewrites` array of `vercel.json` shall hold exactly two rewrites, in this order:
  first `/` to `/ivan` with the one condition that the host is `ivan.histand.net`, then `/` to
  `/family` with no condition.
- AC-002.3 The repository's `README.md` shall hold the texts `ivan.html` and
  `https://ivan.histand.net/`.
Errors: -
Edge cases: the rewrite with the host condition must come first, because Vercel applies the first
  rewrite that matches; `/ivan` requested on `ivan.histand.net` itself redirects to the root of
  that host, so the name card has one URL there (E-001) → AC-005.3; the README, which names
  neither `ivan.html` nor `https://ivan.histand.net/` today (E-005, open; Q-04) → AC-002.3
Tests: T-002.1 [smoke], T-002.2 [integration], T-002.3 [integration]  (test-cases/site.yaml)
Traces: `hosting:root-on-ivan-host`, `hosting:root-elsewhere`; `pages:ivan`; E-005

### FR-003 Serve pages at clean URLs
Status: approved
Source: vercel.json:2 @6d67871
Acceptance (EARS):
- AC-003.1 When a client requests `/family.html` on https://histand.net, the site shall answer 308
  with a `Location` header of `/family`.
- AC-003.2 The top-level `cleanUrls` key of `vercel.json` shall be `true`.
Errors: -
Edge cases: `/family` itself then redirects to `/` (FR-004); on `ivan.histand.net`, `/ivan.html`
  redirects to `/ivan`, and `/ivan` there redirects to the root of that host instead of serving
  the name card a second time (E-001) → AC-005.3
Tests: T-003.1 [smoke], T-003.2 [integration]  (test-cases/site.yaml)
Traces: `hosting:clean-urls`

### FR-004 Redirect /family to the root
Status: live (since 1.0.0)
Source: vercel.json:5 @6d67871
Acceptance (EARS):
- AC-004.1 When a client requests `/family` on https://histand.net, the site shall answer 308 with
  a `Location` header of `/`.
- AC-004.2 The `redirects` array of `vercel.json` shall hold the redirect of `/family` to `/`,
  permanent, with no `has` condition.
- AC-004.3 When a client requests `/family` on https://ivan.histand.net, the site shall answer 308
  with a `Location` header of `/`, where that host serves the name card (FR-002).
Errors: -
Edge cases: the redirect has no host condition, so `/family` on `ivan.histand.net` lands on the
  name card; the owner confirmed 2026-11-16 that this is intended ("/family should redirect to the
  name card", Q-01) → AC-004.3
Tests: T-004.1 [smoke], T-004.2 [integration], T-004.3 [smoke]  (test-cases/site.yaml)
Traces: `hosting:family-to-root`

### FR-005 Redirect /ivan to the root of ivan.histand.net
Status: approved
Source: vercel.json:10 @6d67871
Acceptance (EARS):
- AC-005.1 When a client requests `/ivan` on https://histand.net, the site shall answer 308 with a
  `Location` header of `https://ivan.histand.net/`.
- AC-005.2 The `redirects` array of `vercel.json` shall hold the redirect of `/ivan` to
  `https://ivan.histand.net/`, permanent, with the one condition that the host is `histand.net`.
- AC-005.3 When a client requests `/ivan` on https://ivan.histand.net, the site shall answer 308
  with a `Location` header of `https://ivan.histand.net/`.
Errors: -
Edge cases: `/ivan.html` on `histand.net` first answers 308 to `/ivan` (FR-003), then this rule;
  `/ivan` on `ivan.histand.net` answers 200 with the name card today, a second URL for it there
  (E-001, open; the owner, 2026-11-16: "ivan.histand.net/ivan should redirect to
  ivan.histand.net") → AC-005.3
Tests: T-005.1 [smoke], T-005.2 [integration], T-005.3 [smoke]  (test-cases/site.yaml)
Traces: `hosting:ivan-to-subdomain`, `hosting:ivan-on-subdomain-to-root`; E-001

### FR-006 Redirect www.histand.net and every alias domain to the apex
Status: live (since 1.0.0)
Source: vercel.json:21 @6d67871
  vercel.json:28 @6d67871, vercel.json:29 @6d67871
Acceptance (EARS):
- AC-006.1 When a request for any path arrives on `www.histand.net`, or on one of the alias domains
  `histand.com`, `histand.org`, `histands.com`, `histands.net`, `histands.org`, `anilak.net`,
  `hinault.net` and `ivanivan.net`, or on the `www` host of one of them, the site shall answer 308
  with a `Location` header that is `https://histand.net` followed by the request's path and, when
  the request has one, its query string.
- AC-006.2 The `redirects` array of `vercel.json` shall hold, for each of those 17 hosts, one
  redirect of every path (source `/:path(.*)`) to `https://histand.net/:path`, permanent, with the
  one condition that the host is that host, and shall hold 19 redirects in all.
Errors: -
Edge cases: `/ivan` on an alias host goes to `https://histand.net/ivan` and then to the name card
  (FR-005), two hops; the status is 308, which `"permanent": true` gives (vercel.json:29): the
  owner confirmed 2026-11-16 that 308 is correct (E-002); the query string is kept, which the
  owner confirmed intended 2026-11-16 (Q-02), though Vercel keeps it with no line of
  `vercel.json` saying so
Tests: T-006.1 [smoke], T-006.2 [smoke], T-006.3 [integration]  (test-cases/site.yaml)
Traces: `hosting:www-histand-net-to-apex` and the 16 other `hosting:*-to-apex` rules

### FR-007 Let every crawler crawl the site and name the sitemap
Status: live (since 1.0.0)
Source: robots.txt:1 @6d67871
  robots.txt:2 @6d67871, robots.txt:4 @6d67871
Acceptance (EARS):
- AC-007.1 When a client sends GET `/robots.txt` to https://histand.net, the site shall answer 200
  with content type `text/plain; charset=utf-8` and a body of exactly four lines,
  `User-agent: *`, `Allow: /`, an empty line and `Sitemap: https://histand.net/sitemap.xml`, each
  ending in a newline.
- AC-007.2 The committed `robots.txt` shall hold exactly the four lines of AC-007.1, each ending in
  a newline.
Errors: -
Edge cases: `ivan.histand.net` serves the same file
Tests: T-007.1 [smoke], T-007.2 [integration]  (test-cases/site.yaml)
Traces: `hosting:crawl-all`

### FR-008 List both pages in the sitemap
Status: live (since 1.0.0)
Source: sitemap.xml:2 @6d67871
  sitemap.xml:4 @6d67871, sitemap.xml:8 @6d67871
Acceptance (EARS):
- AC-008.1 The committed `sitemap.xml` shall be a `urlset` element in the namespace
  `http://www.sitemaps.org/schemas/sitemap/0.9` whose `url` children are exactly two, in this
  order: `loc` `https://histand.net/` with `lastmod` `2026-09-17`, and `loc`
  `https://ivan.histand.net/` with `lastmod` `2026-09-17`.
- AC-008.2 When a client sends GET `/sitemap.xml` to https://histand.net, the site shall answer 200
  with content type `application/xml` and a body equal to the committed `sitemap.xml`.
Errors: -
Edge cases: -
Tests: T-008.1 [integration], T-008.2 [smoke]  (test-cases/site.yaml)
Traces: `hosting:crawl-all` (its `sitemap`); `pages:family`, `pages:ivan`

### FR-009 Publish a web app manifest
Status: live (since 1.0.0)
Source: site.webmanifest:3 @6d67871
  site.webmanifest:2 @6d67871, site.webmanifest:4 @6d67871, site.webmanifest:5 @6d67871,
  site.webmanifest:6 @6d67871, site.webmanifest:7 @6d67871, site.webmanifest:8 @6d67871
Acceptance (EARS):
- AC-009.1 The committed `site.webmanifest` shall be a JSON object with `name` "Ivan Histand",
  `short_name` "Histand",
  `start_url` `/`, `display` `browser`, `background_color` `#f5f1ea`, `theme_color` `#f5f1ea`, and
  an `icons` array of exactly two icons, in this order: `src` `/icon-192.png` with `sizes`
  `192x192` and `type` `image/png`, then `src` `/icon-512.png` with `sizes` `512x512` and `type`
  `image/png`.
- AC-009.2 When a client sends GET `/site.webmanifest` to https://histand.net, the site shall
  answer 200 with content type `application/manifest+json; charset=utf-8` and a body that parses
  as the manifest of AC-009.1.
Errors: -
Edge cases: the manifest's `name` is "Ivan Histand" although `/` on `histand.net` is the family
  page, and the family page links it (FR-019): the owner confirmed 2026-11-16 that both are
  intended ("Keep as is.", E-003) → AC-009.1; the icon files belong to area `icons`
Tests: T-009.1 [integration], T-009.2 [smoke]  (test-cases/site.yaml)
Traces: FR-019

### FR-010 Keep local state out of the repository, and files that are not the site off the deploy
Status: approved
Source: .gitignore:1 @6d67871
  .gitignore:2 @6d67871, .gitignore:3 @6d67871
Acceptance (EARS):
- AC-010.1 The repository's `.gitignore` shall ignore `.vercel`, `.DS_Store` in any folder, and
  every file or folder whose name starts with `.env`, and shall not ignore the site's committed
  files.
- AC-010.2 When a client requests, on https://histand.net, a committed file that is not part of
  the site (`README.md`, or any file under `scripts/`, `docs/` or `tests/`), the site shall answer
  404.
- AC-010.3 The repository root shall hold a `.vercelignore` file, which leaves the files of
  AC-010.2 out of the deploy.
Errors: -
Edge cases: `.env.local`, which `vercel link` writes (commit 08b4093) → AC-010.1; today every
  committed file is deployed, and production answers 200 for
  `https://histand.net/scripts/make-assets.py` (E-006, open); the owner answered 2026-11-16 "yes,
  the deploy should leave out files that are not served" (Q-05) → AC-010.2, AC-010.3
Tests: T-010.1 [integration], T-010.2 [smoke], T-010.3 [integration]  (test-cases/site.yaml)
Traces: E-006

### FR-011 Identify the family page in its head
Status: live (since 1.0.0)
Source: family.html:2 @6d67871
  family.html:4 @6d67871, family.html:5 @6d67871, family.html:6 @6d67871, family.html:7 @6d67871,
  family.html:8 @6d67871, family.html:12 @6d67871
Acceptance (EARS):
- AC-011.1 The family page shall declare, on its `html` element, `lang="en"`; on a `meta`
  element, `charset="utf-8"`; the title "Histand — a family name in Doylestown, Bucks County"; the
  `meta` elements named `viewport` "width=device-width, initial-scale=1", `description`
  "Histand, also written Hiestand: a Mennonite family name long associated with Doylestown and
  Bucks County, Pennsylvania." and `robots` "index, follow"; and the canonical address
  `https://histand.net/`, on the `link` element whose `rel` is `canonical`.
Errors: -
Edge cases: the page declares each of these once (family.html:2-12)
Tests: T-011.1 [integration]  (test-cases/site.yaml)
Traces: `pages:family`

### FR-012 Give the family page its own share card
Status: live (since 1.0.0)
Source: family.html:14 @6d67871
  family.html:15 @6d67871, family.html:16 @6d67871, family.html:17 @6d67871,
  family.html:18 @6d67871, family.html:19 @6d67871, family.html:20 @6d67871,
  family.html:21 @6d67871, family.html:22 @6d67871, family.html:23 @6d67871,
  family.html:25 @6d67871, family.html:26 @6d67871, family.html:27 @6d67871,
  family.html:28 @6d67871
Acceptance (EARS):
- AC-012.1 The family page shall declare, on `meta` elements keyed by their `property` attribute,
  `og:type` "website", `og:site_name` "Histand", an `og:title` equal to its title, `og:description`
  "A Mennonite family name long associated with Doylestown and Bucks County, Pennsylvania.",
  `og:url` `https://histand.net/`, `og:locale` "en_US", `og:image`
  `https://histand.net/og-family.png`, `og:image:width` "1200", `og:image:height` "630" and
  `og:image:alt` "Histand — a Mennonite family name in Doylestown, Bucks County, PA"; and, on
  `meta` elements keyed by their `name` attribute, `twitter:card` "summary_large_image",
  `twitter:title` equal to its title, `twitter:description` equal to its `og:description`, and
  `twitter:image` `https://histand.net/og-family.png`.
- AC-012.2 When a client sends HEAD `https://histand.net/og-family.png`, the site shall answer 200
  with content type `image/png`.
Errors: -
Edge cases: the image file itself belongs to area `images`
Tests: T-012.1 [integration], T-012.2 [smoke]  (test-cases/site.yaml)
Traces: `pages:family`

### FR-013 Describe the family page as a schema.org WebPage
Status: live (since 1.0.0)
Source: family.html:43 @6d67871
  family.html:44 @6d67871, family.html:45 @6d67871, family.html:46 @6d67871,
  family.html:47 @6d67871, family.html:48 @6d67871, family.html:49 @6d67871,
  family.html:50 @6d67871
Acceptance (EARS):
- AC-013.1 The family page's JSON-LD (its `script` element of type `application/ld+json`) shall
  be an object with `@context` `https://schema.org`, `@type` `WebPage`, a `name` equal to the page
  title, a `url` equal to the canonical address `https://histand.net/`, a `description` equal to
  the page's `description` meta element, `inLanguage` `en-US`, and an `about` object of `@type`
  `Thing` with `name` "Histand family" and `description` "A Mennonite family of Doylestown
  Township, Bucks County, Pennsylvania".
Errors: -
Edge cases: the comment above the element says the schema claims nothing the page does not show
  (family.html:39-42)
Tests: T-013.1 [integration]  (test-cases/site.yaml)
Traces: `pages:family`

### FR-014 Show the family history, its sources and a link to the name card
Status: live (since 1.0.0)
Source: family.html:227 @6d67871
  family.html:232 @6d67871, family.html:245 @6d67871, family.html:251 @6d67871,
  family.html:268 @6d67871, family.html:269 @6d67871, family.html:275 @6d67871,
  family.html:278 @6d67871
Acceptance (EARS):
- AC-014.1 The family page shall hold one `h1` element, reading "Histand", and five `h2` elements,
  reading, in document order, "Coming to Doylestown", "Places", "William L. Histand,
  photographer", "Sources" and "This site".
- AC-014.2 The family page's Sources list (the first `ul` element after the `h2` "Sources") shall
  hold three `li` items, in this order: a link "Mennonite Heritage Center" to
  `https://mhep.org/new-acquisition-joshua-histand-and-enos-gehman-papers/`, a link "Mennonite
  Heritage Center" to
  `https://mhep.org/from-sandy-ridge-and-pine-run-to-main-street-and-cross-keys-the-photography-of-william-histand-of-doylestown/`
  and a link "Bucks County Herald" to
  `https://www.buckscountyherald.com/opinion/history-lives-samuel-and-rebecca-histand-house/article_4d711655-2aba-5eb9-9053-f5d3143ebf7c.html`,
  each item with a description (a `span` element with class `desc`) that is not empty.
- AC-014.3 The family page's This site paragraph (the first `p` element after the `h2` "This
  site") shall hold exactly one link, "ivan.histand.net" to `https://ivan.histand.net/`.
Errors: -
Edge cases: each Sources item is an `li` holding a `span` with class `head`, which holds the link,
  then the `span` with class `desc` (family.html:270-272)
Tests: T-014.1 [integration], T-014.2 [integration], T-014.3 [integration]  (test-cases/site.yaml)
Traces: `pages:family`

### FR-015 Identify the name card in its head
Status: live (since 1.0.0)
Source: ivan.html:2 @6d67871
  ivan.html:4 @6d67871, ivan.html:5 @6d67871, ivan.html:6 @6d67871, ivan.html:7 @6d67871,
  ivan.html:8 @6d67871, ivan.html:9 @6d67871, ivan.html:13 @6d67871
Acceptance (EARS):
- AC-015.1 The name card shall declare, on its `html` element, `lang="en"`; on a `meta` element,
  `charset="utf-8"`; the title "Ivan Histand"; the `meta` elements named `viewport`
  "width=device-width, initial-scale=1", `description` "Ivan Histand — software I build and how to
  reach me.", `author` "Ivan Histand" and `robots` "index, follow"; and the canonical address
  `https://ivan.histand.net/`, on the `link` element whose `rel` is `canonical`.
Errors: -
Edge cases: the page declares each of these once (ivan.html:2-13)
Tests: T-015.1 [integration]  (test-cases/site.yaml)
Traces: `pages:ivan`

### FR-016 Give the name card its share card
Status: live (since 1.0.0)
Source: ivan.html:15 @6d67871
  ivan.html:16 @6d67871, ivan.html:17 @6d67871, ivan.html:18 @6d67871, ivan.html:19 @6d67871,
  ivan.html:20 @6d67871, ivan.html:21 @6d67871, ivan.html:22 @6d67871, ivan.html:23 @6d67871,
  ivan.html:24 @6d67871, ivan.html:26 @6d67871, ivan.html:27 @6d67871, ivan.html:28 @6d67871,
  ivan.html:29 @6d67871
Acceptance (EARS):
- AC-016.1 The name card shall declare, on `meta` elements keyed by their `property` attribute,
  `og:type` "website", `og:site_name` "Ivan Histand", `og:title` "Ivan Histand", `og:description`
  "Software I build and how to reach me.", `og:url` `https://ivan.histand.net/`, `og:locale`
  "en_US", `og:image` `https://ivan.histand.net/og.png`, `og:image:width` "1200",
  `og:image:height` "630" and `og:image:alt` "Ivan Histand — data engineering, and tools for the
  people who do it."; and, on `meta` elements keyed by their `name` attribute, `twitter:card`
  "summary_large_image", `twitter:title` "Ivan Histand", `twitter:description` "Software I build
  and how to reach me." and `twitter:image` `https://ivan.histand.net/og.png`.
- AC-016.2 When a client sends HEAD `https://ivan.histand.net/og.png`, the site shall answer 200
  with content type `image/png`.
Errors: -
Edge cases: the image file itself belongs to area `images`
Tests: T-016.1 [integration], T-016.2 [smoke]  (test-cases/site.yaml)
Traces: `pages:ivan`

### FR-017 Describe the name card's subject as a schema.org Person
Status: approved
Source: ivan.html:46 @6d67871
  ivan.html:48 @6d67871, ivan.html:49 @6d67871, ivan.html:50 @6d67871, ivan.html:51 @6d67871,
  ivan.html:52 @6d67871, ivan.html:54 @6d67871, ivan.html:55 @6d67871, ivan.html:56 @6d67871,
  ivan.html:66 @6d67871, ivan.html:67 @6d67871
Acceptance (EARS):
- AC-017.1 The name card's JSON-LD (its `script` element of type `application/ld+json`) shall be
  an object with `@context` `https://schema.org`, `@type` `Person`, `name` "Ivan Histand", `url`
  `https://ivan.histand.net/`, `email` `mailto:ivan@histand.net`, a `description` equal to the
  text of the page's `p` element with class `lede`, a `worksFor` object of `@type` `Organization`
  with `url` `https://acuantia.com` whose `parentOrganization` is an object of `@type`
  `Organization` with `url` `https://rotoplas.com`, and `sameAs` holding exactly
  `https://github.com/ihistand`.
- AC-017.2 The name card's visible text (the text of its `body` element) shall hold each of the
  Person's `jobTitle`, `worksFor.name` and `worksFor.parentOrganization.name` values, and its
  `email` value without the `mailto:` prefix.
- AC-017.3 The name card's JSON-LD `knowsAbout` shall hold exactly, in this order, "Data
  engineering", "SQL", "BigQuery", "Dataform" and "PostgreSQL".
- AC-017.4 The name card's visible text shall hold `PostgreSQL`, and shall not hold `Postgres` as
  a word of its own.
Errors: -
Edge cases: the comment above the element says every claim of the schema is one the page itself
  makes (ivan.html:40-45); today `knowsAbout` also holds "Developer tools", and the page says
  "Postgres" (E-004, open; the owner, 2026-11-16: "Postgres should be changed to PostgreSQL" and
  "Drop Developer Tools") → AC-017.3, AC-017.4
Tests: T-017.1 [integration], T-017.2 [integration], T-017.3 [integration], T-017.4 [integration]  (test-cases/site.yaml)
Traces: `pages:ivan`; commits 9ad46dc, b408abb; E-004

### FR-018 Show projects, work, the family page and contact links on the name card
Status: live (since 1.0.0)
Source: ivan.html:246 @6d67871
  ivan.html:247 @6d67871, ivan.html:249 @6d67871, ivan.html:251 @6d67871, ivan.html:259 @6d67871,
  ivan.html:261 @6d67871, ivan.html:265 @6d67871, ivan.html:267 @6d67871, ivan.html:270 @6d67871,
  ivan.html:271 @6d67871
Acceptance (EARS):
- AC-018.1 The name card shall hold one `h1` element, reading "Ivan Histand"; a `p` element with
  class `lede` reading "Data engineering, and tools for the people who do it."; and four `h2`
  elements, reading, in document order, "Projects", "Work", "Elsewhere" and "Contact".
- AC-018.2 The name card's Projects list (the first `ul` element after the `h2` "Projects") shall
  hold six `li` items, in this order, each with an icon (an `img` element with `alt=""`, `width`
  "18" and `height` "18"), a link and a description (a `span` element with class `desc`) that is
  not empty: "SQLAnvil" to `https://sqlanvil.com` with icon `/icons/sqlanvil.svg`, "Incise" to
  `https://incise.dev` with `/icons/incise.png`, "Checklists.io" to `https://checklists.io` with
  `/icons/checklists.png`, "ListAnvil" to `https://listanvil.com` with `/icons/listanvil.png`,
  "Graver" to `https://graver.dev` with `/icons/graver.png`, and "Claude Skills" to
  `https://github.com/ihistand/claude-skills` with `/icons/claude-skills.png`.
- AC-018.3 The name card's Work list (the first `ul` element after the `h2` "Work") shall hold two
  `li` items, in this order, each with an icon, a link and a description that is not empty, as in
  AC-018.2: "Acuantia" to `https://acuantia.com` with icon `/icons/acuantia.png`, then "Rotoplas"
  to `https://rotoplas.com` with icon `/icons/rotoplas.png`.
- AC-018.4 The name card's Elsewhere list (the first `ul` element after the `h2` "Elsewhere")
  shall hold one `li` item: a link "histand.net" to `https://histand.net/`, with a description that
  is not empty and no icon.
- AC-018.5 The name card's Contact paragraph (the `p` element with class `contact`) shall hold
  exactly four links, in this order: "ivan@histand.net" to `mailto:ivan@histand.net`,
  "ihistand@acuantia.com" to `mailto:ihistand@acuantia.com`, "github.com/ihistand" to
  `https://github.com/ihistand`, and "linkedin.com/in/ihistand" to
  `https://www.linkedin.com/in/ihistand/`.
Errors: -
Edge cases: each list item is an `li` holding a `span` with class `head`, which holds the icon
  and the link, then the `span` with class `desc` (ivan.html:251-267); each Projects description,
  the "Claude Skills" entry's included, is current as written: the owner confirmed it intended
  2026-11-16 (Q-03) → AC-018.2
Tests: T-018.1 [integration], T-018.2 [integration], T-018.3 [integration], T-018.4 [integration], T-018.5 [integration]  (test-cases/site.yaml)
Traces: `pages:ivan`; the icon files belong to area `icons`

### FR-019 Link the favicon, touch icon and manifest from both pages
Status: live (since 1.0.0)
Source: family.html:34 @6d67871
  family.html:35 @6d67871, family.html:36 @6d67871, family.html:37 @6d67871,
  ivan.html:35 @6d67871, ivan.html:36 @6d67871, ivan.html:37 @6d67871, ivan.html:38 @6d67871
Acceptance (EARS):
- AC-019.1 The family page and the name card shall each hold exactly four `link` elements whose
  `rel` is `icon`, `apple-touch-icon` or `manifest`, in this order: `rel="icon"` with `href`
  `/favicon.ico` and `sizes` "32x32"; `rel="icon"` with `type` `image/svg+xml` and an `href` that
  starts with `data:image/svg+xml,`; `rel="apple-touch-icon"` with `href` `/apple-touch-icon.png`;
  and `rel="manifest"` with `href` `/site.webmanifest`.
- AC-019.2 When a client sends HEAD `/favicon.ico`, `/apple-touch-icon.png` or `/site.webmanifest`
  to https://histand.net or to https://ivan.histand.net, the site shall answer 200.
Errors: -
Edge cases: the icon files themselves belong to area `icons`
Tests: T-019.1 [integration], T-019.2 [integration], T-019.3 [smoke]  (test-cases/site.yaml)
Traces: `pages:family`, `pages:ivan`; FR-009

### FR-020 Load nothing from another host and run no script
Status: live (since 1.0.0)
Source: ivan.html:251 @6d67871
  family.html:43 @6d67871, ivan.html:46 @6d67871
Acceptance (EARS):
- AC-020.1 The family page and the name card shall each give every `img` element's `src`, and the
  `href` of every `link` element whose `rel` is `icon`, `apple-touch-icon`, `manifest` or
  `stylesheet`, as a path that starts with one `/` and not with `//`, or as a `data:` address; and
  the text of each page's `style` elements shall hold neither `url(` nor `@import`.
- AC-020.2 The family page and the name card shall each hold exactly one `script` element, whose
  `type` is `application/ld+json` and which has no `src`.
Errors: -
Edge cases: `og:image`, `twitter:image` and the canonical address are absolute addresses that
  link previews and search engines read; the page does not load them → outside AC-020.1; commit
  6bdb31a: "This page makes no external requests and that is worth keeping"
Tests: T-020.1 [integration], T-020.2 [integration], T-020.3 [integration], T-020.4 [integration]  (test-cases/site.yaml)
Traces: `pages:family`, `pages:ivan`

### FR-021 Follow the reader's light or dark scheme
Status: live (since 1.0.0)
Source: family.html:9 @6d67871
  family.html:10 @6d67871, family.html:11 @6d67871, ivan.html:10 @6d67871, ivan.html:11 @6d67871,
  ivan.html:12 @6d67871
Acceptance (EARS):
- AC-021.1 The family page and the name card shall each declare the `meta` element named
  `color-scheme` "light dark"; exactly two `meta` elements named `theme-color`, in this order,
  `#f5f1ea` for the `media` "(prefers-color-scheme: light)" and `#15130f` for the `media`
  "(prefers-color-scheme: dark)"; and, in the text of their first `style` element, the light
  colours `:root { --bg: #f5f1ea; --ink: #1c1a16;` and the dark colours
  `@media (prefers-color-scheme: dark) { :root { --bg: #15130f; --ink: #ece6da;`.
Errors: -
Edge cases: each page holds one `style` element, in its head (family.html:59, ivan.html:78)
Tests: T-021.1 [integration], T-021.2 [integration]  (test-cases/site.yaml)
Traces: `pages:family`, `pages:ivan`

### FR-022 Animate the background wash, and stop it under reduced motion
Status: live (since 1.0.0)
Source: family.html:111 @6d67871
  ivan.html:130 @6d67871
Acceptance (EARS):
- AC-022.1 The family page and the name card shall each hold, in the text of their first `style`
  element, the declarations `animation: drift-a 54s ease-in-out infinite alternate;` and
  `animation: drift-b 73s ease-in-out infinite alternate, breathe 97s ease-in-out infinite alternate;`.
- AC-022.2 While the reader's system asks for reduced motion, the family page and the name card
  shall stop the wash: the text of their first `style` element shall hold
  `@media (prefers-reduced-motion: reduce) { body::before, body::after { animation: none; } body::after { opacity: 0.8; } }`.
Errors: -
Edge cases: the first declaration is in the `body::before` rule and the second in the
  `body::after` rule (ivan.html:142-159, family.html:123-140); commit 6bdb31a says only
  transform and opacity animate
Tests: T-022.1 [integration], T-022.2 [integration], T-022.3 [integration], T-022.4 [integration]  (test-cases/site.yaml)
Traces: `pages:family`, `pages:ivan`
