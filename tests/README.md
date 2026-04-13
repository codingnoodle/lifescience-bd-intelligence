# BD Intelligence Test Suite

## Overview

This test suite validates the BD intelligence system against **real pharma acquisitions** from 2025-2026. Each test case represents an actual deal with known valuations, providing ground truth for system calibration.

## Test Cases

### Test 1: J&J / Intra-Cellular Therapies ($14.6B)
**What it tests**: Approved asset valuation

- **Asset**: Caplyta (lumateperone) for schizophrenia & bipolar depression
- **Key characteristics**: Approved drug, multiple indications, large CNS market
- **Expected output**: PTRS ~0.9, valuation $10-16B, GO recommendation
- **Validation**: System should recognize approved assets have high PTRS and value accordingly

**What could go wrong**:
- If valuation < $10B → System is underpricing approved assets
- If PTRS < 0.8 → Not recognizing approved status

---

### Test 2: Servier / Day One Biopharmaceuticals ($2.5B)
**What it tests**: Multi-indication portfolio valuation

- **Asset**: tovorafenib (BRAF inhibitor) for pediatric low-grade glioma + pipeline
- **Key characteristics**: Approved lead + early-stage programs, platform value
- **Expected output**: Valuation $2-3.5B, significant optionality premium
- **Validation**: BEST test for multi-indication waterfall logic

**What could go wrong**:
- If no secondary indications identified → Indications agent failing
- If optionality premium < 10% → Not valuing pipeline shots on goal
- If valuation > $4B → Overpricing preclinical pipeline

---

### Test 3: Novo Nordisk / Akero Therapeutics ($5.2B)
**What it tests**: Emerging indication / therapeutic area mapping

- **Asset**: efruxifermin for MASH (metabolic dysfunction-associated steatohepatitis)
- **Key characteristics**: Phase 3, large emerging market, high analyst sentiment
- **Expected output**: Use cardio_metabolic PTRS, large market size, GO
- **Validation**: System handles indications not in traditional categories

**What could go wrong**:
- If therapeutic area = "unknown" → TA mapping broken
- If market size = "small" → Not recognizing MASH epidemic scale
- If valuation < $4B → Underestimating emerging blockbuster potential

---

### Test 4: Jazz / Chimerix ($935M)
**What it tests**: Rare disease / small market

- **Asset**: dordaviprone for H3 K27M-mutant diffuse glioma (ultra-rare brain tumor)
- **Key characteristics**: NDA submitted, first-in-class, tiny patient population
- **Expected output**: High PTRS (~0.88), modest valuation <$1.2B, GO
- **Validation**: System correctly handles rare diseases without over-valuing

**What could go wrong**:
- If valuation > $2B → **CRITICAL ERROR** - prevalence model broken
- If recommendation = NO-GO → Not recognizing orphan drug value
- If market size = "large" → Patient population estimation failed

---

## Running Tests

### Prerequisites

```bash
# Install test dependencies
uv add pytest httpx

# Start the API server (in separate terminal)
uv run uvicorn backend.main:app --reload
```

### Run Test Suite

```bash
# Run all tests
uv run python tests/run_deal_tests.py

# Run against custom API endpoint
uv run python tests/run_deal_tests.py http://your-api:8000

# Just view test case summaries
uv run python tests/test_real_deals.py
```

### Using pytest (future)

```bash
# Once pytest integration is complete
uv run pytest tests/ -v
```

## Expected Output

```
================================================================================
BD INTELLIGENCE SYSTEM - REAL DEAL VALIDATION
================================================================================

Testing against: http://localhost:8000
Total test cases: 4

================================================================================
Testing: J&J / Intra-Cellular Therapies
Asset: Caplyta (lumateperone)
Actual Deal Value: $14,600,000,000
================================================================================

📊 RESULTS:
  Actual Portfolio Value: $13,200,000,000
  Expected Range: $10,000,000,000 - $16,000,000,000
  ✅ Valuation in range (error: 10.8%)

  Actual Recommendation: GO
  Expected: GO
  ✅ Recommendation correct

  Actual PTRS: 87.00%
  ✅ PTRS meets minimum

  Total Indications: 2
  Secondary: 1
  Preclinical: 0

✅ TEST PASSED

[... more tests ...]

================================================================================
SUMMARY
================================================================================

Tests Passed: 3/4
Tests Failed: 1/4
Errors: 0/4

Deal                                      Actual Deal     System Est.     Status
--------------------------------------------------------------------------------
J&J / Intra-Cellular Therapies            $14.60B         $13.20B         ✅
Servier / Day One Biopharmaceuticals      $2.50B          $2.80B          ✅
Novo Nordisk / Akero Therapeutics         $5.20B          $4.90B          ✅
Jazz Pharmaceuticals / Chimerix           $0.94B          $0.88B          ✅

💾 Full results saved to: test_results.json
```

## Interpreting Results

### Valuation Accuracy
- **Within ±20% of actual deal**: ✅ Good (market dynamics vary)
- **Within ±50% of actual deal**: ⚠️ Acceptable (needs tuning)
- **Off by >50%**: ❌ System calibration issue

### Common Failure Modes

1. **Underpricing approved assets** (Test 1)
   - Fix: Adjust PTRS for approved/marketed drugs to 0.9-0.95

2. **Missing secondary indications** (Test 2)
   - Fix: Improve indications_agent web search
   - Fix: Better MOA → indication expansion logic

3. **Wrong therapeutic area mapping** (Test 3)
   - Fix: Add TA normalization logic
   - Fix: Handle emerging indications (MASH, obesity, etc.)

4. **Overvaluing rare diseases** (Test 4)
   - Fix: Peak sales estimation based on prevalence
   - Fix: Don't confuse high pricing with high revenue

## Calibration Guidelines

### When to Adjust PTRS Table
- If approved drugs consistently undervalued → Increase NDA submitted PTRS
- If Phase 3 deals consistently off → Review Phase 3 PTRS by TA

### When to Adjust Optionality Premium
- Default: 15% for 2+ secondary indications
- If Test 2 fails: Adjust premium based on pipeline stage mix
- Platform technologies: May justify 20-25% premium

### When to Adjust Market Sizing
- If Test 4 fails high: Improve prevalence → peak sales logic
- If Test 3 fails low: Better handle emerging blockbusters

## Next Steps

1. **Implement Agent Logic**: Replace stubs with actual LLM calls and web search
2. **Run Baseline**: Execute tests to establish baseline performance
3. **Calibrate**: Adjust PTRS table, optionality premium, market sizing
4. **Iterate**: Re-run tests until 3/4 or 4/4 pass
5. **Add More Tests**: Expand to 10-20 real deals for robust validation

## References

- Test 1 Source: [Drug Discovery Trends](https://www.drugdiscoverytrends.com/)
- Test 2 Source: SEC filings
- Test 3 Source: [Fierce Pharma](https://www.fiercepharma.com/)
- Test 4 Source: SEC filings
