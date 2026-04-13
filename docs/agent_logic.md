# Agent Logic & Design Considerations

This document covers how each agent reasons, what it scores, known limitations, and guidance for tuning or extending the system. Read this before modifying agent prompts or scoring weights.

---

## Graph Overview

```
User query
    │
    ▼
research_planner  ──► [discovery_agent]  ──► return candidates (discovery mode)
    │
    ├──► science_agent  ─┐
    │                    ├──► synthesizer  ──► GO / WATCH / NO-GO + deal range
    └──► market_agent  ──┘
```

Two execution paths:

| Query type | Example | Path |
|---|---|---|
| **Specific asset** | "ARV-471 ER+ breast cancer Phase 3" | research_planner → science + market (parallel) → synthesizer |
| **Discovery / scan** | "top Phase 2 oncology assets 2028" | research_planner → discovery_agent → return candidates |

The research planner classifies the query and routes accordingly. Specific asset queries run the full diligence graph; discovery queries skip it entirely.

---

## 1. Research Planner

**Model:** Claude Haiku 4.5 (fast, cheap — structured parsing only)

**What it does:**
- Classifies query as `"specific_asset"` or `"discovery"`
- For specific assets: extracts `asset_name`, `indications[]` (name, phase, TA, launch year)
- For discovery: extracts `scan_criteria` (phase, TA, launch year, keywords)
- Looks up PTRS for each indication from the hardcoded phase × TA table

**Key design decisions:**
- `clarification_needed` is always `null` — the agent infers rather than asking. This is intentional: VC associates want instant results, not a back-and-forth. The tradeoff is occasional wrong inference (e.g. wrong TA for an obscure asset), which downstream agents can usually recover from.
- If the user explicitly states a phase (e.g. "what if Phase 1"), that phase is used verbatim — even if the real phase is different. This enables **what-if scenario analysis** (e.g. "how would the deal range change if we model this as Phase 1?").
- Sidebar filters (phase, TA, launch year chips) are passed as hints. They override inferences only when the message is ambiguous.

**PTRS lookup table** (`backend/utils/ptrs_lookup.py`):

| Phase | Oncology | Other TA |
|---|---|---|
| Preclinical | 5% | 8% |
| Phase 1 | 10% | 13% |
| Phase 2 | 25% | 28% |
| Phase 3 | 55% | 60% |
| NDA / BLA | 85% | 88% |

These are industry-standard estimates based on historical approval rates. Oncology has lower PTRS than other TAs at early stages due to higher attrition. Adjust these values in `ptrs_lookup.py` if you want to calibrate to a specific sub-sector (e.g. ADC oncology has been running ~35% Phase 2 success recently).

---

## 2. Science Agent

**Model:** Claude Sonnet (reasoning-capable)
**Search:** Tavily → PubMed, FDA, NEJM, Lancet, ClinicalTrials.gov

**What it scores (0–10):**
- Clinical trial design quality and endpoint selection
- Efficacy data: ORR, PFS, OS, biomarker response
- Mechanism differentiation vs. standard of care
- Safety and tolerability profile
- Regulatory pathway clarity (breakthrough designation, fast-track, etc.)

**Search strategy:**
- Search 1: `"{asset} {indication} clinical trial results efficacy safety"`
- Search 2: `"{asset} mechanism of action target biology"`

If Tavily returns nothing (asset is brand-new or fictional), the model falls back to training knowledge about the asset class and MOA.

**Known limitation — unknown assets:**
For a brand-new asset with no public data, the science score will be driven almost entirely by the agent's priors about the MOA class (e.g. "ADC targeting HER2 in oncology has a reasonable track record"). This is appropriate — the agent is effectively scoring the *archetype*, not the specific asset. The market rationale field will flag this.

**Calibration note:**
Science scores below 4 should typically correlate with fundamental biological concerns (unvalidated target, safety signals in class, failed Phase 2 for same mechanism). A low science score for a well-known target (e.g. EGFR in NSCLC) usually means the agent found competitive differentiation concerns, not a bad target.

---

## 3. Market Agent

**Model:** Claude Sonnet
**Search:** Tavily → EvaluatePharma, BioPharma Dive, SEC filings, Fierce Pharma

**What it scores (0–10):**
- Addressable patient population and treatment rate
- Competitive landscape (approved drugs, pipeline density)
- Pricing / reimbursement precedents
- Deal comp anchoring (see below)

**Three Tavily searches:**
1. `"{asset} market size peak sales revenue"` — asset-specific (returns nothing for new assets)
2. `"{asset} competitive landscape pipeline competitors"` — asset-specific
3. `"{TA} {phase} pharma deal acquisition upfront milestone 2021–2025"` — **archetype-based**, works for any asset

