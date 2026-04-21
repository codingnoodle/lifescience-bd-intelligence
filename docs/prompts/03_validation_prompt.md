# Prompt 3: Validation Against Real Deals

Copy this into Claude Code to validate your system produces realistic deal prices.

---

## The Prompt

```
Run these validation tests against the BD intelligence system. For each test case,
submit the query to /analyze, then compare the output to the real deal price.
Do NOT hardcode any comparators, buyers, or deal values — the system must discover them.

TEST CASE 1: TERN-701 (Merck acquisition, $6.7B)

Input query: "Terns Pharmaceuticals, Phase 1/2 CML asset, allosteric BCR-ABL inhibitor,
63 patients dosed, orphan drug designation, unprecedented efficacy in pretreated patients
from ASH 2025."

Expected agent behavior:
- Science agent should discover: 74% MMR rate vs ~25% for Scemblix, T315I activity,
  orphan designation, 63 patients dosed
- De-risking signals: orphan_drug, patients_dosed_50plus, best_in_class_efficacy
  (possibly fda_registrational_alignment, biomarker_defined_population)
- PTRS should adjust from ~18% base (Phase 1/2 oncology) to ~28-35% adjusted
- Market agent should discover Scemblix (asciminib/Novartis) as SOC
- Differentiation verdict: best_in_class (74% vs 25% MMR is unambiguous)
- Peak sales displacement: $2-4B (Scemblix peak ~$3.5B × 40-60% capture + standalone)
- Synthesizer should identify Merck as top buyer (Keytruda LOE 2028, 1.5x urgency)
- Novartis as defensive buyer (defending Scemblix)

Pass criteria:
- Strategic if-succeed scenario: $5-9B (real deal $6.7B, within ±30%)
- Strategic risk-adjusted: $1.5-3B
- Recommendation: GO or WATCH (not NO-GO)
- Science score: 7+ (unprecedented efficacy data)
- Must discover Scemblix as comparator without being told


TEST CASE 2: Centessa / Eli Lilly ($7.8B total: $6.3B upfront + $1.5B CVR)

Input query: "Centessa Pharmaceuticals, cleminorexton (ORX750) Phase 2a for NT1/NT2/IH,
ORX142 Phase 1, ORX489 preclinical, breakthrough designation, registrational program
Q1 2026."

Expected agent behavior:
- Science agent should discover: OX2R agonist mechanism (disease-modifying, not symptom-only),
  breakthrough designation, Phase 2a with registrational path
- De-risking signals: breakthrough_designation, fda_registrational_alignment,
  platform_multi_indication, best_in_class_efficacy
- PTRS should adjust from ~27% base (Phase 2 neurology) to ~40-50%
- Market agent should discover Xywav/Jazz as SOC for narcolepsy
- Differentiation verdict: new_class_creation (Xywav treats symptoms, ORX750 is disease-modifying)
- Category expansion math: narcolepsy market × 1.5-2.0x expansion × 35% capture
- Multiple indications (NT1, NT2, IH) + pipeline (ORX142, ORX489) = platform premium
- Synthesizer should detect CVR structure (preclinical/Phase 1 assets alongside lead)

Pass criteria:
- Strategic if-succeed scenario: $6-10B (real deal $7.8B total, within ±30%)
- CVR split detected: upfront $5-7B + CVR $1-2B
- Recommendation: GO
- Must discover Xywav as SOC and classify as new_class_creation without being told
- Eli Lilly should appear as a likely buyer (flush capital, neuroscience expansion)


TEST CASE 3: Novo Nordisk / Akero ($5.2B)

Input query: "efruxifermin for MASH metabolic dysfunction-associated steatohepatitis
Phase 3 and liver fibrosis Phase 2, cardio-metabolic, launch 2027"

Pass criteria:
- Strategic if-succeed: $4-7B
- TA correctly mapped to cardio_metabolic
- Large market recognition (MASH is epidemic-scale)
- Recommendation: GO


TEST CASE 4: Jazz / Chimerix ($935M)

Input query: "dordaviprone for H3 K27M-mutant diffuse glioma NDA submitted,
rare disease oncology, launch 2025"

Pass criteria:
- Strategic if-succeed: $0.5-1.5B (small rare disease market)
- Should NOT exceed $2B (prevalence guard)
- Recommendation: GO (high PTRS for NDA-stage)


For each test case, report:
1. What the science agent found (signals, PTRS, score)
2. What the market agent found (comparator, verdict, peak sales)
3. What the synthesizer produced (buyers, scenarios, recommendation)
4. PASS/FAIL against the criteria above

If a test fails, suggest which parameter to tune:
- If strategic is too low: check peak sales sizing, deal multiple base, or buyer urgency
- If strategic is too high: check displacement capture rate or revenue multiplier
- If wrong comparator: check market agent search query construction
- If wrong verdict: check differentiation rubric thresholds
```

---

## What this validates

- Science agent correctly identifies de-risking signals from search data
- Market agent discovers the right SOC and applies the correct differentiation verdict
- Synthesizer maps real buyers with appropriate urgency multipliers
- Strategic if-succeed scenario tracks actual deal prices within 30%
- CVR detection works for multi-asset platforms
- System handles different deal archetypes: displacement (TERN-701), category creation (Centessa), emerging TA (Akero), rare disease (Chimerix)

## Tuning if tests fail

| Symptom | Likely cause | Fix |
|---|---|---|
| Strategic too low | Deal multiple base too conservative | Raise base multiples in synthesizer prompt |
| Strategic too high | Revenue multiplier too aggressive | Lower revenue_multiplier (default 4.0) |
| Wrong comparator found | Search query too broad | Narrow Tavily search to indication-specific terms |
| PTRS too low | Missing de-risking signals | Check science agent prompt for signal detection |
| No CVR detected | CVR detection prompt too strict | Lower threshold for platform component detection |
