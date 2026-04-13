"""
Buyer urgency context for synthesis agent.
Two tables: patent cliff pressure and flush capital / platform-building buyers.
Combined urgency = max(cliff, flush) capped at 1.6x.
Last updated: 2026-04 — refresh quarterly.
"""

# Buyers under patent cliff pressure — urgency is LOE-driven
BUYER_PATENT_CLIFFS = {
    "Merck": {
        "loe_drug": "Keytruda",
        "loe_year": 2028,
        "urgency": 1.5,
        "note": "Keytruda ($25B+ revenue) faces biosimilar entry 2028; most urgent oncology acquirer",
    },
    "BMS": {
        "loe_drug": "Revlimid/Opdivo",
        "loe_year": 2028,
        "urgency": 1.3,
        "note": "Revlimid biosimilars ongoing; Opdivo checkpoint competition; active pipeline rebuilding",
    },
    "Pfizer": {
        "loe_drug": "multiple",
        "loe_year": 2027,
        "urgency": 1.2,
        "note": "Multiple LOEs by 2027; post-COVID cash deployment; broad TA interest",
    },
    "AbbVie": {
        "loe_drug": "Humira biosimilar pressure",
        "loe_year": "ongoing",
        "urgency": 1.1,
        "note": "Humira biosimilar pressure ongoing; offsetting with immunology and oncology deals",
    },
    "Novartis": {
        "loe_drug": "Entresto",
        "loe_year": 2027,
        "urgency": 1.2,
        "note": "Entresto LOE 2027; strong oncology franchise (Kymriah, Kisqali) — defends and extends",
    },
    "J&J": {
        "loe_drug": "Stelara biosimilars",
        "loe_year": 2026,
        "urgency": 1.15,
        "note": "Stelara biosimilars launched 2025-2026; oncology and immunology focus",
    },
    "AstraZeneca": {
        "loe_drug": "none major",
        "loe_year": None,
        "urgency": 1.05,
        "note": "No major near-term LOE; selective acquirer in oncology/ADC and respiratory",
    },
    "Roche": {
        "loe_drug": "staggered",
        "loe_year": None,
        "urgency": 1.1,
        "note": "Staggered LOEs; active in hematology, solid tumors, neuroscience",
    },
    "GSK": {
        "loe_drug": "staggered",
        "loe_year": None,
        "urgency": 1.1,
        "note": "Rebuilding pipeline; respiratory, oncology, HIV; moderate urgency",
    },
    "Sanofi": {
        "loe_drug": "none major",
        "loe_year": None,
        "urgency": 1.0,
        "note": "No major LOE pressure; selective deals, immunology and rare disease focus",
    },
    "Gilead": {
        "loe_drug": "HIV franchise maturing",
        "loe_year": 2027,
        "urgency": 1.2,
        "note": "HIV revenue declining; active in oncology/hematology (Kite, ADC); high deal velocity",
    },
}

# Buyers with excess capital and platform-building intent — urgency is opportunity-driven
# Signals: >20% trailing revenue growth, >3 acquisitions in 12 months, public TA expansion commentary
FLUSH_BUYERS = {
    "Eli Lilly": {
        "source": "GLP-1 (Mounjaro/Zepbound) revenue surge; declared neuroscience expansion 2025",
        "urgency": 1.3,
        "note": "Flush with GLP-1 cash; actively building neuroscience and oncology pipeline",
    },
    "Novo Nordisk": {
        "source": "Ozempic/Wegovy revenue; cardiovascular and obesity expansion",
        "urgency": 1.25,
        "note": "GLP-1 windfall; expanding into cardiometabolic adjacencies and rare disease",
    },
    "AbbVie": {
        "source": "Post-Humira recovery; strong cash generation from Skyrizi/Rinvoq",
        "urgency": 1.15,
        "note": "Recovering immunology revenue + building aesthetics and oncology; active deal pace",
    },
}

_COMBINED_CAP = 1.6  # maximum combined urgency when buyer appears in both tables


def get_buyer_urgency(buyer_name: str) -> float:
    """
    Return the effective urgency multiplier for a buyer.
    If in both tables, use max(cliff, flush) capped at 1.6x.
    """
    cliff = BUYER_PATENT_CLIFFS.get(buyer_name, {}).get("urgency", 1.0)
    flush = FLUSH_BUYERS.get(buyer_name, {}).get("urgency", 1.0)
    if cliff > 1.0 and flush > 1.0:
        return min(max(cliff, flush), _COMBINED_CAP)
    return max(cliff, flush)


def format_buyer_context_for_prompt() -> str:
    """Return formatted buyer context for synthesis agent prompt."""
    lines = ["=== Patent cliff buyers (LOE-driven urgency) ==="]
    for buyer, data in BUYER_PATENT_CLIFFS.items():
        loe_year = data["loe_year"] or "none"
        combined = get_buyer_urgency(buyer)
        lines.append(f"  {buyer}: LOE={loe_year} | cliff_urgency={data['urgency']}x | effective={combined}x | {data['note']}")

    lines.append("\n=== Flush capital buyers (opportunity-driven urgency) ===")
    for buyer, data in FLUSH_BUYERS.items():
        combined = get_buyer_urgency(buyer)
        lines.append(f"  {buyer}: flush_urgency={data['urgency']}x | effective={combined}x | {data['note']}")

    lines.append(f"\nNote: When a buyer appears in both tables, effective = max(cliff, flush) capped at {_COMBINED_CAP}x")
    return "\n".join(lines)
