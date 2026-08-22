# histand.net

Single-page name card for Ivan Histand. Plain HTML, no build step, hosted on Vercel.

- `index.html` — the page. Edit the text directly.
- `vercel.json` — every other domain 301-redirects to `https://histand.net/`.
- Deploy: Vercel project `histand-net` (team `badgeretl`); pushes to `main` deploy to production.

## Domains

`histand.net` is canonical. These redirect to it (apex and `www`):

`histand.com`, `histand.org`, `histands.com`, `histands.net`, `histands.org`,
`anilak.net`, `hinault.net`, `ivanivan.net`

DNS for all of them lives in Route 53: apex `A 76.76.21.21`, `www CNAME cname.vercel-dns.com`.
Mail records on these zones are unrelated to this site — don't touch them when editing DNS.

To add a domain: attach it to the Vercel project, add the two DNS records, and add a redirect
rule for both the apex and `www` hostnames in `vercel.json`.
