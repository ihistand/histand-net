<!-- Format: references/prd-format.md, "practices.md". -->

# Practices

## Sources

| ID | Title | Location | Covers | Read | Decision |
|---|---|---|---|---|---|
| S-01 | Vercel, "Static Configuration with vercel.json" | https://vercel.com/docs/project-configuration/vercel-json | `vercel.json` | 2026-11-17 | approved |
| S-02 | Google Search Central, "How to specify a canonical URL with rel="canonical" and other methods" | https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls | canonical URLs | 2026-11-17 | approved |
| S-03 | Google Search Central, "Introduction to robots.txt" | https://developers.google.com/search/docs/crawling-indexing/robots/intro | `robots.txt` | 2026-11-17 | approved |

## Practices

| ID | Source | Object (glob) | Applies to | Practice |
|---|---|---|---|---|
| P-01 | S-01 | `vercel.json` | code | Does `vercel.json` set `trailingSlash` to `true` or `false`? |
| P-02 | S-01 | `vercel.json` | code | Does `vercel.json` use none of the legacy properties `name`, `version`, `alias`, `scope`, `env`, `build.env` and `builds`? |
| P-03 | S-01 | `vercel.json` | code | Does `vercel.json` hold no `public` key? |
| P-04 | S-01 | `vercel.json` | code | Does no `source` or `destination` of a rewrite or redirect in `vercel.json` end in `.html`? |
| P-05 | S-01 | `vercel.json` | code | Does no rewrite `source` in `vercel.json` name a file the deploy holds? |
| P-06 | S-02 | `*.html` | code | Does each page's head hold a `rel="canonical"` link to that page's own URL? |
| P-07 | S-02 | `*.html` | code | Is every `rel="canonical"` href an absolute URL? |
| P-08 | S-02 | `*.html` | code | Is each page's `rel="canonical"` link inside its `head` element? |
| P-09 | S-02 | `sitemap.xml` | code | Does `sitemap.xml` list each page at the same URL as that page's `rel="canonical"` href? |
| P-10 | S-02 | `*.html` | code | Does every link from one page of the site to the other use that page's canonical URL? |
| P-11 | S-03 | `robots.txt` | code | Does `robots.txt` hold no `Disallow` line for any path that `.vercelignore` leaves out of the deploy? |
| P-12 | S-03 | `robots.txt` | code | Does `robots.txt` hold no `Disallow` line matching a file that a page of `contracts/pages.yaml` loads? |
