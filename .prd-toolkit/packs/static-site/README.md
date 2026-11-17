# static-site 0.1.0

Static sites: the pages a site serves and the rules its host serves them by.

This prd-toolkit pack was written from two adopted PRDs of this kind:

- A: `prdanvil-com` 1.0.1, in the `prdanvil_com` repository (`docs/prd/prdanvil-com/`)
- B: `histand-net` 1.0.0, in the `histand-net` repository (`docs/prd/histand-net/`)

Every item below is one that `prd pack compare` marked `both`: the two PRDs hold it word for word.
The owner decided each one. Nothing here comes from anywhere but those two PRDs, apart from the
four header keys: the name and the description (the owner's), `version: 0.1.0`, and the `toolkit`
range of the built-in packs (`>=0.8.0,<0.9`, from prd-toolkit's `packs/service/pack.yaml`).

## Where each part came from

### Contract types

| Type | Files | Validator | Mark | PRD line |
|---|---|---|---|---|
| `pages` | `contracts/pages.yaml` | `uv run --quiet --script ${PACK}/validate_pages.py` | both | `prdanvil-com/prd.md` §7 row `pages` (line 99); `histand-net/prd.md` §7 row `pages` (line 99) |
| `hosting` | `contracts/hosting.yaml` | `uv run --quiet --script ${PACK}/validate_hosting.py` | both | `prdanvil-com/prd.md` §7 row `hosting` (line 100); `histand-net/prd.md` §7 row `hosting` (line 100) |

Each PRD's section 7 row runs `uv run --quiet --script ../../../scripts/prd/validate_<type>.py`.
`validate_pages.py` and `validate_hosting.py` here are those repositories' `scripts/prd/` files,
copied unchanged. The two repositories' copies are byte for byte the same (`cmp` exit 0 for each),
so there was no validator to choose between. The pack's command is the PRDs' command with the file
path replaced by `${PACK}/<file>`.

### Target kinds

`pages: pages` and `hosting: hosting`, both marked `both`. They are in the pack because their types
are. The comparison counted 19 `pages` and 9 `hosting` test cases in A, and 35 `pages` and 16
`hosting` in B.

### Levels

Both are marked `both`, from each PRD's `testing.md` Levels rows (lines 9 and 10). Neither has a
timeout, so none is written.

| Level | Command | Environment | Gate |
|---|---|---|---|
| `integration` | `uv run --with pytest==8.3.4 --with pyyaml==6.0.2 pytest -p no:cacheprovider tests/integration --tb=short` | local | build |
| `smoke` | `uv run --with pytest==8.3.4 --with pyyaml==6.0.2 pytest -p no:cacheprovider tests/smoke --tb=short` | production | deploy |

### Harness

These nine slots are marked `both`, with the text each PRD's `testing.md` Harness gives:

| Slot | Line in A's `testing.md` | Line in B's `testing.md` |
|---|---|---|
| Lifecycle | 14 | 14 |
| Environment switch | 15 | 15 |
| Database access | 16 | 16 |
| Persistent environments | 19 | 19 |
| Layout | 20 | 20 |
| Fixtures | 22 | 22 |
| Browser identity | 23 | 23 |
| Leaks | 27 | 36 |
| Acceptance | 28 | 37 |

The Lifecycle text names the host: "production is always served by Vercel". The owner chose to
include it.

The other seven Harness slots differ between the two PRDs. The owner left all seven out of the
pack, so each PRD keeps its own text:

- Tools on the runner
- Clean state
- HTTP requests
- Assertions
- Waits
- Effects
- Written rules and their citations

### Standards

Both PRDs have none, so the pack writes no `standards` key.

### Skills

All four rows are marked `both`, from each PRD's `prd.md` §6 (lines 87 to 90):

| Activity | Skill |
|---|---|
| plans | `superpowers:writing-plans` |
| reviewing a change before merge | `code-review` |
| checking a change works before calling it done | `superpowers:verification-before-completion` |
| work on the pages' HTML and CSS | `frontend-design:frontend-design` |

### Vocabulary

The pack's vocabulary is `[]`. The comparison found 104 candidate words used by both PRDs'
requirements. The owner put none of them in.

### builder-tests

`builder-tests: none` is set because neither PRD's Levels has a `unit` row.

## Samples

Each sample is a copy of a real contract file of PRD A with one line removed:

- `samples/pages/bad.yaml` copies `prdanvil-com`'s `contracts/pages.yaml`. The `canonical:` line
  of page `home` is removed. The validator requires `canonical` ("canonical  required").
- `samples/hosting/bad.yaml` copies `prdanvil-com`'s `contracts/hosting.yaml`. The `to:` line of
  rule `www-to-apex` (rule `redirect`) is removed. The validator requires `to` for that rule.

Both validators look up the repository root as the nearest folder above the contract file that has
a `.git`. Inside this plugin, that root is the plugin's own checkout, and it holds none of a site's
files (`index.html`, `vercel.json`, `robots.txt`, …). So a sample is also refused for naming files
that are missing here, not only for its named break. Those other lines are not the break the
sample is meant to show.

## To-do list

None of these items is drafted. Each one names the files a person would start from.

1. **Shared harness helpers.** The pack ships none. Neither repository has a test support module
   or a fixture file: each test file holds its own helpers, as both PRDs' Tools on the runner slots
   say. The HTML-tree reader of the Assertions slots and the smoke HTTP client of the HTTP requests
   slots are in these files:
   - `prdanvil_com`: `tests/integration/test_site.py` and `tests/smoke/test_site.py`
   - `histand-net`: `tests/integration/test_site.py` and `tests/smoke/test_site.py`
2. **Clarify questions for this kind of site.** An interview for a new static site would ask these
   (no `clarify.md` is written). Start from:
   - each PRD's `prd.md` §12 (A line 160, B line 161) and §13 (line 178 in both)
   - each PRD's `contracts/pages.yaml` and `contracts/hosting.yaml`
3. **Rules for a skill for this kind of site.** No skill is written. Start from:
   - each PRD's `prd.md` §5 (line 79, which says `None`) and the §6 rows (lines 87 to 90)
   - each PRD's `testing.md` Harness (A lines 12 to 29, B lines 12 to 38)
   - the seven Harness slots each PRD keeps (listed above)
