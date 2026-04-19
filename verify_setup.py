"""
Verify BD Intelligence system setup.

Run this script to check that all dependencies and credentials are configured correctly.
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()


def check_env_var(var_name: str, required: bool = True) -> bool:
    value = os.getenv(var_name)
    if value:
        if "KEY" in var_name or "SECRET" in var_name or "TOKEN" in var_name:
            display = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        else:
            display = value
        print(f"  OK  {var_name}: {display}")
        return True
    else:
        status = "WARN" if not required else "FAIL"
        req_text = "(optional)" if not required else "(REQUIRED)"
        print(f"  {status} {var_name}: Not set {req_text}")
        return not required


def main():
    print("\n" + "="*80)
    print("BD INTELLIGENCE SYSTEM - SETUP VERIFICATION")
    print("="*80)

    all_good = True

    print(f"\nPython: {sys.version.split()[0]}")

    # LLM provider
    print("\nLLM Provider:")
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    print(f"  Provider: {provider}")

    if provider == "bedrock":
        all_good &= check_env_var("AWS_REGION")
        all_good &= check_env_var("AWS_BEARER_TOKEN_BEDROCK")
    else:
        all_good &= check_env_var("ANTHROPIC_API_KEY")

    try:
        from backend.config import haiku, sonnet
        print(f"  OK  Models loaded (haiku={type(haiku).__name__}, sonnet={type(sonnet).__name__})")
    except Exception as e:
        print(f"  FAIL Models: {e}")
        all_good = False

    # Tavily
    print("\nTavily Search:")
    check_env_var("TAVILY_API_KEY", required=False)

    # Dependencies
    print("\nDependencies:")
    for pkg in ["langgraph", "fastapi", "tavily"]:
        try:
            __import__(pkg)
            print(f"  OK  {pkg}")
        except ImportError:
            req = pkg != "tavily"
            print(f"  {'FAIL' if req else 'WARN'} {pkg} not installed {'(required)' if req else '(optional)'}")
            if req:
                all_good = False

    # Backend structure
    print("\nBackend:")
    try:
        from backend.state import BDState, IndicationAnalysis
        print(f"  OK  State schema (BDState + IndicationAnalysis)")
    except Exception as e:
        print(f"  FAIL State: {e}")
        all_good = False

    try:
        from backend.graph import bd_graph
        print(f"  OK  LangGraph pipeline compiled (sequential)")
    except Exception as e:
        print(f"  FAIL Graph: {e}")
        all_good = False

    try:
        from backend.utils.ptrs_lookup import get_adjusted_ptrs
        r = get_adjusted_ptrs("phase2", "oncology", ["best_in_class_efficacy"])
        print(f"  OK  PTRS adjustment (Ph2 onc + best_in_class: {r['base']} -> {r['adjusted']})")
    except Exception as e:
        print(f"  FAIL PTRS: {e}")
        all_good = False

    try:
        from backend.utils.buyer_context import get_buyer_urgency
        print(f"  OK  Buyer context (Merck urgency: {get_buyer_urgency('Merck')}x)")
    except Exception as e:
        print(f"  FAIL Buyer context: {e}")
        all_good = False

    # Summary
    print("\n" + "="*80)
    if all_good:
        print("READY")
        print("\n  Start backend:  uv run uvicorn backend.main:app --reload")
        print("  Start frontend: cd frontend && npm run dev")
        print("  Run tests:      uv run python tests/run_deal_tests.py")
    else:
        print("SETUP INCOMPLETE — fix the issues above")
    print("="*80 + "\n")

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
