<!-- Format: references/prd-format.md, "errors.md".
Entry lines in order: Detected, Classification, Confirmed, Touches, Evidence (at most 20 lines, continuation lines indented two spaces), Diagnosis, Resolution, Recurrence of. -->

# Error ledger

### E-001 The name card answers 200 at a second URL, ivan.histand.net/ivan
Detected: 2026-11-16, adoption extract of site (vercel.json:10 @6d67871)
Classification: code bug
Touches: FR-002, FR-003, FR-005
Evidence: read-only requests to production, 2026-11-16:
  $ curl -sI -A prd-smoke https://ivan.histand.net/ivan
  HTTP/2 200
  $ curl -sI -A prd-smoke https://histand.net/ivan
  HTTP/2 308
  location: https://ivan.histand.net/
Diagnosis: the redirect of `/ivan` (vercel.json:10-18) holds only on the host `histand.net`, and
  clean URLs (vercel.json:2) serve `/ivan` from `ivan.html` on every other host, so
  `https://ivan.histand.net/ivan` answers 200 with the whole name card, and
  `https://ivan.histand.net/ivan.html` answers 308 to it. Commit d7cfb18 says "histand.net/ivan
  redirects to the subdomain so the page has one URL"; on `ivan.histand.net` the page has two,
  `/` and `/ivan`. The page's canonical address limits the harm for search engines.
Resolution: open
Recurrence of: -

### E-002 Alias-domain redirects answer 308 where the README says 301
Detected: 2026-11-16, adoption extract of site (vercel.json:29 @6d67871)
Classification: code bug
Confirmed: 2026-11-16, "Confirm the class (form)"
Touches: FR-006
Evidence: read-only requests to production, 2026-11-16:
  $ curl -sI -A prd-smoke https://histand.com/
  HTTP/2 308
  location: https://histand.net/
Diagnosis: every alias rule of `vercel.json` (lines 20-206) sets `"permanent": true`, which Vercel
  answers with 308; all 17 hosts answered 308. README.md:6 says "every other domain 301-redirects
  to `https://histand.net/`", and the workspace notes beside this repository say the same. No
  commit message names 308. Both statuses are permanent; which one the site promises is the
  owner's to say.
Resolution: open
Recurrence of: -

### E-003 The manifest linked from the family page is named "Ivan Histand"
Detected: 2026-11-16, adoption extract of site (site.webmanifest:2 @6d67871)
Classification: code bug
Touches: FR-009
Diagnosis: `site.webmanifest` gives `"name": "Ivan Histand"` with `start_url` `/`. The family page
  links it (family.html:37), and on `histand.net` `/` is now the family page, whose sibling
  metadata names the site "Histand" (`og:site_name`, family.html:15). Commit d7cfb18 says the
  apex "needed its own share image — the card's says 'Ivan Histand'". The manifest has not changed
  since b07d475 (2026-08-22), when the site was the name card alone.
Resolution: open
Recurrence of: -

### E-004 The name card's Person schema claims topics the page does not show
Detected: 2026-11-16, adoption extract of site (ivan.html:67 @6d67871)
Classification: code bug
Touches: FR-017
Diagnosis: the comment above the JSON-LD (ivan.html:40-45) says "Every claim here is one the page
  itself makes" and "anything added here has to be added to the page first". Its `knowsAbout`
  list (ivan.html:67-74) holds "PostgreSQL" and "Developer tools"; the page's visible text says
  "Postgres" and nowhere "Developer tools". The same comment says the title and employer are
  there "because the Projects list states them"; since b408abb they are in the Work list.
Resolution: open
Recurrence of: -
