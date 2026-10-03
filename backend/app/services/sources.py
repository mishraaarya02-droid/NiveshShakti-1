"""Official-source adapters that never infer claim truth from reachability."""
from abc import ABC, abstractmethod
from typing import Any, Dict
from urllib.parse import urlparse

import httpx

from ..models import VerificationStatus


def claim_status_for_retrieval(retrieval_status: str) -> VerificationStatus:
    if retrieval_status == "SOURCE_UNAVAILABLE":
        return VerificationStatus.SOURCE_UNAVAILABLE
    return VerificationStatus.UNVERIFIED


class SourceAdapter(ABC):
    source_type = "regulatory"

    def __init__(self, code: str, name: str, official_url: str, manual_url: str):
        self.code = code
        self.name = name
        self.official_url = official_url
        self.manual_url = manual_url

    async def search(self, query: str) -> Dict[str, Any]:
        return {
            "status": claim_status_for_retrieval("SOURCE_UNAVAILABLE"),
            "retrieval_status": "SOURCE_UNAVAILABLE",
            "evidence_text": (
                f"Automated exact-record search is not available through a documented public interface for {self.name}. "
                "Use the official manual verification route; no match or fraud conclusion was produced."
            ),
            "query_used": query,
            "source_url": self.manual_url,
            "source_published_at": None,
            "source_version": None,
        }

    async def verify(self, query: str, entity_type: str = "REG_NUMBER") -> Dict[str, Any]:
        return await self.search(query)

    async def retrieve(self) -> Dict[str, Any]:
        parsed = urlparse(self.official_url)
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=False) as client:
                response = await client.get(
                    self.official_url,
                    headers={"User-Agent": "NiveshShakti-SourceHealth/1.0"},
                )
            reachable = 200 <= response.status_code < 400
            return {
                "retrieval_status": "AVAILABLE" if reachable else "UNAVAILABLE",
                "health_status": "AVAILABLE" if reachable else "DEGRADED",
                "last_error": None if reachable else f"Official site returned HTTP {response.status_code}.",
                "source_url": f"{parsed.scheme}://{parsed.netloc}",
            }
        except httpx.HTTPError:
            return {
                "retrieval_status": "UNAVAILABLE",
                "health_status": "UNAVAILABLE",
                "last_error": "Official source could not be reached.",
                "source_url": f"{parsed.scheme}://{parsed.netloc}",
            }

    async def health_check(self) -> str:
        result = await self.retrieve()
        return result["health_status"]

    async def check_health(self) -> str:
        return await self.health_check()


class SEBIIntermediaryAdapter(SourceAdapter):
    def __init__(self):
        super().__init__(
            "SEBI_INTERMEDIARIES",
            "SEBI Registered Intermediaries",
            "https://www.sebi.gov.in/intermediaries.html",
            "https://www.sebi.gov.in/intermediaries.html",
        )


class SEBIInvestorAdapter(SourceAdapter):
    source_type = "investor_support"

    def __init__(self):
        super().__init__(
            "SEBI_INVESTOR",
            "SEBI Investor Support",
            "https://investor.sebi.gov.in/Investor-support.html",
            "https://investor.sebi.gov.in/Investor-support.html",
        )


class NSDLAdapter(SourceAdapter):
    source_type = "depository"

    def __init__(self):
        super().__init__("NSDL", "National Securities Depository Limited", "https://nsdl.co.in/", "https://nsdl.co.in/")


class RBISachetAdapter(SourceAdapter):
    def __init__(self):
        super().__init__("RBI_SACHET", "RBI Sachet", "https://sachet.rbi.org.in/", "https://sachet.rbi.org.in/")


ADAPTER_REGISTRY = {
    adapter.code: adapter
    for adapter in (
        SEBIIntermediaryAdapter(),
        SEBIInvestorAdapter(),
        NSDLAdapter(),
        RBISachetAdapter(),
    )
}
