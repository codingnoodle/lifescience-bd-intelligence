"""
Test runner for real BD deal validation.

Calls the live /analyze endpoint and compares three-scenario output
against known deal benchmarks. No hardcoded answers.
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
        print(f"{'='*80}")

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

        # Extract three-scenario values
        standalone = result.get("scenarioStandalone") or {}
        displacement = result.get("scenarioDisplacement") or {}
        strategic = result.get("scenarioStrategic") or {}

        strategic_success = strategic.get("ifSuccessBn")
        strategic_risk = strategic.get("riskAdjustedBn")
        displacement_success = displacement.get("ifSuccessBn")
        standalone_success = standalone.get("ifSuccessBn")

        score = result.get("compositeScore") or result.get("score")
        science_score = result.get("scienceScore")
        market_score = result.get("marketScore")
        recommendation = result.get("recommendation") or _recommendation_from_score(score)
        indications = result.get("indications", [])
        buyers = result.get("buyers", [])
        summary = result.get("summary", "")

        # Expected benchmarks
        expected = test_case["expected_analysis"]
        expected_range_usd = expected["expected_valuation_range"]
        expected_range_bn = [v / 1e9 for v in expected_range_usd]
        expected_rec = expected["expected_recommendation"]
        criteria = test_case["test_criteria"]

        # --- Validate ---
        validations = {}
        actual_bn = test_case["actual_deal_value_usd"] / 1e9

        # Strategic if-succeed vs expected range
        if strategic_success is not None:
            in_range = expected_range_bn[0] <= strategic_success <= expected_range_bn[1]
            validations["strategic_in_range"] = in_range
            validations["strategic_success_bn"] = strategic_success
            validations["strategic_risk_bn"] = strategic_risk
            validations["error_vs_actual_pct"] = abs(strategic_success - actual_bn) / actual_bn * 100
        else:
            validations["strategic_in_range"] = False
            validations["error"] = "No strategic scenario returned"

        # Recommendation
        validations["recommendation_correct"] = (recommendation == expected_rec)
        validations["recommendation"] = recommendation
        validations["score"] = score

        # Min PTRS on primary indication
        if criteria.get("min_ptrs") and indications:
            primary_ptrs = indications[0].get("ptrsAdjusted") or indications[0].get("ptrs")
            if primary_ptrs is not None:
                validations["ptrs_ok"] = primary_ptrs >= criteria["min_ptrs"]
                validations["primary_ptrs"] = primary_ptrs

        # Max deal cap (rare disease guard)
        if criteria.get("max_portfolio_value") and strategic_success is not None:
            cap_bn = criteria["max_portfolio_value"] / 1e9
            validations["under_cap"] = strategic_success <= cap_bn

        # --- Print results ---
        print(f"\nTHREE-SCENARIO OUTPUT:")
        print(f"  Standalone     : if-succeed ${standalone_success or 0:.2f}B")
        print(f"  Displacement   : if-succeed ${displacement_success or 0:.2f}B")
        print(f"  Strategic      : if-succeed ${strategic_success or 0:.2f}B  |  risk-adj ${strategic_risk or 0:.2f}B")
        print(f"  Expected range : ${expected_range_bn[0]:.1f}B - ${expected_range_bn[1]:.1f}B")
        print(f"  Actual deal    : ${actual_bn:.2f}B")

        if validations.get("strategic_in_range"):
            print(f"  Strategic: PASS (error vs actual: {validations.get('error_vs_actual_pct', 0):.1f}%)")
        else:
            print(f"  Strategic: FAIL")

        print(f"\n  Score          : {score}/10  (science={science_score}, market={market_score})")
        print(f"  Recommendation : {recommendation} (expected: {expected_rec})")
        print(f"  Recommendation : {'PASS' if validations.get('recommendation_correct') else 'FAIL'}")

        if "primary_ptrs" in validations:
            print(f"  Primary PTRS   : {validations['primary_ptrs']:.3f} (min: {criteria['min_ptrs']})")
            print(f"  PTRS           : {'PASS' if validations.get('ptrs_ok') else 'FAIL'}")

        print(f"\n  Indications    : {len(indications)}")
        for ind in indications:
            verdict = ind.get("differentiationVerdict", "")
            ptrs = ind.get("ptrsAdjusted") or ind.get("ptrs")
            peak = ind.get("peakSalesWithDisplacementBn") or ind.get("peakSalesBn")
            print(f"    - {ind['name']} | {ind['phase']} | ptrs={ptrs} | peak=${peak}B | {verdict}")

        if buyers:
            print(f"\n  Buyers:")
            for b in buyers:
                print(f"    - {b.get('name')} {b.get('urgencyMultiplier', '')}x")

        if summary:
            print(f"\n  Summary: {summary[:200]}...")

        # Overall pass/fail
        required_checks = [
            validations.get("strategic_in_range", False),
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
            "strategic_success_bn": strategic_success,
            "strategic_risk_bn": strategic_risk,
            "score": score,
            "recommendation": recommendation,
            "validations": validations,
            "indications_count": len(indications),
            "buyers_count": len(buyers),
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

        print(f"\n{'Deal':<42} {'Actual':>8} {'If-succeed':>11} {'Risk-adj':>10} {'Status':>8}")
        print("-" * 85)

        for r in self.results:
            name = r["test_case"][:40]
            actual = f"${r['actual_deal_value'] / 1e9:.1f}B"
            if r["status"] == "error":
                success = risk = "ERROR"
                status = "ERROR"
            else:
                success = f"${r['strategic_success_bn']:.1f}B" if r.get("strategic_success_bn") else "N/A"
                risk = f"${r['strategic_risk_bn']:.1f}B" if r.get("strategic_risk_bn") else "N/A"
                status = "PASS" if r["status"] == "passed" else "FAIL"
            print(f"{name:<42} {actual:>8} {success:>11} {risk:>10} {status:>8}")


async def main():
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    runner = DealTestRunner(api_url=api_url)
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
