# Agent Logic & Design Considerations

This document covers how each agent reasons, what it scores, known limitations, and guidance for tuning or extending the system. Read this before modifying agent prompts or scoring weights.

---

## Graph Overview

The system uses a strictly sequential LangGraph pipeline. Each node enriches the shared `BDState` and passes it forward.

```
User query
    |
    v
research_planner  -->  science_agent  -->  market_agent  -->  synthesizer  -->  END
     (Haiku)            (Sonnet)            (Sonnet)           (Sonnet)
```

Sequential execution is required because the market agent reads `ptrs_adjusted` written by the science agent, and the synthesizer reads outputs from both.

Defined in `backend/graph.py` via `StateGraph(BDState)` with four nodes and four edges:

```
research_planner -> science_agent -> market_agent -> synthesizer -> END
```

### Ownership Split

| Agent | Owns | Does NOT touch |
|---|---|---|
| **Science agent** | Intrinsic asset properties: MOA, clinical data, regulatory signals, positioning profile, de-risking signals, PTRS adjustment | Comparators, market sizing, buyers |
| **Market agent** | Competitive environment: SOC comparators, metric comparison, differentiation verdict, dual peak sales | PTRS computation, buyer reasoning |
| **Synthesizer** | Buyer-side reasoning: buyer mapping, bidding tension, deal multiple, three-scenario valuation, CVR detection, composite score | Does not re-run searches for science or market data |

---

## 1. Research Planner

**Model:** Claude Haiku (fast, cheap -- structured parsing only)

**What it does:**
- Classifies query as `"specific_asset"` or `"discovery"`
- For specific assets: extracts `asset_name`, `indications[]` (name, phase, therapeutic_area, launch_year)
- For discovery: extracts `scan_criteria` (phase, TA, launch_year, keywords)
- Normalizes phase and TA strings to canonical keys via `normalize_phase()` and `normalize_ta()` from `ptrs_lookup.py`

**Inputs:**
- `state.message` -- raw user text
- `state.filters` -- sidebar filter hints (phases, launchYears, therapeuticAreas)

**Outputs written to state:**
- `drug_asset_name` -- string
- `indications` -- list of `IndicationAnalysis` dicts with `name`, `phase`, `therapeutic_area`, `launch_year`
- `clarification_needed` -- always null (agent infers rather than asking)
- `research_plan` -- short description string

**Key design decisions:**
- `clarification_needed` is always `null`. The agent infers rather than asking. This is intentional: VC associates want instant results, not a back-and-forth. The tradeoff is occasional wrong inference (e.g. wrong TA for an obscure asset).
- If the user explicitly states a phase (e.g. "what if Phase 1"), that phase is used verbatim -- supports what-if scenario analysis.
- Sidebar filters override inferences only when the message is ambiguous.

---

## 2. Science Agent

**Model:** Claude Sonnet
**Search:** Tavily (2 calls)

### Searches

| # | Query template | Domains |
|---|---|---|
| 1 | `"{asset} clinical trial ClinicalTrials.gov results patients dosed"` | clinicaltrials.gov, pubmed, fda.gov, asco.org, esmo.org, ash.confex.com, biorxiv.org |
| 2 | `"{asset} mechanism of action efficacy safety trial results ASH ASCO ESMO conference"` | pubmed, fda.gov, nejm.org, thelancet.com, nature.com, asco.org, esmo.org, ash.confex.com, biorxiv.org |

Each Tavily call uses `search_depth="advanced"` and `max_results=8`.

### LLM Output (per indication)

The prompt asks the LLM to return structured JSON with:

- **positioning_profile**: `target`, `moa`, `indication`, `line_of_therapy`, `efficacy_metrics[]` (metric_name, value, source), `safety_metrics[]` (metric_name, value, source), `differentiation_claims[]`
- **de_risking_signals**: list of strings from the fixed vocabulary (see PTRS section below)
- **science_score**: float 0-10
- **science_rationale**: 2-3 sentences

### Science Score Guide (0-10)

| Range | Meaning |
|---|---|
| 9-10 | Registrational-ready or pivotal-positive; unambiguous efficacy/safety; landmark differentiation |
| 7-8 | Phase 2/3 with strong signals; differentiated MOA; manageable safety; clear path to registration |
| 5-6 | Phase 1/2 with promising early data; MOA credible; uncertainties remain |
| 3-4 | Phase 1 first-in-human; limited efficacy data; MOA validated in preclinical only |
| 1-2 | Preclinical only; no human data; unvalidated target; class safety concerns |
| 0 | No credible scientific basis |

