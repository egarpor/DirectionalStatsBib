#!/usr/bin/env python3
"""
bibcheck.py — DirectionalStats.bib quality checker.

Scans a BibTeX file for formatting inconsistencies, missing fields,
duplicate entries, and other quality issues. No external dependencies.

Usage:
    python bibcheck.py [--bib FILE] [--fix] [--summary]

Options:
    --bib FILE    Path to .bib file (default: DirectionalStats.bib)
    --fix         Write auto-fixed copy to FILE.fixed
    --summary     Print only issue counts per code, not individual entries

Checks performed:
  E1  Duplicate citation keys
  E2  Duplicate DOI values across entries
  E3  Missing required fields for entry type
  E4  DOI field contains URL prefix (should be bare DOI)   [auto-fix]
  E5  Same field name appears twice within one entry
  W1  Key year differs from year field by more than 2 years
  W2  Same journal abbreviation maps to different fjournal values
  W3  Same fjournal maps to different journal abbreviations
  W4  @article has 'journal' but no 'fjournal'
  W5  Page range uses single dash instead of double dash   [auto-fix]
  W6  arXiv journal entry with non-arXiv DOI format
  I1  Key year differs from year field by 1–2 years (preprint dating)
  I2  Legacy Springer BF-format DOI (often unresolvable)
  I3  @article has no DOI field
  I4  Field present but value is empty
  I5  Citation key contains no 19xx/20xx year
"""

from __future__ import annotations

import re
import sys
import argparse
from collections import defaultdict


# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_bib(filepath: str) -> list[dict]:
    """Return list of entry dicts: {type, key, fields, field_lines, duplicate_fields, line}."""
    with open(filepath, encoding="utf-8") as fh:
        text = fh.read()
    return _parse_text(text)


def _parse_text(text: str) -> list[dict]:
    entries: list[dict] = []
    i, n = 0, len(text)

    while i < n:
        at = text.find("@", i)
        if at == -1:
            break
        i = at + 1

        # Read entry type (letters only)
        j = i
        while j < n and text[j].isalpha():
            j += 1
        etype = text[i:j].lower()
        i = j

        # Skip whitespace to opening brace
        while i < n and text[i] in " \t\n\r":
            i += 1
        if i >= n or text[i] != "{":
            continue
        i += 1  # consume '{'

        entry_line = text.count("\n", 0, at) + 1

        # @preamble / @comment / @string — skip whole brace block
        if etype in ("preamble", "comment", "string"):
            depth = 1
            while i < n and depth > 0:
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                i += 1
            continue

        # Read citation key (up to first comma)
        j = i
        while j < n and text[j] not in (",", "}", "\n"):
            j += 1
        key = text[i:j].strip()
        i = j
        if i >= n or text[i] != ",":
            continue
        i += 1  # consume ','

        # Parse fields until closing } of the entry
        fields: dict[str, str] = {}
        field_lines: dict[str, int] = {}
        duplicate_fields: list[str] = []

        while i < n:
            # Skip whitespace
            while i < n and text[i] in " \t\n\r":
                i += 1
            if i >= n:
                break
            if text[i] == "}":
                i += 1
                break

            # Read field name
            field_start = i
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            fname = text[i:j].lower()
            i = j

            if not fname:
                i += 1  # skip unrecognised character
                continue

            fname_line = text.count("\n", 0, field_start) + 1

            # Skip whitespace + '='
            while i < n and text[i] in " \t\n\r":
                i += 1
            if i < n and text[i] == "=":
                i += 1
            while i < n and text[i] in " \t\n\r":
                i += 1

            # Read field value
            if i >= n:
                break

            if text[i] == "{":
                depth = 1
                i += 1
                start = i
                while i < n and depth > 0:
                    if text[i] == "{":
                        depth += 1
                    elif text[i] == "}":
                        depth -= 1
                    i += 1
                value = text[start : i - 1]
            elif text[i] == '"':
                i += 1
                start = i
                while i < n and text[i] != '"':
                    if text[i] == "\\" and i + 1 < n:
                        i += 1  # skip escaped character
                    i += 1
                value = text[start:i]
                if i < n:
                    i += 1  # consume closing '"'
            else:
                # Bare number or @string name
                j = i
                while j < n and text[j] not in " \t\n\r,}":
                    j += 1
                value = text[i:j].strip()
                i = j

            if fname in fields:
                duplicate_fields.append(fname)
            else:
                fields[fname] = value
                field_lines[fname] = fname_line

            # Skip trailing comma
            while i < n and text[i] in " \t\n\r":
                i += 1
            if i < n and text[i] == ",":
                i += 1

        entries.append(
            {
                "type": etype,
                "key": key,
                "fields": fields,
                "field_lines": field_lines,
                "duplicate_fields": duplicate_fields,
                "line": entry_line,
            }
        )

    return entries


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_duplicate_keys(entries: list[dict]) -> list[dict]:
    """E1: Same citation key used more than once."""
    issues: list[dict] = []
    seen: dict[str, int] = {}
    for e in entries:
        k = e["key"]
        if k in seen:
            issues.append(_issue("E1", e, f"Duplicate key (first at line {seen[k]})"))
        else:
            seen[k] = e["line"]
    return issues


