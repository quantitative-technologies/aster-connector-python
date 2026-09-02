"""Public market data endpoints (V3).

Pro API (V3) counterpart of :mod:`aster.rest_api.market_async`.  Method names match
the V1 module so that callers can swap clients without changing call sites.
"""

from aster.lib.utils import check_required_parameter
from aster.lib.utils import check_required_parameters


async def ping(self):
    url_path = "/fapi/v3/ping"
    return await self.query(url_path)


async def time(self):
    url_path = "/fapi/v3/time"
    return await self.query(url_path)


async def exchange_info(self):
    url_path = "/fapi/v3/exchangeInfo"
    return await self.query(url_path)


async def depth(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v3/depth"
    return await self.query(url_path, params)


async def trades(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v3/trades"
    return await self.query(url_path, params)


async def historical_trades(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v3/historicalTrades"
    return await self.limit_request("GET", url_path, params)


async def agg_trades(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v3/aggTrades"
    return await self.query(url_path, params)


async def klines(self, symbol: str, interval: str, **kwargs):
    check_required_parameters([[symbol, "symbol"], [interval, "interval"]])
    params = {"symbol": symbol, "interval": interval, **kwargs}
    url_path = "/fapi/v3/klines"
    return await self.query(url_path, params)


async def index_price_klines(self, pair: str, interval: str, **kwargs):
    check_required_parameters([[pair, "pair"], [interval, "interval"]])
    params = {"pair": pair, "interval": interval, **kwargs}
    url_path = "/fapi/v3/indexPriceKlines"
    return await self.query(url_path, params)


async def mark_price_klines(self, symbol: str, interval: str, **kwargs):
    check_required_parameters([[symbol, "symbol"], [interval, "interval"]])
    params = {"symbol": symbol, "interval": interval, **kwargs}
    url_path = "/fapi/v3/markPriceKlines"
    return await self.query(url_path, params)


async def mark_price(self, symbol: str = None):
    params = {"symbol": symbol}
    url_path = "/fapi/v3/premiumIndex"
    return await self.query(url_path, params)


async def funding_rate(self, symbol: str = None,  **kwargs):
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v3/fundingRate"
    return await self.query(url_path, params)


async def ticker_24hr_price_change(self, symbol: str = None):
    params = {"symbol": symbol}
    url_path = "/fapi/v3/ticker/24hr"
    return await self.query(url_path, params)


async def ticker_price(self, symbol: str = None):
    params = {"symbol": symbol}
    url_path = "/fapi/v3/ticker/price"
    return await self.query(url_path, params)


async def book_ticker(self, symbol: str = None):
    params = {"symbol": symbol}
    url_path = "/fapi/v3/ticker/bookTicker"
    return await self.query(url_path, params)