If data is sparse for a specific asset, the LLM scores the archetype (MOA class) and notes this in science_rationale.

### PTRS Computation (Python, not LLM)

After receiving the LLM output, the science agent calls `get_adjusted_ptrs(phase, therapeutic_area, signals)` in Python. The LLM does not compute PTRS.

**Outputs written to each indication dict:**
- `positioning_profile` -- dict
- `de_risking_signals` -- list (filtered to valid signals only)
- `ptrs_base` -- float (from lookup table)
- `ptrs_adjusted` -- float (base + signal adjustments, capped)
- `ptrs_breakdown` -- list of `{signal, contribution}` dicts
- `science_score` -- float
- `science_rationale` -- string

---

## 3. Market Agent

**Model:** Claude Sonnet
**Search:** Tavily (3 calls)

### Searches

| # | Query template | Domains |
|---|---|---|
| 1 | `"standard of care {indications} {TAs} approved drugs treatment guidelines"` | evaluate.com, fiercepharma.com, biopharmadive.com, pharmacytimes.com, globenewswire.com, businesswire.com, sec.gov, pubmed, nature.com, asco.org, esmo.org |
| 2 | `"{asset} {indications} market size peak sales revenue commercial forecast"` | (same) |
| 3 | `"{indications} {phases} pipeline competitors drugs clinical trials"` | (same) |

### Inputs from Science Agent

The market agent receives each indication dict already enriched with `positioning_profile`, `ptrs_adjusted`, `de_risking_signals`, etc. It passes the positioning profile (efficacy_metrics, safety_metrics, differentiation_claims) into the prompt so the LLM can perform metric-by-metric comparison against comparators.

### LLM Steps (per indication)

**Step 1 -- Comparator Discovery:** Find current SOC, pull peak sales forecasts for 1-3 key incumbents.

**Step 2 -- Metric Comparison:** Compare each efficacy/safety metric from the positioning_profile against the incumbent's published data. Produces a `metric_comparison[]` table with `{metric, asset_value, comparator_value, direction}`.

**Step 3 -- Differentiation Verdict:** One of five values:

| Verdict | Criteria | Displacement logic |
|---|---|---|
| `best_in_class` | 2+ efficacy metrics meaningfully better, no key metrics worse | Capture 40-60% of SOC peak annual sales |
| `better_in_class` | 1 metric meaningfully better, none worse | Capture 20-40% of SOC peak annual sales |
| `me_too` | Minor improvements or parity | Size on own patient population only |
| `worse_in_class` | Clearly inferior on key metric | Salvage/niche, 5-10% of SOC |
| `new_class_creation` | SOC addresses symptoms not pathology, OR "first-in-class"/"disease-modifying" language, OR no approved drug on this pathway | Category expansion: TA category sales x expansion_multiplier (1.5-2.0x) x 35% capture |

**Step 4 -- Peak Sales Sizing (dual, undiscounted):**

- `peak_sales_standalone_bn`: asset's own patient population x treatment rate x annual price x achievable share
- `peak_sales_with_displacement_bn`:
  - For best_in_class / better_in_class: SOC displacement capture + standalone
  - For new_class_creation: category expansion formula
  - For me_too / worse_in_class: same as standalone

**Comparator confidence:** high (single dominant SOC, clear benchmarks), medium (2-3 SOC options or conference abstract data), low (fragmented SOC or sparse data).

### LLM Output (per indication)

- `comparator` -- `{name, sponsor, peak_sales_bn, source}`
- `metric_comparison` -- list
- `differentiation_verdict` -- string
- `peak_sales_standalone_bn` -- float
- `peak_sales_with_displacement_bn` -- float
- `market_score` -- float 0-10
- `market_rationale` -- string
- `comparator_confidence` -- string

### Market Score Guide (0-10)

| Range | Meaning |
|---|---|
| 9-10 | Blockbuster potential, large unmet need, limited competition, strong pricing power |
| 7-8 | Strong market ($1-3B+ peak), moderate competition, differentiated positioning |
| 5-6 | Moderate market ($0.5-1B peak), competitive space, viable niche |
| 3-4 | Small market (<$500M peak) or highly competitive with pricing pressure |
| 1-2 | Niche/orphan or market already well-served |

