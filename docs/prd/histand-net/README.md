<!-- prd-toolkit:start -->
# histand-net — product requirements

This folder is the living PRD for **histand-net**: the requirements that say what it does, kept in
step with the code. The code implements this PRD, and a change in behaviour starts here, not in
the code. It is maintained with prd-toolkit, a Claude Code plugin (see [../README.md](../README.md) to set it up).

Version 1.0.0 · Approved · Owner: Ivan Histand · Updated 2026-11-17

## What this PRD covers

> histand.net is a static site of two pages: a page about the Histand family name at `https://histand.net/`, and Ivan Histand's name card at `https://ivan.histand.net/`. It is plain HTML served by Vercel with no build step, and eight alias domains, each with its `www`, redirect to `https://histand.net/`.

## Areas

| Area | Adoption | File |
|---|---|---|
| site | adopted | [features/site.md](features/site.md) |

## What is in this folder

| Path | Holds |
|---|---|
| `prd.md` | The overview: goals, glossary, architecture, the requirement index, open questions, changelog |
| `features/` | One file per area: requirements (`FR-nnn`) and their acceptance criteria (`AC-nnn.n`) |
| `test-cases/` | The test cases for each criterion (`T-nnn.n`), which the tests cite |
| `contracts/` | The interfaces the code must match: commands, configuration, schemas, APIs |
| `testing.md` | How the tests are run, at which level and gate |
| `errors.md` | The error ledger: every bug, its class and its fix (`E-nnn`) |
| `operations.md` | Environments and the deploy runbook |
| `nfr.md` | Non-functional requirements (`NFR-nnn`) |
| `adoption.md` | Which areas of the existing code are under this PRD, and their state |

## Reading and changing it

- Read `prd.md`, then the area you care about. With the plugin: `/prd-toolkit:prd-status` for
  where every requirement stands, `/prd-toolkit:prd-context <area>` for one area,
  `/prd-toolkit:prd-publish` for a readable page.
- Don't edit these files by hand. A change in behaviour starts with `/prd-toolkit:prd-change` and
  is built with `/prd-toolkit:prd-build`; a bug starts with `/prd-toolkit:prd-error`. Lint and the
  git hooks check every commit.
<!-- prd-toolkit:end -->