def check_duplicate_dois(entries: list[dict]) -> list[dict]:
    """E2: Same DOI value appears in more than one entry."""
    issues: list[dict] = []
    doi_map: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for e in entries:
        doi = e["fields"].get("doi", "").strip().lower()
        if doi:
            doi_map[doi].append((e["key"], e["line"]))
    for doi, refs in doi_map.items():
        if len(refs) > 1:
            others = "; ".join(f"{k} (line {ln})" for k, ln in refs[1:])
            issues.append(
                {"code": "E2", "key": refs[0][0], "line": refs[0][1],
                 "msg": f"DOI '{doi}' also in: {others}"}
            )
    return issues


_REQUIRED: dict[str, list[str]] = {
    "article":       ["title", "author", "year", "journal"],
    "book":          ["title", "year", "publisher"],
    "inproceedings": ["title", "author", "year", "booktitle"],
    "incollection":  ["title", "author", "year", "booktitle", "publisher"],
    "phdthesis":     ["title", "author", "year", "school"],
    "mastersthesis": ["title", "author", "year", "school"],
    "techreport":    ["title", "author", "year", "institution"],
    "manual":        ["title"],
    "misc":          [],
}


def check_required_fields(entries: list[dict]) -> list[dict]:
    """E3: Entry missing a required field for its type."""
    issues: list[dict] = []
    for e in entries:
        for field in _REQUIRED.get(e["type"], []):
            if not e["fields"].get(field, "").strip():
                issues.append(_issue("E3", e, f"Missing required field '{field}'"))
        if e["type"] == "book":
            if not e["fields"].get("author", "").strip() and \
               not e["fields"].get("editor", "").strip():
                issues.append(_issue("E3", e, "Book missing both 'author' and 'editor'"))
    return issues


_DOI_URL_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://dx.doi.org/",
    "http://dx.doi.org/",
    "doi:",
    "DOI:",
)


def check_doi_prefix(entries: list[dict]) -> list[dict]:
    """E4: DOI field contains a URL prefix; should be bare DOI."""
    issues: list[dict] = []
    for e in entries:
        doi = e["fields"].get("doi", "")
        for pfx in _DOI_URL_PREFIXES:
            if doi.startswith(pfx):
                fixed = doi[len(pfx):]
                issues.append(
                    _fixable("E4", e, f"DOI has URL prefix  →  '{fixed}'",
                             "doi", doi, fixed)
                )
                break
    return issues


def check_duplicate_entry_fields(entries: list[dict]) -> list[dict]:
    """E5: Same field name appears twice within a single entry."""
    issues: list[dict] = []
    for e in entries:
        for fname in e.get("duplicate_fields", []):
            issues.append(_issue("E5", e, f"Duplicate field '{fname}'"))
    return issues