---

## 4. Synthesizer

**Model:** Claude Sonnet
**Search:** Tavily (4 calls for buyer intelligence)

### Searches

| # | Query template | Domains |
|---|---|---|
| 1 | `"pharma companies commercial franchise {TAs} pipeline deals acquisitions 2025 2026"` | fiercepharma.com, biopharmadive.com, evaluate.com, globenewswire.com, businesswire.com, sec.gov, seekingalpha.com, reuters.com, bloomberg.com |
| 2 | `"{top buyer names} pharma M&A acquisition deal 2024 2025 2026 billion"` | (same) |
| 3 | `"{asset} analyst rating coverage price target pharma acquisition"` | (same) |
| 4 | `"{TAs} pharma M&A acquisition deal 2025 2026 billion oncology hematology"` | (same) |

### Inputs

Fully enriched indication dicts from science + market agents. Additionally:
- Pre-computed NPV discount factors per indication: `1 / (1.10 ^ years_to_launch)`
- Pre-computed per-indication dual values: `peak_sales_if_succeed_bn` and `peak_sales_risk_adjusted_bn`
- Buyer context from `buyer_context.py` (patent cliff and flush capital tables, formatted)

### Step 1 -- Buyer Mapping

Identifies top 3 most likely acquirers by combining:

a. **Franchise fit:** which pharma companies have active commercial franchises in this TA
b. **Patent cliff urgency:** uses multipliers from the buyer context tables (see below)
c. **Deal velocity:** if a buyer had 3+ deals >$1B in the past 12 months, add +0.2x to their urgency
d. **Defensive buyers:** a company whose drug IS the SOC comparator identified by the market agent

When a buyer appears in both the patent cliff and flush capital tables:
```
effective_urgency = max(cliff_urgency, flush_urgency), capped at 1.6x
```

#### Patent Cliff Buyers (from `buyer_context.py`)

| Buyer | LOE Drug | LOE Year | Cliff Urgency | Effective Urgency |
|---|---|---|---|---|
| Merck | Keytruda | 2028 | 1.5x | 1.5x |
| BMS | Revlimid/Opdivo | 2028 | 1.3x | 1.3x |
| Pfizer | multiple | 2027 | 1.2x | 1.2x |
| AbbVie | Humira biosimilar pressure | ongoing | 1.1x | 1.15x (flush overlap) |
| Novartis | Entresto | 2027 | 1.2x | 1.2x |
| J&J | Stelara biosimilars | 2026 | 1.15x | 1.15x |
| AstraZeneca | none major | -- | 1.05x | 1.05x |
| Roche | staggered | -- | 1.1x | 1.1x |
| GSK | staggered | -- | 1.1x | 1.1x |
| Sanofi | none major | -- | 1.0x | 1.0x |
| Gilead | HIV franchise maturing | 2027 | 1.2x | 1.2x |

#### Flush Capital Buyers

| Buyer | Source | Flush Urgency | Effective Urgency |
|---|---|---|---|
| Eli Lilly | GLP-1 revenue surge; neuroscience expansion | 1.3x | 1.3x |
| Novo Nordisk | Ozempic/Wegovy; cardiometabolic expansion | 1.25x | 1.25x |
| AbbVie | Skyrizi/Rinvoq recovery; oncology and aesthetics | 1.15x | 1.15x (cliff overlap, max capped) |

### Step 2 -- Bidding Tension

Four binary signals, each contributing up to 0.25 to a total score of 0-1:

| Signal | Threshold | Contribution |
|---|---|---|
| Analyst coverage | 3+ distinct analyst mentions in search results | 0.25 |
| Stock / deal movement | Recent price spike or data readout buzz | 0.25 |
| Capable buyer count | 3+ buyers with urgency >= 1.1 | 0.25 |
| TA deal velocity | 5+ deals >$1B in past 12 months in this TA | 0.25 |

Score-to-premium mapping:

| Score range | Bidding premium |
|---|---|
| 0.0 - 0.3 | 0% |
| 0.3 - 0.6 | 15% |
| 0.6 - 0.8 | 25% |
| 0.8 - 1.0 | 35% |

### Step 3 -- Three-Scenario Valuation

