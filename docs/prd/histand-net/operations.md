<!-- Format: references/prd-format.md, "operations.md". -->

# Operations

## Environments

| Environment | URL | Production |
|---|---|---|
| production | https://histand.net | yes |

## Runbook

1. Merge to main (actor: human) (env: production)
   Do: merge the reviewed branch into `main` on GitHub; Vercel deploys every push to `main` to production (README.md)
   Check: the Vercel deployment of the merge commit shows Ready, and the owner replies "deployed" [ASSUMPTION A-08: confirmed by the owner 2026-11-16: the README says pushes to `main` deploy to production through the Vercel project `histand-net`, and Vercel reports each deployment of a push]
2. Smoke on production (actor: agent) (env: production)
   Run: tests smoke

## Secrets

- None in the repository: the site reads no secret, and Vercel's connection to the repository holds the deploy access.
