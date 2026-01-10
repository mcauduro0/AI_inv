# =============================================================================
# Polygon.io API Client
# =============================================================================
# Client for fetching financial market data from Polygon.io
# =============================================================================

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from functools import lru_cache

import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.config.settings import settings

logger = structlog.get_logger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class StockQuote(BaseModel):
    """Real-time or delayed stock quote."""
    ticker: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    timestamp: datetime


class OHLCV(BaseModel):
    """Open-High-Low-Close-Volume bar."""
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: Optional[float] = None
    timestamp: datetime
    transactions: Optional[int] = None


class CompanyInfo(BaseModel):
    """Basic company information."""
    ticker: str
    name: str
    market: str
    locale: str
    primary_exchange: str
    type: str
    currency_name: str
    cik: Optional[str] = None
    composite_figi: Optional[str] = None
    share_class_figi: Optional[str] = None
    market_cap: Optional[float] = None
    phone_number: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    sic_code: Optional[str] = None
    sic_description: Optional[str] = None
    homepage_url: Optional[str] = None
    total_employees: Optional[int] = None
    list_date: Optional[date] = None


class NewsArticle(BaseModel):
    """News article from Polygon/Benzinga."""
    id: str
    publisher: Dict[str, str]
    title: str
    author: Optional[str] = None
    published_utc: datetime
    article_url: str
    tickers: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    insights: List[Dict[str, Any]] = Field(default_factory=list)


class FinancialReport(BaseModel):
    """Financial report data."""
    ticker: str
    period: str  # "quarterly", "annual"
    fiscal_period: str
    fiscal_year: int
    filing_date: Optional[date] = None
    financials: Dict[str, Any]


# =============================================================================
# Polygon Client
# =============================================================================