Each scenario outputs TWO values side-by-side:
- `if_success_bn`: what the asset is worth IF the drug succeeds (no PTRS discount)
- `risk_adjusted_bn`: expected value with PTRS probability discount applied

The gap between them shows the risk level.

#### Revenue Multiplier

Annual peak sales are converted to total commercial value using a revenue multiplier (NPV of ~10 years of revenue at 10% discount):
- **4.0x** -- standard commercial life
- **5.0x** -- orphan/rare disease (longer exclusivity, less competition)
- **3.0x** -- highly competitive markets (faster erosion)

#### NPV Discount Factor

```
npv_discount = 1 / (1.10 ^ years_to_launch)
```

Pre-computed by the synthesizer in Python before the LLM call and injected into the prompt per indication.

#### Scenario A -- Standalone NPV

Intrinsic value on the asset's own patient population:
```
commercial_value = peak_sales_standalone_bn x revenue_multiplier
if_success_bn    = SUM(commercial_value x npv_discount)       -- across indications
risk_adjusted_bn = SUM(commercial_value x ptrs_adjusted x npv_discount)
```

#### Scenario B -- Platform / Displacement

Commercial value including SOC capture or category creation:
```
commercial_value = peak_sales_with_displacement_bn x revenue_multiplier
if_success_bn    = SUM(commercial_value x npv_discount)
risk_adjusted_bn = SUM(commercial_value x ptrs_adjusted x npv_discount)
```
If multiple indications or platform potential, add 15-25% optionality premium to both values.

#### Scenario C -- Strategic Deal Price

Uses a deal_multiple on annual peak displacement sales. This is how BD bankers price actual deals.

```
deal_multiple = base_multiple(phase) + urgency_adj + bidding_adj + differentiation_adj
if_success_bn    = SUM(peak_sales_with_displacement_bn) x deal_multiple
risk_adjusted_bn = if_success_bn x weighted_average_ptrs_adjusted
```

**Base deal multiple by phase:**

| Phase | Base Multiple |
|---|---|
| Preclinical | 0.5 - 1.0x |
| Phase 1 | 1.0 - 1.5x |
| Phase 1/2 | 1.5 - 2.5x |
| Phase 2 | 2.0 - 3.5x |
| Phase 3 | 3.0 - 5.0x |
| Marketed | 4.0 - 8.0x |

**Adjustments to base multiple:**

| Condition | Adjustment |
|---|---|
| Top buyer urgency >= 1.3 | +0.3x |
| Top buyer urgency >= 1.5 | +0.5x |
| Bidding tension >= 0.6 | +0.3x |
| Bidding tension >= 0.8 | +0.5x |
| best_in_class or new_class_creation | +0.3x |
| Platform / multi-indication | +0.3x |
| me_too or worse_in_class | -0.5x |

### Step 4 -- CVR Structure Detection

If the asset has significant early-stage platform components (preclinical or Phase 1 alongside the lead) OR material approval-path milestones not yet achieved, the strategic scenario splits:

- `predicted_upfront_bn`: base value at signing
- `predicted_cvr_bn`: contingent value rights tied to milestones (typically 20-40% of total deal value)

If no CVR is warranted, `predicted_cvr_bn = 0` and `predicted_upfront_bn` equals the strategic if_success value.

### Step 5 -- Composite Score and Recommendation

```
composite_score = 0.60 x mean(science_scores) + 0.40 x mean(market_scores)
```

Adjusted +/-1 for portfolio breadth (more indications = higher ceiling).

Science is weighted higher because science risk is the primary reason BD deals fail post-signing.

| Score | Recommendation |
|---|---|
| >= 6.5 | **GO** |
| 4.5 - 6.4 | **WATCH** |
| < 4.5 | **NO-GO** |

### Synthesizer Output

```json
{
  "composite_score": 7.8,
  "science_score": 8.2,
  "market_score": 7.5,
  "recommendation": "GO",
  "summary": "3-4 sentence GP summary",
  "buyers": [
    {"name": "...", "urgency_multiplier": 1.5, "rationale": "...", "confidence": "high"}
  ],
  "bidding_tension": {
    "score": 0.75,
    "premium": 0.25,
    "signals": [{"signal": "...", "present": true, "contribution": 0.25}],
    "confidence": "high"
  },
  "scenario_standalone":   {"if_success_bn": ..., "risk_adjusted_bn": ..., "derivation_string": "..."},
  "scenario_displacement": {"if_success_bn": ..., "risk_adjusted_bn": ..., "derivation_string": "..."},
  "scenario_strategic":    {"if_success_bn": ..., "risk_adjusted_bn": ..., "deal_multiple": ...,
                            "predicted_upfront_bn": ..., "predicted_cvr_bn": ..., "derivation_string": "..."}
}
```

