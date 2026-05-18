"""PubMed E-utilities API client for retrieving published literature."""
import httpx
import logging
from xml.etree import ElementTree

logger = logging.getLogger(__name__)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def search_pubmed(query: str, max_results: int = 8) -> list[dict]:
    """
    Search PubMed for articles matching a query.
    Returns list of dicts with pmid, title, abstract, journal, year.
    """
    headers = {"User-Agent": "bd-intelligence/1.0 (research tool)"}
    try:
        with httpx.Client(timeout=15, headers=headers) as client:
            search_resp = client.get(ESEARCH_URL, params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            })
            search_resp.raise_for_status()
            pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])
            if not pmids:
                return []

            fetch_resp = client.get(EFETCH_URL, params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
            })
            fetch_resp.raise_for_status()
            return _parse_articles(fetch_resp.text)
    except Exception as e:
        logger.error(f"PubMed search failed for '{query}': {e}")
        return []


def _parse_articles(xml_text: str) -> list[dict]:
    """Parse PubMed XML response into simplified article dicts."""
    articles = []
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []

    for article_el in root.findall(".//PubmedArticle"):
        medline = article_el.find("MedlineCitation")
        if medline is None:
            continue

        pmid_el = medline.find("PMID")
        article = medline.find("Article")
        if article is None:
            continue

        title_el = article.find("ArticleTitle")
        abstract_el = article.find("Abstract/AbstractText")
        journal_el = article.find("Journal/Title")
        year_el = article.find("Journal/JournalIssue/PubDate/Year")

        articles.append({
            "pmid": pmid_el.text if pmid_el is not None else "",
            "title": title_el.text if title_el is not None else "",
            "abstract": (abstract_el.text or "")[:800] if abstract_el is not None else "",
            "journal": journal_el.text if journal_el is not None else "",
            "year": year_el.text if year_el is not None else "",
        })
    return articles


def format_pubmed_for_prompt(articles: list[dict]) -> str:
    """Format PubMed articles as readable text for LLM prompt."""
    if not articles:
        return "No PubMed results found."
    lines = []
    for a in articles:
        lines.append(
            f"- [PMID {a['pmid']}] {a['title']}\n"
            f"  Journal: {a['journal']} ({a['year']})\n"
            f"  Abstract: {a['abstract'][:400]}"
        )
    return "\n\n".join(lines)
