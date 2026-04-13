"""Configuration for BD intelligence system."""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# Choose LLM provider: "anthropic" or "bedrock"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

# Model configuration - optimize for cost and performance
# - Haiku: Fast + cheap for structured tasks (parsing, lookups)
# - Sonnet: Smart for reasoning tasks (analysis, synthesis)

if LLM_PROVIDER == "bedrock":
    # AWS Bedrock configuration — uses bearer token (AWS_BEARER_TOKEN_BEDROCK)
    from langchain_aws import ChatBedrockConverse

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    logger.info(f"Using AWS Bedrock (Converse API) in region: {AWS_REGION}")

    # Fast + cheap for structured tasks (research planner)
    haiku = ChatBedrockConverse(
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        region_name=AWS_REGION,
        temperature=0.0,
        max_tokens=4096,
    )

    # Smart for reasoning tasks (science, market, synthesis)
    # Using Sonnet 4 global inference profile (Sonnet 3.7 marked legacy on this account)
    sonnet = ChatBedrockConverse(
        model="global.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=AWS_REGION,
        temperature=0.2,
        max_tokens=8192,
    )

    # Optional: Opus for most critical tasks
    # opus = ChatBedrock(
    #     model_id="us.anthropic.claude-opus-4-5-v1:0",
    #     region_name=AWS_REGION,
    #     model_kwargs={
    #         "temperature": 0.3,
    #         "max_tokens": 8192
    #     }
    # )

else:
    # Anthropic API configuration (default)
    from langchain_anthropic import ChatAnthropic

    logger.info("Using Anthropic API")

    # Get API key or use placeholder (will fail at runtime if not set)
    api_key = os.getenv("ANTHROPIC_API_KEY", "sk-ant-placeholder")
    if api_key == "sk-ant-placeholder":
        logger.warning("ANTHROPIC_API_KEY not set - API calls will fail")

    # Fast + cheap for structured tasks (research planning, PTRS lookups)
    haiku = ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=api_key,
        temperature=0.0  # Deterministic for structured tasks
    )

    # Smart for reasoning tasks (scientific analysis, market analysis, synthesis)
    sonnet = ChatAnthropic(
        model="claude-sonnet-4-5-20251001",
        api_key=api_key,
        temperature=0.2  # Slight creativity for reasoning
    )

    # Optional: Opus for most critical tasks (if needed)
    # opus = ChatAnthropic(
    #     model="claude-opus-4-5-20251101",
    #     api_key=api_key,
    #     temperature=0.3
    # )