### Fallback on JSON Parse Error

If the synthesizer LLM output fails to parse, the Python code computes a fallback composite score from the per-indication science and market scores, assigns a recommendation based on the same thresholds, and returns empty buyer/scenario data.

---

## PTRS: Base Lookup Table and De-Risking Adjustment

PTRS values are stored in `backend/ptrs_table.json` and accessed via `backend/utils/ptrs_lookup.py`.

### Base PTRS by Phase and Therapeutic Area

| Phase | Oncology | Immunology | Neurology | Rare Disease | Cardio/Metabolic | Infectious Disease |
|---|---|---|---|---|---|---|
| Preclinical | 6.5% | 8.0% | 5.5% | 10.0% | 8.5% | 7.5% |
| IND Enabling | 10.5% | 12.0% | 9.0% | 14.0% | 11.5% | 11.0% |
| Phase 1 | 13.0% | 17.5% | 14.0% | 21.5% | 19.0% | 17.0% |
| Phase 1/2 | 18.0% | 24.0% | 18.5% | 28.0% | 24.0% | 22.0% |
| Phase 2 | 30.0% | 40.0% | 27.0% | 44.0% | 39.0% | 37.0% |
| Phase 2b | 40.0% | 50.0% | 36.0% | 54.0% | 48.0% | 46.0% |
| Phase 3 | 60.0% | 67.0% | 56.0% | 71.5% | 66.0% | 64.0% |
| NDA/BLA | 85.0% | 87.0% | 83.5% | 89.5% | 86.5% | 85.5% |

### De-Risking Signals (9 signals, fixed vocabulary)

The science agent LLM selects signals from this exact list. Any signal not in this list is filtered out in Python before PTRS computation. Each signal adds a fixed increment to the base PTRS.

| Signal | Additive Adjustment | Definition |
|---|---|---|
| `orphan_drug` | +0.02 | Has orphan drug designation from FDA or EMA |
| `fast_track` | +0.03 | Has FDA fast track designation |
| `breakthrough_designation` | +0.05 | Has FDA breakthrough therapy designation |
| `patients_dosed_50plus` | +0.03 | 50+ patients dosed in clinical program to date |
| `patients_dosed_100plus` | +0.05 | 100+ patients dosed (mutually exclusive with 50plus -- higher is used) |
| `best_in_class_efficacy` | +0.07 | Efficacy metrics meaningfully exceed current SOC benchmarks |
| `fda_registrational_alignment` | +0.04 | FDA has agreed on a registration-enabling trial design |
| `biomarker_defined_population` | +0.03 | Trial uses biomarker-selected patient population |
| `platform_multi_indication` | +0.02 | MOA/platform potentially applicable across multiple indications |

**Mutual exclusion:** If both `patients_dosed_50plus` and `patients_dosed_100plus` are present, only the +0.05 from `100plus` is applied.

**Maximum theoretical adjustment:** +0.31 (all signals except 50plus).

### Phase-Based Caps

Adjusted PTRS is hard-capped per phase to prevent unrealistic values:

| Phase | Cap |
|---|---|
| Preclinical | 0.20 |
| IND Enabling | 0.25 |
| Phase 1 | 0.45 |
| Phase 1/2 | 0.55 |
| Phase 2 | 0.65 |
| Phase 2b | 0.70 |
| Phase 3 | 0.85 |
| NDA/BLA | 0.95 |

### Phase and TA Normalization

`ptrs_lookup.py` contains alias maps that normalize free-text phase and TA strings to canonical keys:

- Phase examples: "Phase 1" -> `phase1`, "Ph2" -> `phase2`, "NDA" -> `nda_submitted`, "BLA" -> `nda_submitted`
- TA examples: "cancer" -> `oncology`, "hematology" -> `oncology`, "CNS" -> `neurology`, "MASH" -> `cardio_metabolic`, "autoimmune" -> `immunology`

If a phase or TA string is not found in the alias map, the system defaults to `phase2` and `oncology` respectively, and the base PTRS lookup returns 0.30 as a fallback.

---