**Peak sales estimation (`peak_sales_bn`):**
This is the **undiscounted** peak sales figure. PTRS and NPV time-discounting are applied downstream by the market agent itself before passing to the synthesizer.

The formula the market agent uses internally:
```
peak_sales_bn_adj = peak_sales_bn × PTRS × (1 / 1.10^years_to_launch)
```

**Why archetype comps matter for new assets:**
A brand-new asset with no Tavily results would otherwise produce a conservative peak sales estimate based only on generic TA benchmarks. The archetype deal search anchors the estimate against what strategic buyers have actually paid for comparable assets:

**Calibrated upfront deal ranges from `backend/utils/deal_benchmarks.json`** (2025–2026 real M&A + licensing data):

| TA | Phase | Low | Mid | High | Key example |
|---|---|---|---|---|---|
| Oncology hematology | Phase 1/2 | $2.0B | $4.5B | $7.5B | Merck/TERN-701 $5.7B (allosteric BCR::ABL1 TKI) |
| Oncology hematology | Phase 2–BLA | $2.0B | $5.0B | $8.0B | Gilead/Arcellx $7.3B (BCMA CAR-T) |
| Oncology ADC (solid tumor) | Phase 1/2 | $1.5B | $3.5B | $6.0B | Gilead/Tubulis $3.15B |
| Oncology IO bispecific | Phase 2 | $1.0B | $2.5B | $4.5B | Pfizer/3SBio $1.25B upfront ($6B total) |
| Oncology IO bispecific | Phase 3 | $1.5B | $4.0B | $8.0B | BMS/BNT327 $3.5B upfront ($11.1B total) |
| Cardiometabolic / GLP-1 / obesity | Phase 2 | $1.0B | $3.0B | $6.0B | Pfizer/Metsera $4.9B; GSK/efimosfermin $1.2B |
| Cardiometabolic / MASH | Phase 3 | $2.0B | $4.5B | $8.0B | Novo/Akero $4.7B; Roche/89bio $2.4B |
| Immunology / autoimmune | Phase 1 | $1.0B | $2.0B | $4.0B | AbbVie/Capstan $2.1B (in vivo CAR-T) |
| Immunology / autoimmune | Phase 1/2 | $1.0B | $2.5B | $5.0B | Gilead/Ouro $2.18B (T-cell engager) |
| Neuroscience / CNS | Phase 2 | $1.0B | $3.5B | $7.0B | Eli Lilly/Centessa $6.3B (OX2R agonists) |
| Neuroscience / neuromuscular | Phase 3 | $3.0B | $8.0B | $14.0B | Novartis/Avidity $12B (AOC) |
| Rare disease | Phase 3 | $0.3B | $2.0B | $6.0B | BioMarin/Inozyme $0.27B vs. BioMarin/Amicus $4.8B |
| Respiratory | Phase 3 / marketed | $2.0B | $6.0B | $10.0B | Merck/Cidara $9.2B; Merck/Verona $10B |

Modality premiums on top: ADC +10–30%, CAR-T +20–40%, gene editing/RNA +10–30%, platform +50–200%.

**Known limitation — PTRS×NPV over-discounting:**
The mechanical PTRS×NPV formula aggressively compresses deal ranges for early-stage assets. A Phase 2 oncology asset with $3B undiscounted peak sales becomes only $465M after PTRS (25%) × NPV (62% for 5-year launch). Real pharma acquirers do not price like this — they pay for **strategic option value** and the upside scenario. The synthesizer is instructed to use archetype comps as a floor to counteract this.

---

## 4. Synthesizer

**Model:** Claude Sonnet
**No external calls** — synthesizes what science + market agents already produced.

**Composite score:**
```
composite = 0.60 × science_score + 0.40 × market_score
```

Science is weighted higher because science risk is the primary reason BD deals fail post-signing. Market risk (competition, pricing) is real but more manageable.

**GO / WATCH / NO-GO thresholds:**

| Score | Recommendation |
|---|---|
| ≥ 6.5 | **GO** |
| 4.5 – 6.4 | **WATCH** |
| < 4.5 | **NO-GO** |

These thresholds are calibrated against the test suite (see `tests/test_real_deals.py`). Adjust them in the synthesizer prompt if you want stricter or looser criteria.

**Deal range — comp-sheet reasoning (3 steps):**

1. **Archetype anchor:** Identify the closest comparable deal archetype from training knowledge (e.g. "Phase 2 oncology ADC → AZ/Daiichi-class: $3–8B upfront for promising assets")

2. **Adjust vs. archetype:** Move the range based on:
   - Science score vs. archetype → higher score = move toward high end
   - Number of indications → 10–20% optionality premium for 2+
   - Best-in-class data, validated target, hot deal environment → premium
   - Weak PTRS, single indication, crowded market → discount

