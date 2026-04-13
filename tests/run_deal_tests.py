"""
Test runner for real BD deal validation.

Calls the live /analyze endpoint (real agents + Tavily + Bedrock) and
compares the output against known deal benchmarks. No hardcoded answers.
"""
import asyncio
import json
import sys
from typing import Dict, Any
import httpx
from tests.test_real_deals import REAL_DEAL_TEST_CASES


def _recommendation_from_score(score: float | None) -> str:
    if score is None:
        return "UNKNOWN"
    if score >= 6.5:
        return "GO"
    if score >= 4.5:
        return "WATCH"
    return "NO-GO"


class DealTestRunner:
    """Run BD intelligence system against real deal test cases."""

    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results = []

    async def run_test_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Call the live /analyze endpoint and validate the result."""
        print(f"\n{'='*80}")
        print(f"Testing: {test_case['deal_name']}")
        print(f"Asset: {test_case['drug_asset_name']}")
        print(f"Actual Deal Value: ${test_case['actual_deal_value_usd'] / 1e9:.2f}B")
        print(f"Query: {test_case['query']}")
        print(f"{'='*80}")

        # Call the live agent pipeline — no stubs, no hardcoded answers
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/analyze",
                    json={"message": test_case["query"], "filters": {}},
                )
                response.raise_for_status()
                api_response = response.json()
            except Exception as e:
                print(f"API Error: {e}")
                return {
                    "test_case": test_case["deal_name"],
                    "status": "error",
                    "error": str(e),
                    "actual_deal_value": test_case["actual_deal_value_usd"],
                }

        result = api_response.get("result") or {}

        # Extract values from live response
        deal_low_bn = result.get("dealRangeLow")   # in $B
        deal_high_bn = result.get("dealRangeHigh") # in $B
        score = result.get("score")
        science_score = result.get("scienceScore")
        market_score = result.get("marketScore")
        indications = result.get("indications", [])
        summary = result.get("summary", "")
        recommendation = _recommendation_from_score(score)

        # Expected benchmarks (from actual deals)
        expected = test_case["expected_analysis"]
        expected_range_usd = expected["expected_valuation_range"]   # in raw $
        expected_range_bn = [v / 1e9 for v in expected_range_usd]  # convert to $B
        expected_rec = expected["expected_recommendation"]
        criteria = test_case["test_criteria"]

        # --- Validate ---
        validations = {}

        # Deal range: use midpoint of [low, high] vs expected range
        if deal_low_bn is not None and deal_high_bn is not None:
            midpoint = (deal_low_bn + deal_high_bn) / 2
            in_range = expected_range_bn[0] <= midpoint <= expected_range_bn[1]
            validations["deal_range_in_expected"] = in_range
            validations["deal_low_bn"] = deal_low_bn
            validations["deal_high_bn"] = deal_high_bn
            validations["midpoint_bn"] = midpoint
            validations["expected_range_bn"] = expected_range_bn
            actual_bn = test_case["actual_deal_value_usd"] / 1e9
            validations["error_vs_actual_pct"] = abs(midpoint - actual_bn) / actual_bn * 100
        else:
            validations["deal_range_in_expected"] = False
            validations["error"] = "No deal range returned"

        # Recommendation
        validations["recommendation_correct"] = (recommendation == expected_rec)
        validations["recommendation"] = recommendation
        validations["score"] = score

        # Min PTRS on primary indication
        if criteria.get("min_ptrs") and indications:
            primary_ptrs = indications[0].get("ptrs")
            if primary_ptrs is not None:
                validations["ptrs_ok"] = primary_ptrs >= criteria["min_ptrs"]
                validations["primary_ptrs"] = primary_ptrs

        # Max deal cap (rare disease guard)
        if criteria.get("max_portfolio_value") and deal_high_bn is not None:
            cap_bn = criteria["max_portfolio_value"] / 1e9
            validations["under_cap"] = deal_high_bn <= cap_bn

        # --- Print results ---
        print(f"\nRESULTS:")
        if deal_low_bn is not None and deal_high_bn is not None:
            print(f"  System deal range : ${deal_low_bn:.2f}B – ${deal_high_bn:.2f}B  (midpoint ${validations['midpoint_bn']:.2f}B)")
        print(f"  Expected range    : ${expected_range_bn[0]:.2f}B – ${expected_range_bn[1]:.2f}B")
        print(f"  Actual deal value : ${test_case['actual_deal_value_usd'] / 1e9:.2f}B")

        if validations.get("deal_range_in_expected"):
            print(f"  Deal range: PASS (error vs actual: {validations.get('error_vs_actual_pct', 0):.1f}%)")
        else:
            print(f"  Deal range: FAIL")

        print(f"\n  Score             : {score}/10  (science={science_score}, market={market_score})")
        print(f"  Recommendation    : {recommendation} (expected: {expected_rec})")
        if validations.get("recommendation_correct"):
            print(f"  Recommendation: PASS")
        else:
            print(f"  Recommendation: FAIL")

        if "primary_ptrs" in validations:
            print(f"  Primary PTRS      : {validations['primary_ptrs']:.2f} (min: {criteria['min_ptrs']})")
            print(f"  PTRS: {'PASS' if validations.get('ptrs_ok') else 'FAIL'}")

        print(f"\n  Indications found : {len(indications)}")
        for ind in indications:
            print(f"    - {ind['name']} | {ind['phase']} | ptrs={ind.get('ptrs')} | peak_sales=${ind.get('peakSalesBn')}B")

        if summary:
            print(f"\n  Summary: {summary[:200]}...")

        print(f"\n  Validation notes:")
        for note in expected.get("validation_notes", [])[:3]:
            print(f"    • {note}")

        # Overall pass/fail
        required_checks = [
            validations.get("deal_range_in_expected", False),
            validations.get("recommendation_correct", False),
        ]
        if "ptrs_ok" in validations:
            required_checks.append(validations["ptrs_ok"])
        if "under_cap" in validations:
            required_checks.append(validations["under_cap"])

        passed = all(required_checks)
        print(f"\n{'PASS' if passed else 'FAIL'}: {test_case['deal_name']}")

        return {
            "test_case": test_case["deal_name"],
            "status": "passed" if passed else "failed",
            "actual_deal_value": test_case["actual_deal_value_usd"],
            "deal_low_bn": deal_low_bn,
            "deal_high_bn": deal_high_bn,
            "score": score,
            "recommendation": recommendation,
            "validations": validations,
            "indications_count": len(indications),
            "full_response": api_response,
        }

    async def run_all_tests(self):
        """Run all test cases and print summary."""
        print("\n" + "=" * 80)
        print("BD INTELLIGENCE — REAL DEAL VALIDATION (live agents)")
        print("=" * 80)
        print(f"API: {self.api_url}")
        print(f"Test cases: {len(REAL_DEAL_TEST_CASES)}")

        for test_case in REAL_DEAL_TEST_CASES:
            result = await self.run_test_case(test_case)
            self.results.append(result)

        self._print_summary()

        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\nFull results saved to: test_results.json")

    def _print_summary(self):
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        errors = sum(1 for r in self.results if r["status"] == "error")

        print(f"\nPassed: {passed}/{len(self.results)}  |  Failed: {failed}  |  Errors: {errors}")

        print(f"\n{'Deal':<42} {'Actual':>8} {'System Low':>11} {'System High':>12} {'Status':>8}")
        print("-" * 85)

        for r in self.results:
            name = r["test_case"][:40]
            actual = f"${r['actual_deal_value'] / 1e9:.1f}B"
            if r["status"] == "error":
                low = high = "ERROR"
                status = "ERROR"
            else:
                low = f"${r['deal_low_bn']:.1f}B" if r.get("deal_low_bn") else "N/A"
                high = f"${r['deal_high_bn']:.1f}B" if r.get("deal_high_bn") else "N/A"
                status = "PASS" if r["status"] == "passed" else "FAIL"
            print(f"{name:<42} {actual:>8} {low:>11} {high:>12} {status:>8}")


async def main():
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    runner = DealTestRunner(api_url=api_url)
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