## Scoring Interaction Effects

| Scenario | What happens |
|---|---|
| High science (8), low market (3) | Composite = 6.0 -> WATCH. Strong science does not overcome a small/crowded market. |
| Low science (2), high market (8) | Composite = 4.4 -> NO-GO. Strong market does not save weak biology. |
| High science (8), high market (8) | Composite = 8.0 -> GO. Strategic scenario anchors to high end of deal multiple range. |
| Single weak indication | No optionality premium. Deal multiple stays at lower end. |
| 3+ indications | 15-25% optionality premium applied by synthesizer to displacement and strategic scenarios. |
| Preclinical, unknown asset | Low PTRS base, heavy NPV discount. Per-indication risk_adjusted values are very small. Strategic deal multiple at 0.5-1.0x provides a floor. |

---

## Tuning Guide

**Science scores feel too high/low across the board:**
Adjust the scoring guide rubric in `backend/agents/science_agent.py` (the SCIENCE_PROMPT). The rubric defines what 9-10, 7-8, etc. mean.

**Market scores or peak sales feel off:**
Adjust the scoring guide in `backend/agents/market_agent.py` (the MARKET_PROMPT). Review the differentiation verdict rubric and displacement capture percentages (40-60% for best_in_class, 20-40% for better_in_class, etc.).

**Deal valuations feel too conservative:**
1. Check if Tavily is configured -- without it, all search data is empty and agents fall back to conservative LLM estimates.
2. Increase the revenue_multiplier values in the synthesizer prompt (currently 3.0-5.0x range).
3. Raise the base deal multiple ranges per phase in the synthesizer prompt.

**Deal valuations feel too aggressive:**
1. Lower the base deal multiple ranges in the synthesizer prompt.
2. Reduce displacement capture percentages in the market agent prompt.
3. Tighten the phase-based PTRS caps in `ptrs_lookup.py`.

**PTRS table needs updating:**
Edit `backend/ptrs_table.json` for base rates and `backend/utils/ptrs_lookup.py` for de-risking adjustments, caps, and alias maps.

**Buyer urgency tables need updating:**
Edit `backend/utils/buyer_context.py`. The tables include `BUYER_PATENT_CLIFFS` and `FLUSH_BUYERS`. The comment in the file says to refresh quarterly.

**Thresholds for GO/WATCH/NO-GO:**
Adjust the three threshold values in the synthesizer prompt (`backend/agents/synthesizer.py`). Run the test suite after changes to validate against known real deals.

**Composite score weights (60/40 split):**
Adjust in the synthesizer prompt. The 60% science / 40% market split reflects that science risk is the primary reason BD deals fail post-signing.

---

## Known Limitations

| Issue | Impact | Potential fix |
|---|---|---|
| Science agent cannot access paywalled journals | Misses data behind NEJM/Lancet paywalls; relies on abstracts and preprints | Add institutional access or expand preprint server coverage |
| Market agent peak sales conservative for unknown assets | When Tavily returns no asset-specific results, LLM falls back to generic TA benchmarks | Add more domain-specific search queries; improve Tavily domain list |
| All LLM outputs are JSON-parsed with no retry | A single malformed JSON response produces fallback/empty data for that agent | Add JSON repair or retry logic |
| Buyer context tables are static | Patent cliff and flush capital data becomes stale | Refresh quarterly; consider dynamic lookup |
| No caching of Tavily searches | Duplicate searches for the same asset across runs cost tokens and latency | Add Redis/file cache keyed on asset + indication + phase |
| Sequential graph means total latency is sum of all agents | ~30-60 seconds for a full run depending on Tavily and LLM response times | Cannot parallelize science and market agents because market reads ptrs_adjusted from science |
| Discovery mode is parsed but no discovery_agent node exists in the graph | Research planner can classify a query as "discovery" but the graph only runs the specific-asset pipeline | Implement a discovery_agent node or route discovery queries differently |
| Tavily domain restrictions may miss relevant sources | Each agent's search is limited to its predefined domain list | Expand or remove domain filters for broader coverage |
| LLM hallucination of de-risking signals | LLM may output signals not in the fixed vocabulary | Mitigated: Python filters to `VALID_DERISKING_SIGNALS` before PTRS computation |
| NPV discount uses fixed 10% rate | Does not account for varying cost of capital across buyers or risk profiles | Make discount rate configurable |
