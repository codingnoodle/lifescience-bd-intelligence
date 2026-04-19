# Test Suite — Real Deal Validation

Validates the BD intelligence system against real pharma acquisitions from 2025-2026.

## Quick start

```bash
# Start API server (terminal 1)
uv run uvicorn backend.main:app --reload

# Run all tests (terminal 2)
uv run python tests/run_deal_tests.py
```

## Test cases

| Deal | Value | Phase | Focus | Pass criteria |
|---|---|---|---|---|
| J&J / Intra-Cellular | $14.6B | Approved | Approved asset pricing | Strategic if-succeed $10-18B, GO |
| Servier / Day One | $2.5B | Approved + pipeline | Multi-indication portfolio | Strategic if-succeed $2-4B, GO |
| Novo / Akero | $5.2B | Phase 3 | Emerging TA (MASH) | Strategic if-succeed $4-7B, GO |
| Jazz / Chimerix | $935M | NDA | Rare disease, tiny market | Strategic if-succeed < $1.5B, GO |

## How it works

- `test_real_deals.py` — test case definitions (deal data, queries, expected ranges)
- `run_deal_tests.py` — runner that calls live `/analyze` endpoint, compares three-scenario output to actual deal values

The runner validates:
- Strategic if-succeed value falls within expected range
- Recommendation matches expected (GO/WATCH/NO-GO)
- PTRS meets minimum threshold for the phase
- Rare disease cap not exceeded

## Interpreting results

- Within 30% of actual deal: PASS
- Within 50%: acceptable, needs tuning
- Off by >50%: calibration issue — check `docs/agent_logic.md` tuning guide

## Adding test cases

Add to `REAL_DEAL_TEST_CASES` in `test_real_deals.py`:

```python
TEST_NEW = {
    "deal_name": "Buyer / Target",
    "actual_deal_value_usd": 5_000_000_000,
    "query": "asset name indication phase TA",
    "expected_analysis": {
        "expected_recommendation": "GO",
        "expected_valuation_range": [4_000_000_000, 6_500_000_000],
    },
    "test_criteria": {
        "min_ptrs": 0.60,
        "expected_go_no_go": "GO",
    },
}
```
