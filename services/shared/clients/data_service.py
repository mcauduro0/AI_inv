"""
Unified Data Service for Investment Research

This service aggregates data from multiple sources (Polygon.io, FMP, SEC EDGAR)
and provides enriched context for LLM-based analysis.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import structlog

from .polygon_client import get_polygon_client, PolygonClient
from .fmp_client import get_fmp_client, FMPClient
from .sec_client import get_sec_client, SECClient

logger = structlog.get_logger(__name__)


@dataclass
class CompanyContext:
    """Comprehensive company context for analysis."""
    ticker: str
    name: str
    sector: str
    industry: str
    description: str
    market_cap: float
    employees: int
    website: str
    
    # Price data
    current_price: float
    price_change_1d: float
    price_change_1m: float
    price_change_ytd: float
    fifty_two_week_high: float
    fifty_two_week_low: float
    avg_volume: float
    
    # Valuation metrics
    pe_ratio: float
    forward_pe: float
    pb_ratio: float
    ps_ratio: float
    ev_ebitda: float
    peg_ratio: float
    
    # Financial metrics
    revenue: float
    revenue_growth: float
    gross_margin: float
    operating_margin: float
    net_margin: float
    roe: float
    roa: float
    roic: float
    
    # Balance sheet
    total_debt: float
    total_cash: float
    debt_to_equity: float
    current_ratio: float
    
    # Dividend
    dividend_yield: float
    payout_ratio: float
    
    # Analyst data
    analyst_rating: str
    price_target: float
    num_analysts: int
    
    # Recent news headlines
    recent_news: List[str]
    
    # Insider activity summary
    insider_buying: int
    insider_selling: int
    
    # Institutional ownership
    institutional_ownership: float
    top_holders: List[str]
    
    def to_prompt_context(self) -> str:
        """Convert to formatted string for LLM prompt."""
        return f"""
=== COMPANY OVERVIEW ===
Company: {self.name} ({self.ticker})
Sector: {self.sector} | Industry: {self.industry}
Description: {self.description[:500]}...
Market Cap: ${self.market_cap:,.0f} | Employees: {self.employees:,}

=== PRICE & PERFORMANCE ===
Current Price: ${self.current_price:.2f}
1-Day Change: {self.price_change_1d:+.2f}%
1-Month Change: {self.price_change_1m:+.2f}%
YTD Change: {self.price_change_ytd:+.2f}%
52-Week Range: ${self.fifty_two_week_low:.2f} - ${self.fifty_two_week_high:.2f}
Avg Volume: {self.avg_volume:,.0f}

=== VALUATION ===
P/E Ratio: {self.pe_ratio:.2f} | Forward P/E: {self.forward_pe:.2f}
P/B Ratio: {self.pb_ratio:.2f} | P/S Ratio: {self.ps_ratio:.2f}
EV/EBITDA: {self.ev_ebitda:.2f} | PEG Ratio: {self.peg_ratio:.2f}

=== PROFITABILITY ===
Revenue: ${self.revenue:,.0f} | Revenue Growth: {self.revenue_growth:+.1f}%
Gross Margin: {self.gross_margin:.1f}% | Operating Margin: {self.operating_margin:.1f}%
Net Margin: {self.net_margin:.1f}%
ROE: {self.roe:.1f}% | ROA: {self.roa:.1f}% | ROIC: {self.roic:.1f}%

=== BALANCE SHEET ===
Total Debt: ${self.total_debt:,.0f} | Total Cash: ${self.total_cash:,.0f}
Debt/Equity: {self.debt_to_equity:.2f} | Current Ratio: {self.current_ratio:.2f}

=== DIVIDEND ===
Dividend Yield: {self.dividend_yield:.2f}% | Payout Ratio: {self.payout_ratio:.1f}%

=== ANALYST CONSENSUS ===
Rating: {self.analyst_rating} | Price Target: ${self.price_target:.2f}
Number of Analysts: {self.num_analysts}

=== OWNERSHIP ===
Institutional Ownership: {self.institutional_ownership:.1f}%
Top Holders: {', '.join(self.top_holders[:5])}
Insider Activity (90 days): {self.insider_buying} buys, {self.insider_selling} sells

