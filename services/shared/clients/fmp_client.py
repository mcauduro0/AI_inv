# =============================================================================
# Financial Modeling Prep (FMP) API Client
# =============================================================================
# Client for fetching fundamental financial data from FMP
# =============================================================================

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from functools import lru_cache

import httpx
import structlog
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.config.settings import settings

logger = structlog.get_logger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class CompanyProfile(BaseModel):
    """Company profile and overview."""
    symbol: str
    company_name: str
    exchange: str
    industry: str
    sector: str
    country: str
    description: str
    ceo: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    full_time_employees: Optional[int] = None
    market_cap: Optional[float] = None
    price: Optional[float] = None
    beta: Optional[float] = None
    vol_avg: Optional[int] = None
    last_div: Optional[float] = None
    range_52_week: Optional[str] = Field(None, alias="range")
    ipo_date: Optional[date] = None
    is_etf: bool = False
    is_actively_trading: bool = True


class IncomeStatement(BaseModel):
    """Income statement data."""
    date: date
    symbol: str
    period: str
    revenue: float
    cost_of_revenue: float
    gross_profit: float
    gross_profit_ratio: float
    operating_expenses: float
    operating_income: float
    operating_income_ratio: float
    ebitda: float
    ebitda_ratio: float
    net_income: float
    net_income_ratio: float
    eps: float
    eps_diluted: float
    weighted_average_shares: int
    weighted_average_shares_diluted: int


class BalanceSheet(BaseModel):
    """Balance sheet data."""
    date: date
    symbol: str
    period: str
    total_assets: float
    total_current_assets: float
    cash_and_equivalents: float
    short_term_investments: float
    inventory: float
    total_liabilities: float
    total_current_liabilities: float
    long_term_debt: float
    total_stockholders_equity: float
    retained_earnings: float
    common_stock: float


class CashFlowStatement(BaseModel):
    """Cash flow statement data."""
    date: date
    symbol: str
    period: str
    operating_cash_flow: float
    capital_expenditure: float
    free_cash_flow: float
    dividends_paid: float
    stock_repurchased: float
    debt_repayment: float
    net_change_in_cash: float


class FinancialRatios(BaseModel):
    """Key financial ratios."""
    symbol: str
    date: date
    period: str
    # Profitability
    gross_profit_margin: Optional[float] = None
    operating_profit_margin: Optional[float] = None
    net_profit_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_capital_employed: Optional[float] = None
    # Liquidity
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    cash_ratio: Optional[float] = None
    # Leverage
    debt_ratio: Optional[float] = None
    debt_equity_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    # Efficiency
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None
    receivables_turnover: Optional[float] = None
    # Valuation
    price_earnings_ratio: Optional[float] = None
    price_to_book_ratio: Optional[float] = None
    price_to_sales_ratio: Optional[float] = None
    ev_to_ebitda: Optional[float] = None
    price_to_free_cash_flow: Optional[float] = None
    # Per Share
    earnings_per_share: Optional[float] = None
    book_value_per_share: Optional[float] = None
    free_cash_flow_per_share: Optional[float] = None
    dividend_per_share: Optional[float] = None
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None


class AnalystEstimate(BaseModel):
    """Analyst estimates and consensus."""
    symbol: str
    date: date
    estimated_revenue_low: float
    estimated_revenue_high: float
    estimated_revenue_avg: float
    estimated_ebitda_low: float
    estimated_ebitda_high: float
    estimated_ebitda_avg: float
    estimated_eps_low: float
    estimated_eps_high: float
    estimated_eps_avg: float
    number_analysts_estimated_revenue: int
    number_analysts_estimated_eps: int


class InsiderTrade(BaseModel):
    """Insider trading activity."""
    symbol: str
    filing_date: date
    transaction_date: date
    reporting_name: str
    transaction_type: str
    securities_owned: int
    securities_transacted: int
    price: Optional[float] = None
    form_type: str


class InstitutionalHolder(BaseModel):
    """Institutional holder information."""
    holder: str
    shares: int
    date_reported: date
    change: int
    change_percentage: float


# =============================================================================
# FMP Client
# =============================================================================

