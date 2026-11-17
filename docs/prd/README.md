<!-- prd-toolkit:start -->
# Product requirements

Each folder here is a living PRD: the requirements for one system in this repository, kept in
step with its code. Code implements its PRD; a change in behaviour starts in the PRD.

| PRD | Version | Status | Covers |
|---|---|---|---|
| [histand-net](histand-net/) | 1.0.0 | Approved | histand.net is a static site of two pages: a page about the Histand family name at `https://histand.net/`, and Ivan Histand's name card at `https://ivan.histand.net/`. |

## How it works

- Each area of a system has requirements (`FR-nnn`); each requirement has acceptance criteria
  (`AC-nnn.n`), and each criterion has test cases (`T-nnn.n`).
- Tests cite the test cases they prove, and commits cite the requirements they implement
  (`Refs: FR-012`), so a change can be traced from the PRD to the code and back.
- Bugs are recorded in each PRD's `errors.md` before they are fixed.
- Lint, the git hooks and CI check that the PRD, the tests and the code stay in step.

## Getting started

- Install the prd-toolkit plugin for Claude Code: https://github.com/PRDAnvil/prd-toolkit/tree/main/prd-toolkit
- Once per clone: `.prd-toolkit/prd hooks install docs/prd/<slug>`
- Then see each PRD's README.
<!-- prd-toolkit:end -->
