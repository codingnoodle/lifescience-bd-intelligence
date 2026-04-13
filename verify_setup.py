"""
Verify BD Intelligence system setup.

Run this script to check that all dependencies and credentials are configured correctly.
"""
import os
import sys
from dotenv import load_dotenv
load_dotenv()


def check_env_var(var_name: str, required: bool = True) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if "KEY" in var_name or "SECRET" in var_name:
            display = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
        else:
            display = value
        print(f"  ✅ {var_name}: {display}")
        return True
    else:
        status = "⚠️" if not required else "❌"
        req_text = "(optional)" if not required else "(REQUIRED)"
        print(f"  {status} {var_name}: Not set {req_text}")
        return not required


def main():
    print("\n" + "="*80)
    print("BD INTELLIGENCE SYSTEM - SETUP VERIFICATION")
    print("="*80)
    
    all_good = True
    
    # Check Python version
    print("\n📦 Python Environment:")
    print(f"  ✅ Python {sys.version.split()[0]}")
    
    # Check LLM provider
    print("\n🤖 LLM Provider:")
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    print(f"  Provider: {provider}")
    
    if provider == "bedrock":
        print("\n☁️ AWS Bedrock Configuration:")
        all_good &= check_env_var("AWS_REGION")
        all_good &= check_env_var("AWS_BEARER_TOKEN_BEDROCK")
        
        # Try to load Bedrock config
        try:
            from backend.config import haiku, sonnet
            print(f"  ✅ Bedrock models loaded")
            print(f"     - Haiku: {type(haiku).__name__}")
            print(f"     - Sonnet: {type(sonnet).__name__}")
        except Exception as e:
            print(f"  ❌ Failed to load Bedrock models: {e}")
            all_good = False
    else:
        print("\n🔑 Anthropic API Configuration:")
        all_good &= check_env_var("ANTHROPIC_API_KEY")
        
        # Try to load Anthropic config
        try:
            from backend.config import haiku, sonnet
            print(f"  ✅ Anthropic models loaded")
            print(f"     - Haiku: {type(haiku).__name__}")
            print(f"     - Sonnet: {type(sonnet).__name__}")
        except Exception as e:
            print(f"  ❌ Failed to load Anthropic models: {e}")
            all_good = False
    
    # Check Tavily
    print("\n🔍 Tavily Search:")
    tavily_set = check_env_var("TAVILY_API_KEY", required=False)
    if tavily_set:
        try:
            from backend.tools.langchain_tools import get_tools
            tools = get_tools()
            if tools:
                print(f"  ✅ Web search tool enabled ({len(tools)} tools)")
            else:
                print(f"  ⚠️ No tools enabled (TAVILY_API_KEY set but not used)")
        except Exception as e:
            print(f"  ❌ Failed to load tools: {e}")
    else:
        print(f"  ⚠️ Web search disabled - agents won't be able to search for data")
    
    # Check dependencies
    print("\n📚 Dependencies:")
    try:
        import importlib.metadata
        import langgraph
        version = importlib.metadata.version("langgraph")
        print(f"  ✅ langgraph {version}")
    except:
        print(f"  ❌ langgraph not installed")
        all_good = False
    
    try:
        import fastapi
        print(f"  ✅ fastapi {fastapi.__version__}")
    except:
        print(f"  ❌ fastapi not installed")
        all_good = False
    
    try:
        import tavily
        print(f"  ✅ tavily-python installed")
    except:
        print(f"  ⚠️ tavily-python not installed (optional)")
    
    # Check backend structure
    print("\n📁 Backend Structure:")
    try:
        from backend.state import BDState, Indication, PortfolioValuation
        print(f"  ✅ State models loaded")
    except Exception as e:
        print(f"  ❌ State models failed: {e}")
        all_good = False
    
    try:
        from backend.graph import bd_graph
        print(f"  ✅ LangGraph workflow compiled")
    except Exception as e:
        print(f"  ❌ Graph compilation failed: {e}")
        all_good = False
    
    try:
        from backend.utils import PTRSCalculator
        calc = PTRSCalculator()
        ptrs = calc.get_ptrs("phase3", "oncology")
        print(f"  ✅ PTRS calculator working (Phase 3 Oncology: {ptrs})")
    except Exception as e:
        print(f"  ❌ PTRS calculator failed: {e}")
        all_good = False
    
    # Summary
    print("\n" + "="*80)
    if all_good:
        print("✅ SYSTEM READY")
        print("\nNext steps:")
        print("  1. Start API: uv run uvicorn backend.main:app --reload")
        print("  2. Test endpoint: curl http://localhost:8000/")
        print("  3. Run tests: uv run python tests/test_real_deals.py")
    else:
        print("❌ SETUP INCOMPLETE")
        print("\nPlease fix the issues above before running the system.")
        print("\nCommon fixes:")
        print("  - Add missing credentials to .env file")
        print("  - Run: uv sync")
        print("  - Check AWS Bedrock model access in AWS Console")
    print("="*80 + "\n")
    
    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
