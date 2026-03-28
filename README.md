# QuantPath

**MFE admission prediction and program ranking** — data-driven school selection for Master of Financial Engineering programs.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
[![CI](https://github.com/MasterAgentAI/QuantPath/actions/workflows/ci.yml/badge.svg)](https://github.com/MasterAgentAI/QuantPath/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Data

- **6,984 admission records** from GradCafe and QuantNet (accepted / rejected / waitlisted)
- **28 MFE programs** with prerequisites, deadlines, acceptance rates, salary outcomes
- **21 trained logistic regression models** (one per program with $\geq 30$ samples)

## Methodology

**Admission prediction**: per-program logistic regression on GPA + GRE Quant with bias correction. Raw training data has survivor bias (self-reported), so the model replaces the biased intercept with $\text{logit}(r)$ where $r$ is the official acceptance rate, preserving learned feature slopes.

**Profile evaluation**: 5-dimension weighted scoring (Math 30%, Statistics 20%, CS 20%, Finance/Econ 15%, GPA 15%) across 36 sub-factors extracted from coursework. Flags gaps ($< 6.0$) and strengths ($\geq 9.0$).

**School ranking**: reach / target / safety classification using LR probability thresholds (reach $< 40\%$, target $40$–$70\%$, safety $\geq 70\%$) with a 100-point composite fit score (GPA closeness, prerequisite match, acceptance feasibility, academic profile).

## Usage

```bash
pip install -e .

# Evaluate profile across 5 dimensions
quantpath evaluate --profile profiles/my_profile.yaml

# Rank 28 programs as reach / target / safety
quantpath rank --profile profiles/my_profile.yaml

# Build optimized application list (2-4 reach, 3-4 target, 1-2 safety)
quantpath list --profile profiles/my_profile.yaml

# Check prerequisite match for a specific program
quantpath match --profile profiles/my_profile.yaml --program baruch-mfe
```

## License

MIT
