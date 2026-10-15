"""
Document retriever that loads synthetic SEBI-style filings & earnings transcripts
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.rag.vector_store import SimpleVectorStore
from app.config import settings, FILINGS_DIR
import json


# Synthetic corpus (in real system this would be SEBI filings + transcripts)
SYNTHETIC_DOCUMENTS = [
    {
        "id": "REL_Q1_2025",
        "symbol": "RELIANCE",
        "title": "Reliance Industries – Q1 FY25 Earnings Transcript",
        "section": "Management Commentary",
        "text": (
            "Reliance Industries reported strong consolidated revenue growth of 12% YoY driven by "
            "robust performance in Retail and Digital Services. Jio Platforms continues expansion "
            "with subscriber addition of 8 million in the quarter. Oil-to-chemicals segment faced "
            "margin pressure due to global crack spreads. Management remains optimistic about "
            "long-term growth in new energy and 5G monetization."
        ),
    },
    {
        "id": "REL_SEBI_2024",
        "symbol": "RELIANCE",
        "title": "Reliance Industries – SEBI Corporate Filing (Annual Report Excerpt)",
        "section": "Risk Factors",
        "text": (
            "Key risks include volatility in crude oil prices, regulatory changes in telecom and "
            "retail sectors, and execution risks in new energy projects. The company maintains a "
            "strong balance sheet with net debt to EBITDA within comfortable limits. Capital "
            "expenditure guidance remains elevated for the next three years."
        ),
    },
    {
        "id": "TCS_Q2_2025",
        "symbol": "TCS",
        "title": "Tata Consultancy Services – Q2 FY25 Results",
        "section": "CEO Commentary",
        "text": (
            "TCS delivered industry-leading margins and healthy deal wins. Growth was led by "
            "Banking & Financial Services and Retail verticals. Management highlighted strong "
            "demand for AI and cloud transformation services. Attrition has stabilized and "
            "utilization remains high. Outlook for the full year is constructive with expected "
            "acceleration in discretionary spending."
        ),
    },
    {
        "id": "TCS_FILING",
        "symbol": "TCS",
        "title": "TCS – SEBI Related Party & Governance Filing",
        "section": "Governance",
        "text": (
            "The company continues to maintain high standards of corporate governance. No material "
            "related-party transactions of concern were reported. Cash generation remains strong "
            "and the board approved an interim dividend. Risks around geopolitical uncertainty "
            "and currency volatility were noted."
        ),
    },
    {
        "id": "INFY_EARNINGS",
        "symbol": "INFY",
        "title": "Infosys – Q1 FY25 Earnings Call",
        "section": "Financial Highlights",
        "text": (
            "Infosys reported modest revenue growth with sequential improvement. Large deal TCV "
            "was healthy. Management flagged softness in certain European markets and delayed "
            "decision making by clients. Margin expansion was aided by cost optimization. "
            "The company reiterated its focus on generative AI deals and digital transformation."
        ),
    },
    {
        "id": "HDFC_BANK_Q",
        "symbol": "HDFCBANK",
        "title": "HDFC Bank – Quarterly Results & SEBI Filing",
        "section": "Asset Quality",
        "text": (
            "HDFC Bank showed resilient loan growth and stable asset quality. NIMs remained "
            "under some pressure post-merger integration. Deposit mobilization has improved. "
            "Management expressed confidence in medium-term growth trajectory while cautioning "
            "about competitive intensity in retail lending."
        ),
    },
    {
        "id": "ICICI_RESULTS",
        "symbol": "ICICIBANK",
        "title": "ICICI Bank – Earnings Transcript Excerpt",
        "section": "CEO Remarks",
        "text": (
            "ICICI Bank delivered strong operating performance with healthy retail loan growth "
            "and controlled credit costs. The bank continues to gain market share in key segments. "
            "Provision coverage remains comfortable. Management highlighted opportunities in "
            "wealth management and digital banking while noting macroeconomic uncertainties."
        ),
    },
    {
        "id": "GENERIC_MARKET",
        "symbol": "NIFTY",
        "title": "Market Commentary – FII Flows & Macro",
        "section": "Macro",
        "text": (
            "Foreign Institutional Investors showed mixed flows in recent sessions. Domestic "
            "institutional support has provided a floor. Valuation multiples for large-cap IT "
            "and private banks remain reasonable relative to historical averages. Global rate "
            "trajectory and crude prices remain key swing factors for the Indian market."
        ),
    },
]


class DocumentRetriever:
    def __init__(self):
        self.store = SimpleVectorStore(model_name=settings.embedding_model)
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        # Load synthetic docs
        self.store.add_documents(SYNTHETIC_DOCUMENTS)

        # Also try loading any extra JSON files from data/filings
        if FILINGS_DIR.exists():
            for f in FILINGS_DIR.glob("*.json"):
                try:
                    with open(f) as fh:
                        extra = json.load(fh)
                        if isinstance(extra, list):
                            self.store.add_documents(extra)
                        elif isinstance(extra, dict):
                            self.store.add_documents([extra])
                except Exception:
                    pass
        self._loaded = True

    def retrieve(self, query: str, symbol: Optional[str] = None, top_k: int = 3) -> List[Dict[str, Any]]:
        self.load()
        results = self.store.search(query, top_k=top_k, symbol_filter=symbol)
        # Filter by similarity threshold if embeddings available
        return [r for r in results if r.get("score", 0) >= settings.similarity_threshold or r.get("score", 0) > 0.1]