=== RECENT NEWS ===
{chr(10).join(['• ' + news for news in self.recent_news[:5]])}
"""


class DataService:
    """Unified data service for investment research."""
    
    def __init__(self):
        self.polygon = get_polygon_client()
        self.fmp = get_fmp_client()
        self.sec = get_sec_client()
        self.logger = logger.bind(service="data_service")
    
    async def get_company_context(self, ticker: str) -> CompanyContext:
        """
        Get comprehensive company context for analysis.
        
        Aggregates data from multiple sources into a unified context object.
        """
        self.logger.info("Fetching company context", ticker=ticker)
        
        try:
            # Fetch data from multiple sources in parallel
            polygon_details, fmp_profile, fmp_ratios, fmp_metrics, news, insider, holders = await asyncio.gather(
                self._get_polygon_details(ticker),
                self._get_fmp_profile(ticker),
                self._get_fmp_ratios(ticker),
                self._get_fmp_metrics(ticker),
                self._get_recent_news(ticker),
                self._get_insider_activity(ticker),
                self._get_institutional_holders(ticker),
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(polygon_details, Exception):
                polygon_details = {}
            if isinstance(fmp_profile, Exception):
                fmp_profile = {}
            if isinstance(fmp_ratios, Exception):
                fmp_ratios = {}
            if isinstance(fmp_metrics, Exception):
                fmp_metrics = {}
            if isinstance(news, Exception):
                news = []
            if isinstance(insider, Exception):
                insider = {"buying": 0, "selling": 0}
            if isinstance(holders, Exception):
                holders = []
            
            # Get price data
            price_data = await self._get_price_data(ticker)
            
            return CompanyContext(
                ticker=ticker.upper(),
                name=fmp_profile.get("companyName", polygon_details.get("name", ticker)),
                sector=fmp_profile.get("sector", polygon_details.get("sic_description", "Unknown")),
                industry=fmp_profile.get("industry", "Unknown"),
                description=fmp_profile.get("description", polygon_details.get("description", "")),
                market_cap=fmp_profile.get("mktCap", polygon_details.get("market_cap", 0)) or 0,
                employees=fmp_profile.get("fullTimeEmployees", polygon_details.get("total_employees", 0)) or 0,
                website=fmp_profile.get("website", polygon_details.get("homepage_url", "")),
                
                current_price=price_data.get("price", 0),
                price_change_1d=price_data.get("change_1d", 0),
                price_change_1m=price_data.get("change_1m", 0),
                price_change_ytd=price_data.get("change_ytd", 0),
                fifty_two_week_high=fmp_metrics.get("yearHigh", 0) or 0,
                fifty_two_week_low=fmp_metrics.get("yearLow", 0) or 0,
                avg_volume=fmp_profile.get("volAvg", 0) or 0,
                
                pe_ratio=fmp_ratios.get("peRatioTTM", 0) or 0,
                forward_pe=fmp_metrics.get("peRatio", 0) or 0,
                pb_ratio=fmp_ratios.get("priceToBookRatioTTM", 0) or 0,
                ps_ratio=fmp_ratios.get("priceToSalesRatioTTM", 0) or 0,
                ev_ebitda=fmp_ratios.get("enterpriseValueMultipleTTM", 0) or 0,
                peg_ratio=fmp_ratios.get("pegRatioTTM", 0) or 0,
                
                revenue=fmp_metrics.get("revenue", 0) or 0,
                revenue_growth=fmp_metrics.get("revenueGrowth", 0) or 0,
                gross_margin=(fmp_ratios.get("grossProfitMarginTTM", 0) or 0) * 100,
                operating_margin=(fmp_ratios.get("operatingProfitMarginTTM", 0) or 0) * 100,
                net_margin=(fmp_ratios.get("netProfitMarginTTM", 0) or 0) * 100,
                roe=(fmp_ratios.get("returnOnEquityTTM", 0) or 0) * 100,
                roa=(fmp_ratios.get("returnOnAssetsTTM", 0) or 0) * 100,
                roic=(fmp_ratios.get("returnOnCapitalEmployedTTM", 0) or 0) * 100,
                
                total_debt=fmp_metrics.get("totalDebt", 0) or 0,
                total_cash=fmp_metrics.get("cashAndCashEquivalents", 0) or 0,
                debt_to_equity=fmp_ratios.get("debtEquityRatioTTM", 0) or 0,
                current_ratio=fmp_ratios.get("currentRatioTTM", 0) or 0,
                
                dividend_yield=(fmp_ratios.get("dividendYieldTTM", 0) or 0) * 100,
                payout_ratio=(fmp_ratios.get("payoutRatioTTM", 0) or 0) * 100,
                
                analyst_rating=fmp_profile.get("rating", "N/A"),
                price_target=fmp_metrics.get("targetPrice", 0) or 0,
                num_analysts=fmp_metrics.get("numberOfAnalysts", 0) or 0,
                
                recent_news=news,
                
                insider_buying=insider.get("buying", 0),
                insider_selling=insider.get("selling", 0),
                
                institutional_ownership=fmp_metrics.get("institutionalOwnership", 0) or 0,
                top_holders=[h.get("holder", "") for h in holders[:5]] if holders else []
            )
            
        except Exception as e:
            self.logger.error("Failed to get company context", ticker=ticker, error=str(e))
            raise
    
    async def _get_polygon_details(self, ticker: str) -> Dict[str, Any]:
        """Get company details from Polygon."""
        try:
            details = await self.polygon.get_ticker_details(ticker)
            return asdict(details) if details else {}
        except Exception as e:
            self.logger.warning("Polygon details failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_fmp_profile(self, ticker: str) -> Dict[str, Any]:
        """Get company profile from FMP."""
        try:
            profile = await self.fmp.get_company_profile(ticker)
            return profile.__dict__ if profile else {}
        except Exception as e:
            self.logger.warning("FMP profile failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_fmp_ratios(self, ticker: str) -> Dict[str, Any]:
        """Get financial ratios from FMP."""
        try:
            ratios = await self.fmp.get_financial_ratios(ticker, period="ttm", limit=1)
            return ratios[0].__dict__ if ratios else {}
        except Exception as e:
            self.logger.warning("FMP ratios failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_fmp_metrics(self, ticker: str) -> Dict[str, Any]:
        """Get key metrics from FMP."""
        try:
            metrics = await self.fmp.get_key_metrics(ticker, period="ttm", limit=1)
            return metrics[0].__dict__ if metrics else {}
        except Exception as e:
            self.logger.warning("FMP metrics failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_price_data(self, ticker: str) -> Dict[str, Any]:
        """Get price and performance data."""
        try:
            # Get current quote
            quote = await self.fmp.get_quote(ticker)
            if not quote:
                return {}
            
            return {
                "price": quote.price,
                "change_1d": quote.change_percentage,
                "change_1m": 0,  # Would need historical data
                "change_ytd": quote.ytd or 0
            }
        except Exception as e:
            self.logger.warning("Price data failed", ticker=ticker, error=str(e))
            return {}
    
    async def _get_recent_news(self, ticker: str) -> List[str]:
        """Get recent news headlines."""
        try:
            news = await self.polygon.get_news(ticker=ticker, limit=10)
            return [article.title for article in news[:5]]
        except Exception as e:
            self.logger.warning("News fetch failed", ticker=ticker, error=str(e))
            return []
    
    async def _get_insider_activity(self, ticker: str) -> Dict[str, int]:
        """Get insider trading activity summary."""
        try:
            trades = await self.fmp.get_insider_trading(ticker, limit=50)
            buying = sum(1 for t in trades if t.transaction_type and "purchase" in t.transaction_type.lower())
            selling = sum(1 for t in trades if t.transaction_type and "sale" in t.transaction_type.lower())
            return {"buying": buying, "selling": selling}
        except Exception as e:
            self.logger.warning("Insider activity failed", ticker=ticker, error=str(e))
            return {"buying": 0, "selling": 0}
    
    async def _get_institutional_holders(self, ticker: str) -> List[Dict[str, Any]]:
        """Get institutional holders."""
        try:
            holders = await self.fmp.get_institutional_holders(ticker)
            return [{"holder": h.holder, "shares": h.shares} for h in holders[:10]]
        except Exception as e:
            self.logger.warning("Institutional holders failed", ticker=ticker, error=str(e))
            return []
    
    async def get_financial_statements(self, ticker: str, years: int = 5) -> Dict[str, Any]:
        """Get detailed financial statements."""
        try:
            income, balance, cashflow = await asyncio.gather(
                self.fmp.get_income_statement(ticker, period="annual", limit=years),
                self.fmp.get_balance_sheet(ticker, period="annual", limit=years),
                self.fmp.get_cash_flow_statement(ticker, period="annual", limit=years),
                return_exceptions=True
            )
            
            return {
                "income_statement": [s.__dict__ for s in income] if not isinstance(income, Exception) else [],
                "balance_sheet": [s.__dict__ for s in balance] if not isinstance(balance, Exception) else [],
                "cash_flow": [s.__dict__ for s in cashflow] if not isinstance(cashflow, Exception) else []
            }
        except Exception as e:
            self.logger.error("Financial statements failed", ticker=ticker, error=str(e))
            return {}
    
    async def get_sec_filings(self, ticker: str, form_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get recent SEC filings."""
        try:
            # Look up CIK
            cik = await self.sec.lookup_cik(ticker)
            if not cik:
                return []
            
            filings = await self.sec.get_company_filings(
                cik=cik,
                form_types=form_types or ["10-K", "10-Q", "8-K"],
                limit=20
            )
            
            return [
                {
                    "form_type": f.form_type,
                    "filing_date": f.filing_date.isoformat() if f.filing_date else None,
                    "description": f.primary_document,
                    "url": f"https://www.sec.gov/Archives/edgar/data/{cik}/{f.accession_number.replace('-', '')}"
                }
                for f in filings
            ]
        except Exception as e:
            self.logger.error("SEC filings failed", ticker=ticker, error=str(e))
            return []
    
    async def screen_stocks(
        self,
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Screen stocks based on criteria."""
        try:
            results = await self.fmp.screen_stocks(**criteria)
            return results[:50]  # Limit results
        except Exception as e:
            self.logger.error("Stock screening failed", error=str(e))
            return []
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get market overview data."""
        try:
            # Get major indices
            indices = ["SPY", "QQQ", "DIA", "IWM"]
            quotes = await asyncio.gather(
                *[self.fmp.get_quote(idx) for idx in indices],
                return_exceptions=True
            )
            
            market_data = {}
            for idx, quote in zip(indices, quotes):
                if not isinstance(quote, Exception) and quote:
                    market_data[idx] = {
                        "price": quote.price,
                        "change": quote.change_percentage
                    }
            
            return market_data
        except Exception as e:
            self.logger.error("Market overview failed", error=str(e))
            return {}


def get_data_service() -> DataService:
    """Get a DataService instance."""
    return DataService()