_KEY_YEAR_RE = re.compile(r"((?:19|20)\d{2})")


def check_key_year_mismatch(entries: list[dict]) -> list[dict]:
    """W1/I1: Year in citation key differs from the year field value."""
    issues: list[dict] = []
    for e in entries:
        year_field = e["fields"].get("year", "").strip()
        if not year_field.isdigit():
            continue
        m = _KEY_YEAR_RE.search(e["key"])
        if not m:
            continue
        key_year, actual_year = int(m.group(1)), int(year_field)
        diff = abs(key_year - actual_year)
        if diff == 0:
            continue
        code = "W1" if diff > 2 else "I1"
        issues.append(_issue(code, e, f"key year {key_year} ≠ year {actual_year} (Δ={diff})"))
    return issues


def check_journal_consistency(entries: list[dict]) -> list[dict]:
    """W2/W3: Same journal abbreviation or fjournal used with different counterpart."""
    issues: list[dict] = []
    abbr_to_full: dict[str, set[str]] = defaultdict(set)
    full_to_abbr: dict[str, set[str]] = defaultdict(set)

    for e in entries:
        j  = e["fields"].get("journal",  "").strip()
        fj = e["fields"].get("fjournal", "").strip()
        if j and fj:
            abbr_to_full[j].add(fj)
            full_to_abbr[fj].add(j)

    for abbr, fulls in sorted(abbr_to_full.items()):
        if len(fulls) > 1:
            variants = "; ".join(f'"{f}"' for f in sorted(fulls))
            issues.append({"code": "W2", "key": abbr, "line": 0,
                           "msg": f"'{abbr}' → {len(fulls)} fjournal variants: {variants}"})

    for full, abbrs in sorted(full_to_abbr.items()):
        if len(abbrs) > 1:
            variants = "; ".join(f'"{a}"' for a in sorted(abbrs))
            issues.append({"code": "W3", "key": full, "line": 0,
                           "msg": f"'{full}' ← {len(abbrs)} journal abbr variants: {variants}"})

    return issues


def check_missing_fjournal(entries: list[dict]) -> list[dict]:
    """W4: @article has 'journal' field but no 'fjournal' field."""
    issues: list[dict] = []
    for e in entries:
        if e["type"] == "article":
            j  = e["fields"].get("journal",  "").strip()
            fj = e["fields"].get("fjournal", "").strip()
            if j and not fj:
                issues.append(_issue("W4", e, "has 'journal' but no 'fjournal'"))
    return issues


_SINGLE_DASH_RANGE = re.compile(r"(?<!-)\s*-\s*(?!-)")


def check_page_format(entries: list[dict]) -> list[dict]:
    """W5: Page range uses single dash instead of the BibTeX double dash."""
    issues: list[dict] = []
    for e in entries:
        pages = e["fields"].get("pages", "").strip()
        if not pages or "--" in pages:
            continue
        if _SINGLE_DASH_RANGE.search(pages):
            fixed = _SINGLE_DASH_RANGE.sub("--", pages)
            issues.append(
                _fixable("W5", e, f"pages = {{{pages}}}  →  {{{fixed}}}",
                         "pages", pages, fixed,
                         line=e["field_lines"].get("pages", e["line"]))
            )
    return issues


_ARXIV_JOURNAL = re.compile(r"^arXiv:", re.IGNORECASE)
_ARXIV_DOI     = re.compile(r"^10\.48550/arXiv\.", re.IGNORECASE)


def check_arxiv_consistency(entries: list[dict]) -> list[dict]:
    """W6: Entry with arXiv journal but DOI not in 10.48550/arXiv.* format."""
    issues: list[dict] = []
    for e in entries:
        j   = e["fields"].get("journal", "").strip()
        doi = e["fields"].get("doi",     "").strip()
        if _ARXIV_JOURNAL.match(j) and doi and not _ARXIV_DOI.match(doi):
            issues.append(_issue("W6", e, f"arXiv entry has non-arXiv DOI: '{doi}'"))
    return issues


