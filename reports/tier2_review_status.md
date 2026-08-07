# DR-100: Tier-2 Human Domain Expert Review (Gate D of Road to FINAL)

Cycle: 256

## Status: **BLOCKED ON HUMAN REVIEW**

This gate CANNOT be completed autonomously. It requires actual
human domain experts to review the proposals and submit scores.

## What has been prepared

- **Review form**: `reports/tier2_review_form.md` (6 anonymized proposals)
- **CSV response template**: `reports/tier2_review_template.csv`
- **JSON response template**: `reports/tier2_review_template.json`
- **Aggregation script**: `reports/tier2_review_aggregation.py`
- **Internal mapping**: `reports/tier2_review_mapping.json` (NOT for reviewers)

## What is required to close this gate

1. Recruit ≥3 domain experts (materials science, biology, physics —
   matching the domains of the gold discoveries).
2. Send each expert the review form + CSV template.
3. Each expert reviews ALL proposals (or a random subset, but the
   same subset across experts for inter-rater agreement).
4. Collect filled CSV templates.
5. Merge responses into a single CSV: `reports/tier2_review_responses.csv`
6. Run the aggregation script:
   ```
   python3 reports/tier2_review_aggregation.py reports/tier2_review_responses.csv
   ```
7. The script writes `reports/tier2_review_aggregated.json` with
   the gate verdict.

## Rubric summary

- 7 scoring dimensions (D1-D7)
- Each scored 1-5 (1=strongly disagree, 5=strongly agree)
- Overall verdict per proposal: ACCEPT / REVISE / REJECT

## Gate D verdict logic (applied by aggregation script)

- **PASS**: overall mean score ≥ 3.5 AND accept rate ≥ 50%
- **PARTIAL**: overall mean score ≥ 3.0 OR accept rate ≥ 30%
- **FAIL**: both below thresholds

## Until responses are collected

Gate D remains BLOCKED. The FINAL verdict cannot be issued until
Gate D is PASS or PARTIAL. If Gate D is FAIL (or remains BLOCKED
for longer than a reasonable review period), the FINAL verdict
remains NOT TRUSTWORTHY.
