"""
Simple in-memory vector store – pure Python keyword search.
No sentence-transformers / torch / torchvision required.
"""
from typing import List, Dict, Any, Optional


class SimpleVectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.documents: List[Dict[str, Any]] = []

    def add_documents(self, docs: List[Dict[str, Any]]):
        """docs: list of {id, title, text, symbol, section, ...}"""
        self.documents.extend(docs)

    def search(self, query: str, top_k: int = 3, symbol_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        indices = list(range(len(self.documents)))
        if symbol_filter:
            sym = symbol_filter.replace(".NS", "").upper()
            indices = [
                i for i, d in enumerate(self.documents)
                if sym in d.get("symbol", "").upper() or sym in d.get("title", "").upper()
            ]
            if not indices:
                indices = list(range(len(self.documents)))

        # Keyword overlap scoring
        query_terms = set(query.lower().split())
        scored = []
        for i in indices:
            d = self.documents[i]
            text_terms = set(d["text"].lower().split())
            score = len(query_terms & text_terms) / max(1, len(query_terms))
            scored.append((score, i))
        scored.sort(reverse=True)

        results = []
        for score, i in scored[:top_k]:
            d = self.documents[i].copy()
            d["score"] = float(score)
            results.append(d)
        return results