_LEGACY_DOI = re.compile(r"^10\.\d+/bf[0-9]", re.IGNORECASE)


def check_legacy_dois(entries: list[dict]) -> list[dict]:
    """I2: Legacy Springer BF-prefix DOI (often unresolvable)."""
    issues: list[dict] = []
    for e in entries:
        doi = e["fields"].get("doi", "")
        if _LEGACY_DOI.match(doi):
            issues.append(
                _issue("I2", e, f"Legacy BF-format DOI '{doi}' (may not resolve)",
                       line=e["field_lines"].get("doi", e["line"]))
            )
    return issues


def check_missing_dois(entries: list[dict]) -> list[dict]:
    """I3: @article entry has no DOI field."""
    issues: list[dict] = []
    for e in entries:
        if e["type"] == "article" and not e["fields"].get("doi", "").strip():
            issues.append(_issue("I3", e, "Article has no DOI"))
    return issues


_EMPTY_FIELD_SKIP = frozenset({
    # Commonly used as placeholders when the value is unknown/inapplicable;
    # an empty value here is intentional and should not be flagged.
    "number", "series", "address", "note", "url",
    "subtitle", "booksubtitle", "edition", "editor",
    # Handled by dedicated checks (I3) or genuinely optional for many types
    "doi", "volume", "pages",
})


def check_empty_fields(entries: list[dict]) -> list[dict]:
    """I4: Field is present but its value is empty (skips common placeholder fields)."""
    issues: list[dict] = []
    for e in entries:
        for fname, fval in e["fields"].items():
            if fname in _EMPTY_FIELD_SKIP:
                continue
            if not fval.strip():
                issues.append(
                    _issue("I4", e, f"Empty value for field '{fname}'",
                           line=e["field_lines"].get(fname, e["line"]))
                )
    return issues


_KEY_HAS_YEAR = re.compile(r"(?:19|20)\d{2}")


def check_key_format(entries: list[dict]) -> list[dict]:
    """I5: Citation key contains no 19xx/20xx year."""
    issues: list[dict] = []
    for e in entries:
        if not _KEY_HAS_YEAR.search(e["key"]):
            issues.append(_issue("I5", e, f"Key '{e['key']}' contains no year"))
    return issues


# ── Helpers ────────────────────────────────────────────────────────────────────

def _issue(code: str, e: dict, msg: str, line: int | None = None) -> dict:
    return {
        "code": code,
        "key":  e["key"],
        "line": line if line is not None else e["line"],
        "msg":  msg,
    }


def _fixable(
    code: str,
    e: dict,
    msg: str,
    field: str,
    old_value: str,
    new_value: str,
    line: int | None = None,
) -> dict:
    d = _issue(code, e, msg,
               line if line is not None else e["field_lines"].get(field, e["line"]))
    d.update({"fixable": True, "field": field,
              "old_value": old_value, "new_value": new_value})
    return d


# ── Report ─────────────────────────────────────────────────────────────────────

_DESCRIPTIONS: dict[str, str] = {
    "E1": "Duplicate citation keys",
    "E2": "Duplicate DOI values",
    "E3": "Missing required fields",
    "E4": "DOI field contains URL prefix  [auto-fix]",
    "E5": "Duplicate field within entry",
    "W1": "Key year mismatch > 2 years",
    "W2": "Same journal abbreviation → different fjournal",
    "W3": "Same fjournal → different journal abbreviation",
    "W4": "Article missing fjournal field",
    "W5": "Page range with single dash  [auto-fix]",
    "W6": "arXiv entry with non-arXiv DOI format",
    "I1": "Key year mismatch 1–2 years (preprint dating — usually expected)",
    "I2": "Legacy BF-format DOI (may be unresolvable)",
    "I3": "Article missing DOI",
    "I4": "Empty field value",
    "I5": "Citation key has no year",
}