class FMPClient:
    """
    Client for Financial Modeling Prep API.
    
    Provides access to:
    - Company profiles and fundamentals
    - Financial statements (income, balance sheet, cash flow)
    - Financial ratios and metrics
    - Analyst estimates and ratings
    - Insider trading data
    - Institutional holdings
    - SEC filings
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.financial_data.fmp_api_key
        self.logger = structlog.get_logger(__name__)
    
    async def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Make an API request to FMP."""
        params = params or {}
        params["apikey"] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    
    # =========================================================================
    # Company Profile
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_company_profile(self, symbol: str) -> CompanyProfile:
        """
        Get company profile and overview.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            CompanyProfile with company details
        """
        data = await self._request(f"profile/{symbol}")
        
        if not data:
            raise ValueError(f"No profile found for {symbol}")
        
        profile = data[0]
        return CompanyProfile(
            symbol=profile.get("symbol"),
            company_name=profile.get("companyName"),
            exchange=profile.get("exchange"),
            industry=profile.get("industry"),
            sector=profile.get("sector"),
            country=profile.get("country"),
            description=profile.get("description"),
            ceo=profile.get("ceo"),
            website=profile.get("website"),
            phone=profile.get("phone"),
            address=profile.get("address"),
            city=profile.get("city"),
            state=profile.get("state"),
            zip=profile.get("zip"),
            full_time_employees=profile.get("fullTimeEmployees"),
            market_cap=profile.get("mktCap"),
            price=profile.get("price"),
            beta=profile.get("beta"),
            vol_avg=profile.get("volAvg"),
            last_div=profile.get("lastDiv"),
            range_52_week=profile.get("range"),
            ipo_date=profile.get("ipoDate"),
            is_etf=profile.get("isEtf", False),
            is_actively_trading=profile.get("isActivelyTrading", True)
        )
    
    # =========================================================================
    # Financial Statements
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_income_statement(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[IncomeStatement]:
        """
        Get income statement data.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual"
            limit: Number of periods to return
            
        Returns:
            List of IncomeStatement objects
        """
        data = await self._request(
            f"income-statement/{symbol}",
            params={"period": period, "limit": limit}
        )
        
        statements = []
        for item in data:
            statements.append(IncomeStatement(
                date=item.get("date"),
                symbol=item.get("symbol"),
                period=item.get("period"),
                revenue=item.get("revenue", 0),
                cost_of_revenue=item.get("costOfRevenue", 0),
                gross_profit=item.get("grossProfit", 0),
                gross_profit_ratio=item.get("grossProfitRatio", 0),
                operating_expenses=item.get("operatingExpenses", 0),
                operating_income=item.get("operatingIncome", 0),
                operating_income_ratio=item.get("operatingIncomeRatio", 0),
                ebitda=item.get("ebitda", 0),
                ebitda_ratio=item.get("ebitdaratio", 0),
                net_income=item.get("netIncome", 0),
                net_income_ratio=item.get("netIncomeRatio", 0),
                eps=item.get("eps", 0),
                eps_diluted=item.get("epsdiluted", 0),
                weighted_average_shares=item.get("weightedAverageShsOut", 0),
                weighted_average_shares_diluted=item.get("weightedAverageShsOutDil", 0)
            ))
        
        return statements
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_balance_sheet(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[BalanceSheet]:
        """
        Get balance sheet data.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual"
            limit: Number of periods to return
            
        Returns:
            List of BalanceSheet objects
        """
        data = await self._request(
            f"balance-sheet-statement/{symbol}",
            params={"period": period, "limit": limit}
        )
        
        statements = []
        for item in data:
            statements.append(BalanceSheet(
                date=item.get("date"),
                symbol=item.get("symbol"),
                period=item.get("period"),
                total_assets=item.get("totalAssets", 0),
                total_current_assets=item.get("totalCurrentAssets", 0),
                cash_and_equivalents=item.get("cashAndCashEquivalents", 0),
                short_term_investments=item.get("shortTermInvestments", 0),
                inventory=item.get("inventory", 0),
                total_liabilities=item.get("totalLiabilities", 0),
                total_current_liabilities=item.get("totalCurrentLiabilities", 0),
                long_term_debt=item.get("longTermDebt", 0),
                total_stockholders_equity=item.get("totalStockholdersEquity", 0),
                retained_earnings=item.get("retainedEarnings", 0),
                common_stock=item.get("commonStock", 0)
            ))
        
        return statements
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_cash_flow_statement(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[CashFlowStatement]:
        """
        Get cash flow statement data.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual"
            limit: Number of periods to return
            
        Returns:
            List of CashFlowStatement objects
        """
        data = await self._request(
            f"cash-flow-statement/{symbol}",
            params={"period": period, "limit": limit}
        )
        
        statements = []
        for item in data:
            statements.append(CashFlowStatement(
                date=item.get("date"),
                symbol=item.get("symbol"),
                period=item.get("period"),
                operating_cash_flow=item.get("operatingCashFlow", 0),
                capital_expenditure=item.get("capitalExpenditure", 0),
                free_cash_flow=item.get("freeCashFlow", 0),
                dividends_paid=item.get("dividendsPaid", 0),
                stock_repurchased=item.get("commonStockRepurchased", 0),
                debt_repayment=item.get("debtRepayment", 0),
                net_change_in_cash=item.get("netChangeInCash", 0)
            ))
        
        return statements
    
    # =========================================================================
    # Financial Ratios
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_financial_ratios(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[FinancialRatios]:
        """
        Get key financial ratios.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual"
            limit: Number of periods to return
            
        Returns:
            List of FinancialRatios objects
        """
        data = await self._request(
            f"ratios/{symbol}",
            params={"period": period, "limit": limit}
        )
        
        ratios = []
        for item in data:
            ratios.append(FinancialRatios(
                symbol=symbol,
                date=item.get("date"),
                period=item.get("period", period),
                gross_profit_margin=item.get("grossProfitMargin"),
                operating_profit_margin=item.get("operatingProfitMargin"),
                net_profit_margin=item.get("netProfitMargin"),
                return_on_assets=item.get("returnOnAssets"),
                return_on_equity=item.get("returnOnEquity"),
                return_on_capital_employed=item.get("returnOnCapitalEmployed"),
                current_ratio=item.get("currentRatio"),
                quick_ratio=item.get("quickRatio"),
                cash_ratio=item.get("cashRatio"),
                debt_ratio=item.get("debtRatio"),
                debt_equity_ratio=item.get("debtEquityRatio"),
                interest_coverage=item.get("interestCoverage"),
                asset_turnover=item.get("assetTurnover"),
                inventory_turnover=item.get("inventoryTurnover"),
                receivables_turnover=item.get("receivablesTurnover"),
                price_earnings_ratio=item.get("priceEarningsRatio"),
                price_to_book_ratio=item.get("priceToBookRatio"),
                price_to_sales_ratio=item.get("priceToSalesRatio"),
                ev_to_ebitda=item.get("enterpriseValueMultiple"),
                price_to_free_cash_flow=item.get("priceToFreeCashFlowsRatio"),
                earnings_per_share=item.get("netIncomePerShare"),
                book_value_per_share=item.get("bookValuePerShare"),
                free_cash_flow_per_share=item.get("freeCashFlowPerShare"),
                dividend_per_share=item.get("dividendPerShare"),
                dividend_yield=item.get("dividendYield"),
                payout_ratio=item.get("payoutRatio")
            ))
        
        return ratios
    
    # =========================================================================
    # Analyst Data
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_analyst_estimates(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[AnalystEstimate]:
        """
        Get analyst estimates and consensus.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual"
            limit: Number of periods to return
            
        Returns:
            List of AnalystEstimate objects
        """
        data = await self._request(
            f"analyst-estimates/{symbol}",
            params={"period": period, "limit": limit}
        )
        
        estimates = []
        for item in data:
            estimates.append(AnalystEstimate(
                symbol=symbol,
                date=item.get("date"),
                estimated_revenue_low=item.get("estimatedRevenueLow", 0),
                estimated_revenue_high=item.get("estimatedRevenueHigh", 0),
                estimated_revenue_avg=item.get("estimatedRevenueAvg", 0),
                estimated_ebitda_low=item.get("estimatedEbitdaLow", 0),
                estimated_ebitda_high=item.get("estimatedEbitdaHigh", 0),
                estimated_ebitda_avg=item.get("estimatedEbitdaAvg", 0),
                estimated_eps_low=item.get("estimatedEpsLow", 0),
                estimated_eps_high=item.get("estimatedEpsHigh", 0),
                estimated_eps_avg=item.get("estimatedEpsAvg", 0),
                number_analysts_estimated_revenue=item.get("numberAnalystEstimatedRevenue", 0),
                number_analysts_estimated_eps=item.get("numberAnalystsEstimatedEps", 0)
            ))
        
        return estimates
    
    # =========================================================================
    # Insider Trading
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_insider_trading(
        self,
        symbol: str,
        limit: int = 50
    ) -> List[InsiderTrade]:
        """
        Get insider trading activity.
        
        Args:
            symbol: Stock ticker symbol
            limit: Number of transactions to return
            
        Returns:
            List of InsiderTrade objects
        """
        data = await self._request(
            f"insider-trading",
            params={"symbol": symbol, "limit": limit}
        )
        
        trades = []
        for item in data:
            trades.append(InsiderTrade(
                symbol=item.get("symbol"),
                filing_date=item.get("filingDate"),
                transaction_date=item.get("transactionDate"),
                reporting_name=item.get("reportingName"),
                transaction_type=item.get("transactionType"),
                securities_owned=item.get("securitiesOwned", 0),
                securities_transacted=item.get("securitiesTransacted", 0),
                price=item.get("price"),
                form_type=item.get("formType")
            ))
        
        return trades
    
    # =========================================================================
    # Institutional Holdings
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_institutional_holders(
        self,
        symbol: str
    ) -> List[InstitutionalHolder]:
        """
        Get institutional holders for a stock.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            List of InstitutionalHolder objects
        """
        data = await self._request(f"institutional-holder/{symbol}")
        
        holders = []
        for item in data:
            holders.append(InstitutionalHolder(
                holder=item.get("holder"),
                shares=item.get("shares", 0),
                date_reported=item.get("dateReported"),
                change=item.get("change", 0),
                change_percentage=item.get("changeInSharesPercentage", 0)
            ))
        
        return holders
    
    # =========================================================================
    # Stock Screener
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def screen_stocks(
        self,
        market_cap_more_than: Optional[int] = None,
        market_cap_less_than: Optional[int] = None,
        price_more_than: Optional[float] = None,
        price_less_than: Optional[float] = None,
        beta_more_than: Optional[float] = None,
        beta_less_than: Optional[float] = None,
        volume_more_than: Optional[int] = None,
        dividend_more_than: Optional[float] = None,
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        country: Optional[str] = None,
        exchange: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Screen stocks based on criteria.
        
        Returns:
            List of matching stocks
        """
        params = {"limit": limit}
        
        if market_cap_more_than:
            params["marketCapMoreThan"] = market_cap_more_than
        if market_cap_less_than:
            params["marketCapLowerThan"] = market_cap_less_than
        if price_more_than:
            params["priceMoreThan"] = price_more_than
        if price_less_than:
            params["priceLowerThan"] = price_less_than
        if beta_more_than:
            params["betaMoreThan"] = beta_more_than
        if beta_less_than:
            params["betaLowerThan"] = beta_less_than
        if volume_more_than:
            params["volumeMoreThan"] = volume_more_than
        if dividend_more_than:
            params["dividendMoreThan"] = dividend_more_than
        if sector:
            params["sector"] = sector
        if industry:
            params["industry"] = industry
        if country:
            params["country"] = country
        if exchange:
            params["exchange"] = exchange
        
        data = await self._request("stock-screener", params=params)
        return data


    # =========================================================================
    # Key Metrics
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_key_metrics(
        self,
        symbol: str,
        period: str = "quarter",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get key financial metrics.
        
        Args:
            symbol: Stock ticker symbol
            period: "quarter" or "annual" or "ttm"
            limit: Number of periods to return
            
        Returns:
            List of key metrics dictionaries
        """
        if period == "ttm":
            data = await self._request(f"key-metrics-ttm/{symbol}")
        else:
            data = await self._request(
                f"key-metrics/{symbol}",
                params={"period": period, "limit": limit}
            )
        
        # Return as list of dict-like objects with __dict__
        class MetricsDict(dict):
            def __init__(self, d):
                super().__init__(d)
                self.__dict__.update(d)
        
        if isinstance(data, list):
            return [MetricsDict(item) for item in data]
        elif isinstance(data, dict):
            return [MetricsDict(data)]
        return []
    
    # =========================================================================
    # Stock Quote
    # =========================================================================
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_quote(self, symbol: str):
        """
        Get real-time stock quote.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Quote object with price data
        """
        data = await self._request(f"quote/{symbol}")
        
        if not data:
            return None
        
        quote = data[0] if isinstance(data, list) else data
        
        class Quote:
            def __init__(self, d):
                self.symbol = d.get("symbol")
                self.name = d.get("name")
                self.price = d.get("price", 0)
                self.change = d.get("change", 0)
                self.change_percentage = d.get("changesPercentage", 0)
                self.day_low = d.get("dayLow", 0)
                self.day_high = d.get("dayHigh", 0)
                self.year_low = d.get("yearLow", 0)
                self.year_high = d.get("yearHigh", 0)
                self.market_cap = d.get("marketCap", 0)
                self.pe = d.get("pe", 0)
                self.eps = d.get("eps", 0)
                self.volume = d.get("volume", 0)
                self.avg_volume = d.get("avgVolume", 0)
                self.open = d.get("open", 0)
                self.previous_close = d.get("previousClose", 0)
                self.ytd = d.get("priceAvg200", 0)  # Use 200-day avg as proxy
        
        return Quote(quote)


@lru_cache()
def get_fmp_client() -> FMPClient:
    """Get a cached FMP client instance."""
    return FMPClient()
