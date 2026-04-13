"""
Test suite with real BD deals to validate the system.

These test cases are based on actual pharma acquisitions and should be used
to calibrate the BD intelligence system's valuation and recommendation logic.
"""
import pytest
from typing import Dict, Any


# Test Case 1: J&J / Intra-Cellular Therapies ($14.6B, Jan 2025)
TEST_1_JNJ_INTRACELLULAR = {
    "deal_name": "J&J / Intra-Cellular Therapies",
    "actual_deal_value_usd": 14_600_000_000,
    "announcement_date": "2025-01",
    "drug_asset_name": "Caplyta (lumateperone)",
    "query": "Caplyta (lumateperone) for schizophrenia (approved) and bipolar depression (approved), neurology",
    
    "expected_analysis": {
        "primary_indication": {
            "name": "Schizophrenia",
            "therapeutic_area": "neurology",
            "clinical_stage": "nda_submitted",  # Already approved
            "expected_ptrs": 0.90,  # Very high for approved drug
        },
        "secondary_indications": [
            {
                "name": "Bipolar Depression",
                "therapeutic_area": "neurology",
                "clinical_stage": "nda_submitted",  # Also approved
            }
        ],
        "market_characteristics": {
            "therapeutic_area": "CNS / Neurology",
            "market_exclusivity": "Through 2040",
            "market_size": "Large CNS market",
            "peak_sales_estimate_range": [1_500_000_000, 2_500_000_000],
        },
        "expected_recommendation": "GO",
        "expected_valuation_range": [10_000_000_000, 16_000_000_000],
        "validation_notes": [
            "This is approved asset - PTRS should be near 1.0",
            "Market agent must size CNS market correctly",
            "If system scores below $10B, it's underpricing approved assets",
            "Multiple approved indications = low risk, high certainty",
        ]
    },
    
    "test_criteria": {
        "min_ptrs": 0.80,
        "min_portfolio_value": 10_000_000_000,
        "expected_go_no_go": "GO",
        "science_score": "high",
        "market_score": "high",
    }
}


# Test Case 2: Servier / Day One Biopharmaceuticals ($2.5B, March 2026)
TEST_2_SERVIER_DAYONE = {
    "deal_name": "Servier / Day One Biopharmaceuticals",
    "actual_deal_value_usd": 2_500_000_000,
    "announcement_date": "2026-03",
    "drug_asset_name": "tovorafenib (BRAF inhibitor)",
    "query": "tovorafenib BRAF inhibitor for pediatric low-grade glioma (approved) and other BRAF-mutant tumors (phase 1), oncology, launch 2026",
    
    "expected_analysis": {
        "primary_indication": {
            "name": "Pediatric Low-Grade Glioma",
            "therapeutic_area": "oncology",
            "clinical_stage": "nda_submitted",  # FDA approved
            "expected_ptrs": 0.85,
        },
        "secondary_indications": [
            {
                "name": "Other BRAF-mutant tumors",
                "therapeutic_area": "oncology",
                "clinical_stage": "phase1",  # Earlier stage
                "notes": "Platform value - BRAF inhibitor applicable to multiple tumor types"
            },
            {
                "name": "Additional rare oncology indications",
                "therapeutic_area": "rare_disease",
                "clinical_stage": "preclinical",
            }
        ],
        "market_characteristics": {
            "therapeutic_area": "Rare Oncology",
            "market_size": "Moderate (pediatric + rare diseases)",
            "platform_value": "High - BRAF pathway relevant to multiple indications",
            "peak_sales_estimate_range": [400_000_000, 800_000_000],
        },
        "expected_recommendation": "GO",
        "expected_valuation_range": [2_000_000_000, 3_500_000_000],
        "validation_notes": [
            "BEST multi-indication waterfall test",
            "Lead asset approved (de-risked) + early pipeline (optionality)",
            "Platform value beyond lead is real but early",
            "Optionality premium should be significant (multiple shots on goal)",
            "Tests ability to value preclinical pipeline appropriately",
        ]
    },
    
    "test_criteria": {
        "min_ptrs": 0.80,  # For primary
        "min_portfolio_value": 2_000_000_000,
        "max_portfolio_value": 3_500_000_000,
        "expected_go_no_go": "GO",
        "secondary_indications_count": "≥2",
        "optionality_premium_pct": "≥10%",
    }
}