class PolygonClient:
    """
    Client for Polygon.io API.
    
    Provides access to:
    - Real-time and historical stock quotes
    - OHLCV bars (daily, hourly, minute)
    - Company information and financials
    - News and market sentiment
    - Options data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.financial_data.polygon_api_key
        self._client = None
        self.logger = structlog.get_logger(__name__)
    
    @property
    def client(self):
        """Lazy-load the Polygon REST client."""
        if self._client is None:
            from polygon import RESTClient
            self._client = RESTClient(api_key=self.api_key)
        return self._client
    
    # =========================================================================
    # Stock Quotes
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_last_quote(self, ticker: str) -> StockQuote:
        """
        Get the last quote for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            StockQuote with latest price data
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.get_last_quote(ticker)
        )
        
        return StockQuote(
            ticker=ticker,
            price=(result.bid_price + result.ask_price) / 2 if result.bid_price and result.ask_price else 0,
            bid=result.bid_price,
            ask=result.ask_price,
            bid_size=result.bid_size,
            ask_size=result.ask_size,
            timestamp=datetime.fromtimestamp(result.participant_timestamp / 1e9)
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_last_trade(self, ticker: str) -> StockQuote:
        """
        Get the last trade for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            StockQuote with last trade price
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.get_last_trade(ticker)
        )
        
        return StockQuote(
            ticker=ticker,
            price=result.price,
            timestamp=datetime.fromtimestamp(result.participant_timestamp / 1e9)
        )
    
    # =========================================================================
    # Historical Data
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_daily_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: Optional[date] = None,
        adjusted: bool = True
    ) -> List[OHLCV]:
        """
        Get daily OHLCV bars for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date (defaults to today)
            adjusted: Whether to return adjusted prices
            
        Returns:
            List of OHLCV bars
        """
        import asyncio
        
        end_date = end_date or date.today()
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(self.client.list_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=start_date.isoformat(),
                to=end_date.isoformat(),
                adjusted=adjusted,
                limit=50000
            ))
        )
        
        bars = []
        for agg in results:
            bars.append(OHLCV(
                ticker=ticker,
                open=agg.open,
                high=agg.high,
                low=agg.low,
                close=agg.close,
                volume=agg.volume,
                vwap=agg.vwap,
                timestamp=datetime.fromtimestamp(agg.timestamp / 1000),
                transactions=agg.transactions
            ))
        
        self.logger.debug(
            "Fetched daily bars",
            ticker=ticker,
            count=len(bars),
            start=start_date,
            end=end_date
        )
        
        return bars
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_intraday_bars(
        self,
        ticker: str,
        start_date: date,
        end_date: Optional[date] = None,
        timespan: str = "hour",
        multiplier: int = 1
    ) -> List[OHLCV]:
        """
        Get intraday OHLCV bars for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date
            end_date: End date
            timespan: Bar timespan (minute, hour)
            multiplier: Timespan multiplier (e.g., 5 for 5-minute bars)
            
        Returns:
            List of OHLCV bars
        """
        import asyncio
        
        end_date = end_date or date.today()
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(self.client.list_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=start_date.isoformat(),
                to=end_date.isoformat(),
                limit=50000
            ))
        )
        
        bars = []
        for agg in results:
            bars.append(OHLCV(
                ticker=ticker,
                open=agg.open,
                high=agg.high,
                low=agg.low,
                close=agg.close,
                volume=agg.volume,
                vwap=agg.vwap,
                timestamp=datetime.fromtimestamp(agg.timestamp / 1000),
                transactions=agg.transactions
            ))
        
        return bars
    
    # =========================================================================
    # Company Information
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_ticker_details(self, ticker: str) -> CompanyInfo:
        """
        Get detailed company information for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CompanyInfo with company details
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.get_ticker_details(ticker)
        )
        
        return CompanyInfo(
            ticker=result.ticker,
            name=result.name,
            market=result.market,
            locale=result.locale,
            primary_exchange=result.primary_exchange,
            type=result.type,
            currency_name=result.currency_name,
            cik=result.cik,
            composite_figi=result.composite_figi,
            share_class_figi=result.share_class_figi,
            market_cap=result.market_cap,
            phone_number=result.phone_number,
            address=result.address.__dict__ if result.address else None,
            description=result.description,
            sic_code=result.sic_code,
            sic_description=result.sic_description,
            homepage_url=result.homepage_url,
            total_employees=result.total_employees,
            list_date=result.list_date
        )
    
    # =========================================================================
    # News
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_news(
        self,
        ticker: Optional[str] = None,
        limit: int = 50,
        published_after: Optional[datetime] = None
    ) -> List[NewsArticle]:
        """
        Get news articles, optionally filtered by ticker.
        
        Args:
            ticker: Optional ticker to filter news
            limit: Maximum number of articles
            published_after: Only return articles after this time
            
        Returns:
            List of NewsArticle objects
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        kwargs = {"limit": limit}
        if ticker:
            kwargs["ticker"] = ticker
        if published_after:
            kwargs["published_utc_gte"] = published_after.isoformat()
        
        results = await loop.run_in_executor(
            None,
            lambda: list(self.client.list_ticker_news(**kwargs))
        )
        
        articles = []
        for news in results:
            articles.append(NewsArticle(
                id=news.id,
                publisher={"name": news.publisher.name, "homepage_url": news.publisher.homepage_url},
                title=news.title,
                author=news.author,
                published_utc=news.published_utc,
                article_url=news.article_url,
                tickers=news.tickers or [],
                description=news.description,
                keywords=news.keywords or [],
                insights=news.insights or []
            ))
        
        self.logger.debug(
            "Fetched news articles",
            ticker=ticker,
            count=len(articles)
        )
        
        return articles
    
    # =========================================================================
    # Financials
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_financials(
        self,
        ticker: str,
        timeframe: str = "quarterly",
        limit: int = 10
    ) -> List[FinancialReport]:
        """
        Get financial reports for a company.
        
        Args:
            ticker: Stock ticker symbol
            timeframe: "quarterly" or "annual"
            limit: Maximum number of reports
            
        Returns:
            List of FinancialReport objects
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(self.client.vx.list_stock_financials(
                ticker=ticker,
                timeframe=timeframe,
                limit=limit
            ))
        )
        
        reports = []
        for fin in results:
            reports.append(FinancialReport(
                ticker=ticker,
                period=timeframe,
                fiscal_period=fin.fiscal_period,
                fiscal_year=fin.fiscal_year,
                filing_date=fin.filing_date,
                financials=fin.financials.__dict__ if fin.financials else {}
            ))
        
        return reports
    
    # =========================================================================
    # Market Status
    # =========================================================================
    
    async def get_market_status(self) -> Dict[str, Any]:
        """
        Get current market status (open/closed).
        
        Returns:
            Dictionary with market status information
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.get_market_status()
        )
        
        return {
            "market": result.market,
            "server_time": result.server_time,
            "exchanges": result.exchanges,
            "currencies": result.currencies
        }


@lru_cache()
def get_polygon_client() -> PolygonClient:
    """Get a cached Polygon client instance."""
    return PolygonClient()
