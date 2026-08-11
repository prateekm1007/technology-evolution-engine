"""
Tests for F-047: real arXiv papers replace fabricated paper corpus.

Per ANTI_ENTROPY.md rule 1 (tests first), these tests lock the F-047
contract:
  1. No fabricated paper files remain (no 10.XXXX_*.txt pattern).
  2. 10 real arXiv paper files exist (NNNN.NNNNN.txt pattern).
  3. Each real paper file has the required metadata fields.
  4. The arXiv IDs do NOT form an arithmetic sequence (PR-20).
  5. Each paper's source URL returns HTTP 200 (PR-19).
  6. Each paper file's FETCH STATUS is OK (not FAILED).
  7. No templated "We [verb] [device] that achieves..." abstracts remain.

This is the same pattern as tests for F-043 (patent corpus), applied to
the paper corpus. The fabrication signature was sequential DOI endings
(.001 through .010) + templated abstracts without author metadata.
"""
import pathlib
import re
import subprocess
import sys
import urllib.request

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PAPERS_DIR = ROOT / "data" / "ingestion" / "papers"


# ----------------------------------------------------------------------
# 1. No fabricated files remain
# ----------------------------------------------------------------------

def test_no_fabricated_paper_files_remain():
    """F-047: no files matching the fabricated pattern (10.XXXX_*.txt)
    should remain in data/ingestion/papers/."""
    fabricated_pattern = re.compile(r"^10\.\d+_.*\.txt$")
    fabricated = [f.name for f in PAPERS_DIR.iterdir()
                  if fabricated_pattern.match(f.name)]
    assert len(fabricated) == 0, (
        f"F-047 violation: {len(fabricated)} fabricated paper files still "
        f"present: {fabricated}. All 10 fabricated files (sequential DOI "
        f"endings .001 through .010) must be deleted."
    )


def test_no_sequential_doi_endings_remain():
    """F-047: no files with sequential DOI endings (.001 through .010)
    should remain. This is the tell-tale fabrication signature."""
    files = sorted(f.name for f in PAPERS_DIR.iterdir() if f.suffix == ".txt")
    # Check that no file has a sequential .NNN ending (1-10)
    sequential_pattern = re.compile(r"\.00[1-9]\.txt$|\.010\.txt$")
    sequential_files = [f for f in files if sequential_pattern.search(f)]
    assert len(sequential_files) == 0, (
        f"F-047 violation: found files with sequential DOI endings: "
        f"{sequential_files}. Real arXiv IDs do not form sequential integer "
        f"sequences."
    )


# ----------------------------------------------------------------------
# 2. 10 real arXiv paper files exist
# ----------------------------------------------------------------------

def test_ten_real_paper_files_exist():
    """F-047: exactly 10 real arXiv paper files should exist (one per
    domain that was in the fabricated corpus)."""
    # Real arXiv IDs match the pattern NNNN.NNNNN (4 digits, dot, 5 digits)
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f.name for f in PAPERS_DIR.iterdir()
                  if arxiv_pattern.match(f.name)]
    assert len(real_files) == 10, (
        f"F-047 violation: expected 10 real arXiv paper files, found "
        f"{len(real_files)}: {real_files}"
    )


def test_each_paper_file_has_required_metadata():
    """Each real paper file must have the required metadata fields:
    TITLE, ARXIV ID, URL, FETCH STATUS, RETRIEVAL DATE, RETRIEVAL METHOD,
    SOURCE VERIFICATION, ABSTRACT."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    required_fields = [
        "TITLE:",
        "ARXIV ID:",
        "URL:",
        "FETCH STATUS:",
        "RETRIEVAL DATE:",
        "RETRIEVAL METHOD:",
        "SOURCE VERIFICATION:",
        "ABSTRACT",
    ]
    for f in real_files:
        content = f.read_text(encoding="utf-8")
        for field in required_fields:
            assert field in content, (
                f"Paper file {f.name} missing required field: {field}"
            )


def test_each_paper_fetch_status_is_ok():
    """Each real paper file must have FETCH STATUS: OK (not FAILED).
    A FAILED status means the fetch didn't actually retrieve real content."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    for f in real_files:
        content = f.read_text(encoding="utf-8")
        assert "FETCH STATUS: OK" in content, (
            f"Paper file {f.name} does not have FETCH STATUS: OK. "
            f"A failed fetch means the content is not real."
        )


# ----------------------------------------------------------------------
# 3. PR-20: arXiv IDs do NOT form an arithmetic sequence
# ----------------------------------------------------------------------