# Test Case 3: Novo Nordisk / Akero Therapeutics ($5.2B, Oct 2025)
TEST_3_NOVO_AKERO = {
    "deal_name": "Novo Nordisk / Akero Therapeutics",
    "actual_deal_value_usd": 5_200_000_000,
    "announcement_date": "2025-10",
    "drug_asset_name": "efruxifermin",
    "query": "efruxifermin for MASH metabolic dysfunction-associated steatohepatitis phase 3 and liver fibrosis phase 2, cardio-metabolic, launch 2027",
    
    "expected_analysis": {
        "primary_indication": {
            "name": "MASH (Metabolic dysfunction-associated steatohepatitis)",
            "therapeutic_area": "cardio_metabolic",  # Map to this TA
            "clinical_stage": "phase3",
            "expected_ptrs": 0.66,  # Phase 3 cardio_metabolic
            "notes": "MASH is emerging indication - not in traditional PTRS tables",
        },
        "secondary_indications": [
            # May have earlier-stage programs
        ],
        "market_characteristics": {
            "therapeutic_area": "Metabolic Disease / MASH",
            "market_size": "Very Large - MASH affects millions globally",
            "competitive_landscape": "Emerging field, high unmet need",
            "peak_sales_estimate_range": [3_000_000_000, 6_000_000_000],
            "analyst_sentiment": "Transformational (Evercore ISI)",
        },
        "expected_recommendation": "GO",
        "expected_valuation_range": [4_000_000_000, 6_500_000_000],
        "validation_notes": [
            "Tests market agent's ability to handle EMERGING indications",
            "MASH wasn't in traditional PTRS tables - use cardio_metabolic lookup",
            "Phase 3 asset with high PTRS",
            "Large addressable market (epidemic-scale disease)",
            "Called 'transformational' by analysts - sentiment matters",
        ]
    },
    
    "test_criteria": {
        "therapeutic_area_mapping": "cardio_metabolic",
        "min_ptrs": 0.60,
        "min_portfolio_value": 4_000_000_000,
        "expected_go_no_go": "GO",
        "market_size": "large",
    }
}


# Test Case 4: Jazz / Chimerix ($935M, March 2025)
TEST_4_JAZZ_CHIMERIX = {
    "deal_name": "Jazz Pharmaceuticals / Chimerix",
    "actual_deal_value_usd": 935_000_000,
    "announcement_date": "2025-03",
    "drug_asset_name": "dordaviprone",
    "query": "dordaviprone for H3 K27M-mutant diffuse glioma NDA submitted, rare disease oncology, launch 2025",
    
    "expected_analysis": {
        "primary_indication": {
            "name": "H3 K27M-mutant Diffuse Glioma",
            "therapeutic_area": "rare_disease",  # or "oncology"
            "clinical_stage": "nda_submitted",
            "expected_ptrs": 0.895,  # NDA submitted, rare disease
            "notes": "First-in-class for rare high-grade brain tumor, no approved therapies",
        },
        "secondary_indications": [],  # Likely none - ultra-rare single indication
        "market_characteristics": {
            "therapeutic_area": "Rare Disease / Neuro-Oncology",
            "market_size": "Very Small - ultra-rare patient population",
            "unmet_need": "Extreme - no FDA-approved therapies",
            "orphan_drug_status": "Likely",
            "patient_population": "<1,000 patients per year",
            "peak_sales_estimate_range": [150_000_000, 300_000_000],
        },
        "expected_recommendation": "GO",
        "expected_valuation_range": [700_000_000, 1_200_000_000],
        "validation_notes": [
            "RARE DISEASE / SMALL MARKET test",
            "NDA submitted → high PTRS (~88%)",
            "Tiny patient population → modest peak sales",
            "Should output sub-$1B range",
            "If system outputs $3B+ something is wrong with prevalence estimation",
            "Orphan drug pricing can be high but volume is very low",
            "First-in-class + no competition = pricing power but small market",
        ]
    },
    
    "test_criteria": {
        "min_ptrs": 0.85,
        "max_portfolio_value": 1_500_000_000,  # Should NOT exceed this
        "expected_go_no_go": "GO",
        "market_size": "small",
        "validation_alert": "If valuation > $2B, prevalence model is broken",
    }
}


# Aggregate test cases
REAL_DEAL_TEST_CASES = [
    TEST_1_JNJ_INTRACELLULAR,
    TEST_2_SERVIER_DAYONE,
    TEST_3_NOVO_AKERO,
    TEST_4_JAZZ_CHIMERIX,
]


def test_case_summary():
    """Print summary of all test cases."""
    print("\n" + "="*80)
    print("BD INTELLIGENCE SYSTEM - REAL DEAL TEST CASES")
    print("="*80)
    
    for i, test_case in enumerate(REAL_DEAL_TEST_CASES, 1):
        print(f"\nTest {i}: {test_case['deal_name']}")
        print(f"  Actual Deal Value: ${test_case['actual_deal_value_usd']:,.0f}")
        print(f"  Date: {test_case['announcement_date']}")
        print(f"  Asset: {test_case['drug_asset_name']}")
        
        expected = test_case['expected_analysis']
        print(f"  Primary: {expected['primary_indication']['name']}")
        print(f"  Stage: {expected['primary_indication']['clinical_stage']}")
        print(f"  TA: {expected['primary_indication']['therapeutic_area']}")
        
        if expected.get('secondary_indications'):
            print(f"  Secondary Indications: {len(expected['secondary_indications'])}")
        
        val_range = expected['expected_valuation_range']
        print(f"  Expected Valuation: ${val_range[0]:,.0f} - ${val_range[1]:,.0f}")
        print(f"  Recommendation: {expected['expected_recommendation']}")
        
        if expected.get('validation_notes'):
            print(f"  Key Tests:")
            for note in expected['validation_notes'][:2]:
                print(f"    • {note}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    test_case_summary()
