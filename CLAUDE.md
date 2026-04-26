# DirectionalStats.bib — Agent Instructions

## Repository purpose

Curated BibTeX bibliography on Directional Statistics (~1,780 entries). Primary file: `DirectionalStats.bib`.

---

## Automatic bib-cleaning agent

When asked to clean, check, validate, or audit the bibliography, run
`bibcheck.py` and act on its output.

### Quick check (read-only, no changes)

```bash
python bibcheck.py
```

Use `--summary` for a compact count-only view.

### Auto-fix safe issues

```bash
python bibcheck.py --fix
# Review DirectionalStats.bib.fixed, then:
mv DirectionalStats.bib.fixed DirectionalStats.bib
```

Auto-fixable issues (E4, W5) are always safe to apply without human review.

### After fixing, re-tidy formatting

```bash
./bibtex-tidy-master/bin/bibtex-tidy \
  --sort=type,-year,author,key \
  --no-escape --align=13 --curly --tab \
  --duplicates=citation \
  --sort-fields=title,subtitle,author,year,journal,fjournal,booktitle,booksubtitle,publisher,address,series,volume,number,pages,editor,edition,note,url,doi \
  --no-remove-dupe-fields \
  DirectionalStats.bib
```

---

## Issue codes

| Code | Severity | Meaning | Action |
|------|----------|---------|--------|
| E1 | Error | Duplicate citation key | Fix manually — keep the more complete entry |
| E2 | Error | Same DOI in two entries | Investigate — usually one entry is wrong or a duplicate |
| E3 | Error | Missing required field | Add the field |
| E4 | Error | DOI has URL prefix | Auto-fix with `--fix` |
| E5 | Error | Field duplicated within entry | Remove duplicate |
| W1 | Warning | Key year differs from year field by >2 | Check whether the key or the year is wrong |
| W2 | Warning | Same journal abbreviation → different fjournal | Unify the fjournal value |
| W3 | Warning | Same fjournal → different journal abbreviation | Unify the journal abbreviation |
| W4 | Warning | Article has journal but no fjournal | Add the full journal name |
| W5 | Warning | Page range with single dash | Auto-fix with `--fix` |
| W6 | Warning | arXiv entry with non-arXiv DOI | Use `10.48550/arXiv.XXXX.XXXXX` format |
| I1 | Info | Key year ± 1–2 years | Usually expected (preprint → published); skip unless clearly wrong |
| I2 | Info | Legacy BF-format DOI | Verify by visiting `https://doi.org/<doi>`; remove if 404 |
| I3 | Info | Article missing DOI | Look up the DOI and add it |
| I4 | Info | Non-placeholder field is empty | Investigate and fill in or remove |
| I5 | Info | Key has no year component | Rename key to include year |

---

## BibTeX conventions

### Entry field order

All entries must use this exact field order (bibtex-tidy enforces it):

```
title, subtitle, author, year, journal, fjournal, booktitle, booksubtitle,
publisher, address, series, volume, number, pages, editor, edition, note, url, doi
```

### Citation key format

`LastnameYYYY` — first author's surname + 4-digit publication year.
Suffixes `a`, `b`, … disambiguate multiple works by the same author in the same year.

Preprints often use the submission year in the key; the `year` field holds the
final publication year. A mismatch up to 2 years (I1) is normal and expected.

### Journal fields

Every `@article` must have both:
- `journal` — abbreviated name (e.g., `Ann. Stat.`)
- `fjournal` — full name (e.g., `Annals of Statistics`)

For arXiv preprints:
- `journal = {arXiv:XXXX.XXXXX}` and `fjournal = {arXiv:XXXX.XXXXX}`
- `doi = {10.48550/arXiv.XXXX.XXXXX}`

### Sorting

Entries are sorted: by type → inverse chronological order → alphabetical by
first author surname. `bibtex-tidy` handles this automatically.

### Special characters

Use LaTeX encoding throughout: `\'e`, `\"{o}`, `\c{c}`, etc.
Do **not** use Unicode directly. The file header declares `% Encoding: UTF-8`
but all non-ASCII characters should be represented in LaTeX notation.

### DOIs

- Bare DOI only — no `https://doi.org/` prefix.
- All lowercase preferred, though mixed case is acceptable.
- Legacy Springer BF-format DOIs (`10.1007/bf…`) often do not resolve for
  publications from the 1980s–1990s. Verify before removing.

## Files

| File | Purpose |
|------|---------|
| `DirectionalStats.bib` | Main bibliography (edit this) |
| `bibcheck.py` | Quality checker / auto-fixer |
| `bibclean.sh` | Runs bibtex-tidy to reformat and sort |
| `processing.R` | R utilities: journal consistency, missing DOIs |
| `other-bibs/` | Derived subset files (do not edit directly) |
| `DOI_CORRECTIONS_NEEDED.md` | Open DOI issues requiring manual review |