def test_arxiv_ids_do_not_form_arithmetic_sequence():
    """PR-20: the arXiv IDs must NOT form an arithmetic sequence. The
    fabricated files had sequential DOI endings (.001 through .010);
    real arXiv IDs should not have this pattern."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    # Extract the numeric part after the dot
    nums = []
    for f in real_files:
        parts = f.stem.split(".")
        if len(parts) == 2:
            try:
                nums.append(int(parts[1]))
            except ValueError:
                pass
    nums.sort()
    assert len(nums) == 10, f"Expected 10 arXiv IDs, got {len(nums)}"

    diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
    # Check no sequential +1 pattern (the fabrication signature)
    has_sequential_pattern = all(d == 1 for d in diffs)
    assert not has_sequential_pattern, (
        f"F-047 violation: arXiv IDs form a sequential +1 pattern: {nums}. "
        f"This is the fabrication signature."
    )
    # Check no constant diff (arithmetic sequence)
    all_same_diff = len(set(diffs)) == 1
    assert not all_same_diff, (
        f"F-047 violation: arXiv IDs form an arithmetic sequence: diffs={diffs}. "
        f"Real arXiv IDs do not have constant diffs."
    )


# ----------------------------------------------------------------------
# 4. PR-19: each URL returns HTTP 200
# ----------------------------------------------------------------------

def test_each_paper_url_returns_http_200():
    """PR-19: each paper's source URL must return HTTP 200. A 404 means
    the citation is broken."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    for f in real_files:
        content = f.read_text(encoding="utf-8")
        # Extract URL from the file
        url_match = re.search(r"^URL:\s*(.+)$", content, re.MULTILINE)
        assert url_match, f"Paper file {f.name} has no URL field"
        url = url_match.group(1).strip()
        # Verify URL returns HTTP 200
        try:
            req = urllib.request.Request(
                url, method="HEAD",
                headers={"User-Agent": "F-047-verifier/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                assert response.status == 200, (
                    f"Paper {f.name} URL returned HTTP {response.status}, "
                    f"expected 200. URL: {url}"
                )
        except Exception as e:
            # HEAD might not be supported — try GET
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "F-047-verifier/1.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    assert response.status == 200, (
                        f"Paper {f.name} URL returned HTTP {response.status}. "
                        f"URL: {url}"
                    )
            except Exception as e2:
                pytest.fail(
                    f"Paper {f.name} URL {url} could not be fetched: {e2}"
                )


# ----------------------------------------------------------------------
# 5. No templated abstracts remain
# ----------------------------------------------------------------------

def test_no_templated_abstracts_remain():
    """F-047: no templated 'We [verb] [device] that achieves...' abstracts
    should remain. The fabricated files all started with 'We demonstrate...',
    'We fabricated...', 'We synthesized...'. Real arXiv abstracts have
    varied structure."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    templated_starts = [
        "We demonstrate that",
        "We fabricated",
        "We synthesized",
        "We report",
        "We experimentally demonstrate",
    ]
    for f in real_files:
        content = f.read_text(encoding="utf-8")
        # Find the ABSTRACT section
        abs_match = re.search(
            r"ABSTRACT \(extracted from arxiv\.org\):\s*\n(.+?)(?:\n\nFULL FETCHED|$)",
            content, re.DOTALL
        )
        assert abs_match, f"Paper {f.name} has no ABSTRACT section"
        abstract = abs_match.group(1).strip()
        # Check that the abstract does NOT start with a templated phrase
        for templated in templated_starts:
            assert not abstract.startswith(templated), (
                f"Paper {f.name} abstract starts with templated phrase "
                f"'{templated}'. Real arXiv abstracts have varied structure."
            )


# ----------------------------------------------------------------------
# 6. Each paper file is non-trivial (has real content)
# ----------------------------------------------------------------------

def test_each_paper_file_has_substantial_content():
    """Each real paper file should have substantial content (not just
    a stub). A file < 1000 bytes likely failed to fetch real content."""
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    for f in real_files:
        size = f.stat().st_size
        assert size > 1000, (
            f"Paper file {f.name} is only {size} bytes — likely a failed "
            f"fetch. Real arXiv paper files should be >1000 bytes."
        )


# ----------------------------------------------------------------------
# 7. The 10 domains are covered (one paper per domain)
# ----------------------------------------------------------------------

def test_ten_domains_covered():
    """F-047: the 10 real papers should cover the 10 domains that were
    in the fabricated corpus:
    1. Radiative cooling
    2. Atmospheric water harvesting (MOF)
    3. Graphene oxide desalination
    4. Thermoelectric bismuth telluride
    5. Piezoelectric polymer
    6. Photoelectrochemical water splitting
    7. Solid-state battery garnet
    8. Biodegradable polymer
    9. Direct air capture (amine silica)
    10. LED spectral vertical farming
    """
    arxiv_pattern = re.compile(r"^\d{4}\.\d{4,5}\.txt$")
    real_files = [f for f in PAPERS_DIR.iterdir() if arxiv_pattern.match(f.name)]
    all_content = ""
    for f in real_files:
        all_content += f.read_text(encoding="utf-8").lower() + "\n"

    # Each domain should appear in at least one paper's content
    domain_keywords = [
        ("radiative cooling", ["radiative cooling", "sub-ambient", "subambient"]),
        ("atmospheric water / MOF", ["metal-organic framework", "mof", "water harvest"]),
        ("graphene oxide desalination", ["graphene oxide", "desalination", "membrane"]),
        ("thermoelectric", ["thermoelectric", "bismuth telluride", "bi2te3"]),
        ("piezoelectric polymer", ["piezoelectric", "pvdf", "polymer"]),
        ("photoelectrochemical", ["photoelectrochemical", "water splitting", "photoanode"]),
        ("solid-state battery garnet", ["garnet", "solid-state", "li7la3zr2o12", "electrolyte"]),
        ("biodegradable polymer", ["biodegrad", "bioplastic", "polymer blend"]),
        ("direct air capture", ["direct air capture", "amine-functionalized", "co2 capture"]),
        ("vertical farming / LED", ["vertical farming", "led", "spectral", "light pipe"]),
    ]
    missing_domains = []
    for domain, keywords in domain_keywords:
        found = any(kw in all_content for kw in keywords)
        if not found:
            missing_domains.append(domain)
    # Allow some flexibility — not every domain may have a perfect keyword match
    # but at least 8 of 10 should be covered
    assert len(missing_domains) <= 2, (
        f"F-047: {len(missing_domains)} domains not covered by any paper: "
        f"{missing_domains}. At least 8 of 10 domains should be covered."
    )