def print_report(
    all_issues: list[dict],
    total_entries: int,
    bib_file: str,
    summary_only: bool = False,
) -> None:
    by_code: dict[str, list[dict]] = defaultdict(list)
    for iss in all_issues:
        by_code[iss["code"]].append(iss)

    W = 64
    print("=" * W)
    print("  DirectionalStats.bib — Quality Report")
    print(f"  File:    {bib_file}")
    print(f"  Entries: {total_entries}")
    print(f"  Issues:  {len(all_issues)}")
    print("=" * W)

    for sev, label in (("E", "ERRORS"), ("W", "WARNINGS"), ("I", "INFO")):
        codes = sorted(c for c in by_code if c.startswith(sev))
        if not codes:
            continue
        count = sum(len(by_code[c]) for c in codes)
        print(f"\n{'─' * W}")
        print(f"  {label}  ({count})")
        print(f"{'─' * W}")

        for code in codes:
            isslist = by_code[code]
            print(f"\n[{code}] {_DESCRIPTIONS.get(code, code)}  ({len(isslist)})")
            if summary_only:
                continue
            for iss in sorted(isslist, key=lambda x: x["line"]):
                loc = f" (line {iss['line']})" if iss["line"] else ""
                print(f"  • {iss['key']}{loc}: {iss['msg']}")

    fixable = [i for i in all_issues if i.get("fixable")]
    if fixable:
        print(f"\n{'─' * W}")
        print(f"  AUTO-FIXABLE  ({len(fixable)} issues — rerun with --fix)")
        print(f"{'─' * W}")
        fc: dict[str, int] = defaultdict(int)
        for i in fixable:
            fc[i["code"]] += 1
        for code, cnt in sorted(fc.items()):
            print(f"  [{code}] {_DESCRIPTIONS.get(code, code)}: {cnt} issue(s)")

    print()


# ── Fix ────────────────────────────────────────────────────────────────────────

def apply_fixes(filepath: str, fixable_issues: list[dict]) -> str:
    """Return corrected file content with all auto-fixable issues applied."""
    with open(filepath, encoding="utf-8") as fh:
        lines = fh.readlines()

    replacements: dict[int, list[tuple[str, str]]] = defaultdict(list)
    for iss in fixable_issues:
        replacements[iss["line"]].append((iss["old_value"], iss["new_value"]))

    for line_no, repls in replacements.items():
        idx = line_no - 1
        if 0 <= idx < len(lines):
            line = lines[idx]
            for old, new in repls:
                line = line.replace(f"{{{old}}}", f"{{{new}}}", 1)
            lines[idx] = line

    return "".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

_ALL_CHECKS = [
    check_duplicate_keys,
    check_duplicate_dois,
    check_required_fields,
    check_doi_prefix,
    check_duplicate_entry_fields,
    check_key_year_mismatch,
    check_journal_consistency,
    check_missing_fjournal,
    check_page_format,
    check_arxiv_consistency,
    check_legacy_dois,
    check_missing_dois,
    check_empty_fields,
    check_key_format,
]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check a BibTeX file for quality issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--bib",     default="DirectionalStats.bib",
                    help="BibTeX file to check (default: DirectionalStats.bib)")
    ap.add_argument("--fix",     action="store_true",
                    help="Write auto-fixed copy to FILE.fixed")
    ap.add_argument("--summary", action="store_true",
                    help="Print only counts per issue code")
    args = ap.parse_args()

    entries = parse_bib(args.bib)

    all_issues: list[dict] = []
    for check in _ALL_CHECKS:
        all_issues.extend(check(entries))

    print_report(all_issues, len(entries), args.bib, summary_only=args.summary)

    if args.fix:
        fixable = [i for i in all_issues if i.get("fixable")]
        if fixable:
            fixed_content = apply_fixes(args.bib, fixable)
            out_path = args.bib + ".fixed"
            with open(out_path, "w", encoding="utf-8") as fh:
                fh.write(fixed_content)
            print(f"Fixed copy written to: {out_path}")
            print(f"Review the changes, then apply with:")
            print(f"  mv {out_path} {args.bib}")
        else:
            print("No auto-fixable issues found.")

    has_errors = any(i["code"].startswith("E") for i in all_issues)
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
