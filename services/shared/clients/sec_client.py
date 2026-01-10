# =============================================================================
# SEC EDGAR API Client
# =============================================================================
# Client for fetching SEC filings and regulatory data
# =============================================================================

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from functools import lru_cache

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class SECFiling(BaseModel):
    """SEC filing metadata."""
    accession_number: str
    filing_date: date
    report_date: Optional[date] = None
    form_type: str
    primary_document: str
    primary_doc_description: Optional[str] = None
    items: List[str] = Field(default_factory=list)
    size: Optional[int] = None
    is_xbrl: bool = False
    is_inline_xbrl: bool = False


class Form4Filing(BaseModel):
    """SEC Form 4 insider trading filing."""
    accession_number: str
    filing_date: date
    issuer_cik: str
    issuer_name: str
    issuer_ticker: Optional[str] = None
    owner_cik: str
    owner_name: str
    is_director: bool = False
    is_officer: bool = False
    is_ten_percent_owner: bool = False
    officer_title: Optional[str] = None
    transactions: List[Dict[str, Any]] = Field(default_factory=list)


class Form13FFiling(BaseModel):
    """SEC Form 13F institutional holdings filing."""
    accession_number: str
    filing_date: date
    report_date: date
    filer_cik: str
    filer_name: str
    total_value: float
    holdings_count: int
    holdings: List[Dict[str, Any]] = Field(default_factory=list)


class CompanyFacts(BaseModel):
    """Company XBRL facts from SEC."""
    cik: str
    entity_name: str
    facts: Dict[str, Any]


# =============================================================================
# SEC Client
# =============================================================================