3. **Sanity check:** PTRS-adjusted NPV provides a theoretical floor; the archetype comp provides a ceiling. The true deal range sits between these.

**Why not just use PTRS-adjusted NPV × multiplier?**
That approach produces systematically low deal ranges for early-stage assets. A Phase 2 asset with 25% PTRS and $4B undiscounted peak sales → $620M adj peak → $1.2–2.5B deal range via formula. But real Phase 2 oncology deals regularly close at $3–8B because acquirers are paying for the upside scenario and competitive exclusivity, not the expected value. The comp-sheet approach replicates how actual BD bankers model these deals.

**GP summary format:**
Four sentences max, written for a non-technical GP reading in 30 seconds:
1. Asset identity and core thesis
2. Key science data point or concern
3. Market opportunity and deal range
4. Key risk or caveat

---

## 5. Discovery Agent

**Model:** Claude Sonnet
**Trigger:** Query classified as `"discovery"` by research planner

**What it does:**
Returns a ranked list of 3–5 real, publicly known candidates matching the scan criteria. Uses training knowledge of clinical pipelines, ClinicalTrials.gov data, and recent conference disclosures.

**Output per candidate:**

| Field | Description |
|---|---|
| `name` | INN or asset code |
| `sponsor` | Company name |
| `status` | `active` / `discontinued` / `partnered` |
| `phase` | e.g. "Phase 2" |
| `details` | 1–2 sentence mechanism + key trial data |
| `target` | Molecular target or MOA |
| `trialId` | NCT number (only if highly confident, else null) |
| `sites` | Trial sites or null |
| `lastUpdate` | Approx. date of most recent public update |
| `historicalDeal` | Deal value if partnered/acquired |

**Known limitation — training data cutoff:**
The discovery agent uses model training knowledge, not live ClinicalTrials.gov data. Assets entering trials after the training cutoff (August 2025) will not appear. For production use, this agent should be extended with a live ClinicalTrials.gov API call via Tavily or direct API.

**Trial IDs:**
The agent is instructed to only populate `trialId` if highly confident. Still, verify any NCT numbers before sharing with investors — hallucinated trial IDs are a known failure mode for LLMs in this domain.

---

## Scoring Interaction Effects

| Scenario | What happens |
|---|---|
| High science (8), low market (3) | Composite = 6.0 → WATCH. The strong science doesn't overcome a small/crowded market. |
| Low science (2), high market (8) | Composite = 4.4 → NO-GO. Strong market doesn't save weak biology. |
| High science (8), high market (8) | Composite = 8.0 → GO. Deal range anchors to high end of archetype. |
| Single weak indication | No optionality premium. Deal range stays at lower end. |
| 3+ indications | 10–20% optionality premium. Synthesizer raises deal range ceiling. |
| Preclinical, unknown asset | PTRS = 5%, NPV discount = 50%. Adj. peak sales very low. Comp-sheet anchoring prevents collapse to near-zero. |

---

## Tuning Guide

**Science scores feel too high/low across the board:**
Adjust the scoring guide in `backend/agents/science_agent.py`. The rubric defines what 9–10, 7–8, etc. mean.

**Deal ranges feel too conservative:**
1. Check if Tavily is configured — without it, the archetype comp search is empty and the model falls back to conservative estimates.
2. Add more archetype anchors to the market agent prompt for specific TAs you cover most.
3. Raise the deal multiplier range in the synthesizer prompt (currently 2–8×, adjust up for hot markets).

**Deal ranges feel too aggressive:**
Lower the archetype comp reference values in the market agent prompt, or add a discount rule in the synthesizer for early-stage assets.

**PTRS table needs updating:**
Edit `backend/utils/ptrs_lookup.py`. Phase aliases and TA normalization are also in that file.

**Thresholds for GO/WATCH/NO-GO:**
Adjust the three threshold values at the bottom of the synthesizer prompt. Run the test suite after changes to validate against known real deals.

---

## Known Issues & Future Work

| Issue | Impact | Fix |
|---|---|---|
| Discovery agent uses training knowledge only | Misses assets entering trials after Aug 2025 | Integrate live ClinicalTrials.gov API |
| Science agent can't access paywalled journals | Misses data behind NEJM/Lancet paywalls | Add institutional access or use preprint servers |
| Market agent peak sales conservative for unknown assets | Deal range too low for novel MOAs | More archetype anchors per TA; improve Tavily domain list |
| Single indication → deal range collapses via PTRS | Undervalues platform assets | Add platform premium rule when MOA is broadly applicable |
| No caching | Duplicate searches for same asset cost tokens | Add Redis cache keyed on asset + indication + phase |
