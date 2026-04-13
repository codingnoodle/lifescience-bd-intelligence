# Test Case Quick Reference

## At a Glance

| Deal | Value | Asset | Stage | Test Focus | Pass Criteria |
|------|-------|-------|-------|------------|---------------|
| **J&J / Intra-Cellular** | $14.6B | Caplyta | Approved | Approved asset pricing | $10-16B, GO |
| **Servier / Day One** | $2.5B | tovorafenib | Approved + Pipeline | Multi-indication portfolio | $2-3.5B, GO, optionality premium |
| **Novo / Akero** | $5.2B | efruxifermin | Phase 3 | Emerging indication (MASH) | $4-6.5B, GO, large market |
| **Jazz / Chimerix** | $935M | dordaviprone | NDA | Rare disease, small market | <$1.5B, GO, small market |

## Red Flags by Test

### Test 1: J&J / Intra-Cellular
- ❌ Valuation < $10B → Underpricing approved assets
- ❌ PTRS < 80% → Not recognizing approved status
- ❌ NO-GO recommendation → Something fundamentally broken

### Test 2: Servier / Day One
- ❌ No secondary indications → Indications agent failing
- ❌ Optionality premium < 10% → Not valuing pipeline
- ❌ Valuation > $4B → Overpricing preclinical assets

### Test 3: Novo / Akero
- ❌ Therapeutic area = unknown → TA mapping broken
- ❌ Market size = small → Not recognizing epidemic-scale disease
- ❌ Valuation < $4B → Missing blockbuster potential

### Test 4: Jazz / Chimerix
- ❌ Valuation > $2B → **CRITICAL** - Prevalence model broken
- ❌ Market size = large → Patient population wrong
- ❌ NO-GO → Not recognizing orphan drug value

## Expected PTRS by Test

- Test 1 (Approved): ~87-90%
- Test 2 (Approved lead): ~85% primary, ~10% preclinical
- Test 3 (Phase 3): ~66% (cardio_metabolic)
- Test 4 (NDA): ~89.5% (rare_disease)

## Expected Indication Counts

- Test 1: 2 indications (both approved)
- Test 2: 3-4 indications (1 approved, 2-3 early/preclinical)
- Test 3: 1-2 indications (MASH primary, possible expansion)
- Test 4: 1 indication (ultra-rare, single focus)

## Run Commands

```bash
# View test case summaries
uv run python tests/test_real_deals.py

# Run all tests
uv run python tests/run_deal_tests.py

# Run single test (future)
uv run python tests/run_deal_tests.py --test "J&J"
```

## What Good Looks Like

```
Deal                                      Actual Deal     System Est.     Status
--------------------------------------------------------------------------------
J&J / Intra-Cellular Therapies            $14.60B         $13.20B         ✅
Servier / Day One Biopharmaceuticals      $2.50B          $2.80B          ✅
Novo Nordisk / Akero Therapeutics         $5.20B          $4.90B          ✅
Jazz Pharmaceuticals / Chimerix           $0.94B          $0.88B          ✅

Tests Passed: 4/4
```

**Target**: 3/4 or 4/4 tests passing within ±30% valuation accuracy