class SECClient:
    """
    Client for SEC EDGAR API.
    
    Provides access to:
    - Company filings (10-K, 10-Q, 8-K, etc.)
    - Insider trading (Form 4)
    - Institutional holdings (Form 13F)
    - XBRL financial facts
    - Full-text filing search
    """
    
    BASE_URL = "https://data.sec.gov"
    SUBMISSIONS_URL = f"{BASE_URL}/submissions"
    COMPANY_FACTS_URL = f"{BASE_URL}/api/xbrl/companyfacts"
    FULL_TEXT_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
    
    # SEC requires a User-Agent header with contact info
    USER_AGENT = "Investment-Agent-System contact@example.com"
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self._headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json"
        }
    
    def _format_cik(self, cik: str) -> str:
        """Format CIK to 10 digits with leading zeros."""
        return cik.zfill(10)
    
    async def _request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make an API request to SEC."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # Company Filings
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_company_filings(
        self,
        cik: str,
        form_types: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[SECFiling]:
        """
        Get recent filings for a company.
        
        Args:
            cik: Company CIK number
            form_types: Filter by form types (e.g., ["10-K", "10-Q"])
            limit: Maximum number of filings to return
            
        Returns:
            List of SECFiling objects
        """
        cik = self._format_cik(cik)
        url = f"{self.SUBMISSIONS_URL}/CIK{cik}.json"
        
        data = await self._request(url)
        
        filings = []
        recent = data.get("filings", {}).get("recent", {})
        
        for i in range(min(limit, len(recent.get("accessionNumber", [])))):
            form_type = recent["form"][i]
            
            # Filter by form type if specified
            if form_types and form_type not in form_types:
                continue
            
            filing = SECFiling(
                accession_number=recent["accessionNumber"][i],
                filing_date=recent["filingDate"][i],
                report_date=recent.get("reportDate", [None])[i] if recent.get("reportDate") else None,
                form_type=form_type,
                primary_document=recent["primaryDocument"][i],
                primary_doc_description=recent.get("primaryDocDescription", [None])[i],
                items=recent.get("items", [[]])[i] if recent.get("items") else [],
                size=recent.get("size", [None])[i],
                is_xbrl=recent.get("isXBRL", [False])[i] if recent.get("isXBRL") else False,
                is_inline_xbrl=recent.get("isInlineXBRL", [False])[i] if recent.get("isInlineXBRL") else False
            )
            filings.append(filing)
            
            if len(filings) >= limit:
                break
        
        self.logger.debug(
            "Fetched company filings",
            cik=cik,
            count=len(filings)
        )
        
        return filings
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_filing_document(
        self,
        cik: str,
        accession_number: str,
        document_name: str
    ) -> str:
        """
        Get the content of a filing document.
        
        Args:
            cik: Company CIK number
            accession_number: Filing accession number
            document_name: Name of the document file
            
        Returns:
            Document content as string
        """
        cik = self._format_cik(cik)
        accession_clean = accession_number.replace("-", "")
        
        url = f"{self.BASE_URL}/Archives/edgar/data/{cik}/{accession_clean}/{document_name}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.text
    
    # =========================================================================
    # Company Facts (XBRL)
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_company_facts(self, cik: str) -> CompanyFacts:
        """
        Get XBRL facts for a company.
        
        Args:
            cik: Company CIK number
            
        Returns:
            CompanyFacts with all available XBRL data
        """
        cik = self._format_cik(cik)
        url = f"{self.COMPANY_FACTS_URL}/CIK{cik}.json"
        
        data = await self._request(url)
        
        return CompanyFacts(
            cik=cik,
            entity_name=data.get("entityName", ""),
            facts=data.get("facts", {})
        )
    
    async def get_financial_metric(
        self,
        cik: str,
        metric: str,
        taxonomy: str = "us-gaap",
        periods: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get a specific financial metric from XBRL facts.
        
        Args:
            cik: Company CIK number
            metric: Metric name (e.g., "Revenues", "NetIncomeLoss")
            taxonomy: XBRL taxonomy (us-gaap, dei, etc.)
            periods: Number of periods to return
            
        Returns:
            List of metric values with dates
        """
        facts = await self.get_company_facts(cik)
        
        taxonomy_facts = facts.facts.get(taxonomy, {})
        metric_data = taxonomy_facts.get(metric, {})
        
        # Get USD values (most common)
        units = metric_data.get("units", {})
        usd_values = units.get("USD", [])
        
        # Sort by end date and return most recent
        sorted_values = sorted(
            usd_values,
            key=lambda x: x.get("end", ""),
            reverse=True
        )
        
        return sorted_values[:periods]
    
    # =========================================================================
    # Form 4 (Insider Trading)
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_insider_transactions(
        self,
        cik: str,
        limit: int = 50
    ) -> List[Form4Filing]:
        """
        Get Form 4 insider trading filings for a company.
        
        Args:
            cik: Company CIK number
            limit: Maximum number of filings
            
        Returns:
            List of Form4Filing objects
        """
        # First get all Form 4 filings
        filings = await self.get_company_filings(
            cik=cik,
            form_types=["4"],
            limit=limit
        )
        
        # For now, return basic filing info
        # Full parsing would require downloading and parsing XML
        form4_filings = []
        for filing in filings:
            form4_filings.append(Form4Filing(
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                issuer_cik=cik,
                issuer_name="",  # Would need to parse XML
                owner_cik="",
                owner_name="",
                transactions=[]
            ))
        
        return form4_filings
    
    # =========================================================================
    # Form 13F (Institutional Holdings)
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_13f_holdings(
        self,
        manager_cik: str,
        limit: int = 10
    ) -> List[Form13FFiling]:
        """
        Get Form 13F institutional holdings filings.
        
        Args:
            manager_cik: Investment manager CIK number
            limit: Maximum number of filings
            
        Returns:
            List of Form13FFiling objects
        """
        filings = await self.get_company_filings(
            cik=manager_cik,
            form_types=["13F-HR"],
            limit=limit
        )
        
        # Basic filing info - full parsing would require XML processing
        holdings_filings = []
        for filing in filings:
            holdings_filings.append(Form13FFiling(
                accession_number=filing.accession_number,
                filing_date=filing.filing_date,
                report_date=filing.report_date or filing.filing_date,
                filer_cik=manager_cik,
                filer_name="",
                total_value=0,
                holdings_count=0,
                holdings=[]
            ))
        
        return holdings_filings
    
    # =========================================================================
    # Full-Text Search
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def search_filings(
        self,
        query: str,
        form_types: Optional[List[str]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across SEC filings.
        
        Args:
            query: Search query
            form_types: Filter by form types
            date_from: Start date filter
            date_to: End date filter
            limit: Maximum results
            
        Returns:
            List of matching filings
        """
        params = {
            "q": query,
            "from": 0,
            "size": limit
        }
        
        if form_types:
            params["forms"] = ",".join(form_types)
        if date_from:
            params["startdt"] = date_from.isoformat()
        if date_to:
            params["enddt"] = date_to.isoformat()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.FULL_TEXT_SEARCH_URL,
                params=params,
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("hits", {}).get("hits", [])
    
    # =========================================================================
    # CIK Lookup
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def lookup_cik(self, ticker: str) -> Optional[str]:
        """
        Look up CIK number for a ticker symbol.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CIK number or None if not found
        """
        url = f"{self.BASE_URL}/submissions/CIK-lookup-data.txt"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            # Parse the lookup data
            for line in response.text.split("\n"):
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    if parts[0].upper() == ticker.upper():
                        return parts[1]
        
        return None


@lru_cache()
def get_sec_client() -> SECClient:
    """Get a cached SEC client instance."""
    return SECClient()
