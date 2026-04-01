# MFE Admission Data Quality Report

**Generated**: 2026-04-01 01:27:50
**Total Records**: 11566

## Records by Source

| Source | Count | % |
|--------|------:|--:|
| quantnet_tracker | 6723 | 58.1% |
| reddit | 3494 | 30.2% |
| gradcafe | 1089 | 9.4% |
| 1p3a-offer | 143 | 1.2% |
| 1p3a-raw | 27 | 0.2% |
| 1p3a-bbs | 24 | 0.2% |
| 1p3a-thread | 22 | 0.2% |
| 1p3a-bg | 14 | 0.1% |
| 小红书 | 7 | 0.1% |
| chasedream | 7 | 0.1% |
| quantnet | 6 | 0.1% |
| offershow | 4 | 0.0% |
| linkedin | 3 | 0.0% |
| 1p3a-member | 3 | 0.0% |

## Quality Tier Distribution

| Tier | Description | Count | % |
|------|-------------|------:|--:|
| A (Gold) | 4+ rich fields + result | 406 | 3.5% |
| B (Silver) | 2-3 rich fields + result | 1319 | 11.4% |
| C (Bronze) | GPA/GRE + result | 6985 | 60.4% |
| D (Basic) | Result only or no result | 2856 | 24.7% |

## Tier Distribution by Source

| Source | A | B | C | D | Total |
|--------|--:|--:|--:|--:|------:|
| 1p3a-bbs | 2 | 15 | 0 | 7 | 24 |
| 1p3a-bg | 0 | 0 | 0 | 14 | 14 |
| 1p3a-member | 0 | 0 | 0 | 3 | 3 |
| 1p3a-offer | 0 | 0 | 0 | 143 | 143 |
| 1p3a-raw | 0 | 6 | 0 | 21 | 27 |
| 1p3a-thread | 5 | 8 | 0 | 9 | 22 |
| chasedream | 7 | 0 | 0 | 0 | 7 |
| gradcafe | 0 | 176 | 255 | 658 | 1089 |
| linkedin | 3 | 0 | 0 | 0 | 3 |
| offershow | 4 | 0 | 0 | 0 | 4 |
| quantnet | 6 | 0 | 0 | 0 | 6 |
| quantnet_tracker | 0 | 0 | 6723 | 0 | 6723 |
| reddit | 372 | 1114 | 7 | 2001 | 3494 |
| 小红书 | 7 | 0 | 0 | 0 | 7 |

## Field Coverage

| Field | Records with data | Coverage % |
|-------|------------------:|-----------:|
| result | 11151 | 96.4% |
| program | 10955 | 94.7% |
| research_level | 10565 | 91.3% |
| season | 7928 | 68.5% |
| gpa_scale | 7256 | 62.7% |
| gpa | 6963 | 60.2% |
| major | 3263 | 28.2% |
| major_relevance | 3263 | 28.2% |
| undergrad_school | 2624 | 22.7% |
| undergrad_tier | 1824 | 15.8% |
| undergrad_country | 1812 | 15.7% |
| nationality | 1570 | 13.6% |
| intern_level | 1365 | 11.8% |
| intern_relevance | 1365 | 11.8% |
| has_research | 1115 | 9.6% |
| intern_count | 1063 | 9.2% |
| toefl | 583 | 5.0% |
| gender | 445 | 3.8% |
| has_paper | 425 | 3.7% |
| gre_quant | 222 | 1.9% |
| gre_verbal | 199 | 1.7% |

## Top 25 Programs by Record Count

| Program | Count |
|---------|------:|
| bu-msmf | 1432 |
| cmu-mscf | 1284 |
| columbia-msfe | 1073 |
| mit-mfin | 825 |
| uchicago-msfm | 754 |
| baruch-mfe | 702 |
| cornell-mfe | 583 |
| nyu-tandon-mfe | 542 |
| berkeley-mfe | 507 |
| gatech-qcf | 462 |
| finance-unknown | 423 |
| uiuc-msfe | 361 |
| ucla-mfe | 291 |
| stanford-mcf | 186 |
| rutgers-mqf | 176 |
| uwash-cfrm | 174 |
| mfe-unknown | 170 |
| utoronto-mmf | 161 |
| ncstate-mfm | 149 |
| jhu-mfm | 132 |
| fordham-msqf | 117 |
| usc-msmf | 88 |
| princeton-mfin | 72 |
| stevens-mfe | 70 |
| toronto-mmf | 46 |

## Result Distribution

| Result | Count | % |
|--------|------:|--:|
| accepted | 7072 | 63.8% |
| rejected | 3852 | 34.7% |
| waitlisted | 166 | 1.5% |

## Top Seasons

| Season | Count |
|--------|------:|
| 25Fall | 813 |
| 17Fall | 567 |
| 24Fall | 564 |
| 14Fall | 549 |
| 18Fall | 522 |
| 15Fall | 516 |
| 26Fall | 512 |
| 16Fall | 504 |
| 12Fall | 458 |
| 13Fall | 425 |

## Model-Readiness Summary

- **Tier A+B (model-ready with rich features)**: 1725 records (14.9%)
- **Tier C (basic features)**: 6985 records (60.4%)
- **Tier D (needs enrichment)**: 2856 records (24.7%)
- **Records with accept/reject/waitlist label**: 11090 (95.9%)

## Pipeline Summary

| Pipeline | Source | Records | Method |
|----------|--------|--------:|--------|
| 1 - Reddit | reddit | 3494 | Reddit JSON search API across 8 subreddits + global search |
| 2 - GradCafe | gradcafe | 1089 | GitHub dataset (be-green/gradcafe) filtered for finance/quant |
| 3a - 1P3A Offer | 1p3a-offer | 143 | Existing offer_1p3a_results.csv |
| 3b - 1P3A BG | 1p3a-bg | 14 | Existing offer_1p3a_backgrounds.csv |
| 3c - Collected | quantnet_tracker + others | 6730 | Existing collected.csv (multi-source) |
| 3d - Threads | 1p3a-thread | 22 | Existing parsed_threads.csv |
| 3e - BBS | 1p3a-bbs | 24 | 24 BBS thread JSON files |
| 3f - Raw | 1p3a-raw | 27 | 16 raw 1P3A text files |
