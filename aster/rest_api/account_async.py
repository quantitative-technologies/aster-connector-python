from aster.lib.utils import check_required_parameter
from aster.lib.utils import check_required_parameters


async def change_position_mode(self, dualSidePosition: str, **kwargs):
    check_required_parameter(dualSidePosition, "dualSidePosition")
    params = {"dualSidePosition": dualSidePosition, **kwargs}
    url_path = "/fapi/v1/positionSide/dual"
    return await self.sign_request("POST", url_path, params)


async def get_position_mode(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/positionSide/dual"
    return await self.sign_request("GET", url_path, params)


async def change_multi_asset_mode(self, multiAssetsMargin: str, **kwargs):
    check_required_parameter(multiAssetsMargin, "multiAssetsMargin")
    params = {"multiAssetsMargin": multiAssetsMargin, **kwargs}
    url_path = "/fapi/v1/multiAssetsMargin"
    return await self.sign_request("POST", url_path, params)


async def get_multi_asset_mode(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/multiAssetsMargin"
    return await self.sign_request("GET", url_path, params)


async def new_order(self, symbol: str, side: str, type: str, **kwargs):
    check_required_parameters([[symbol, "symbol"], [side, "side"], [type, "type"]])
    params = {"symbol": symbol, "side": side, "type": type, **kwargs}
    url_path = "/fapi/v1/order"
    return await self.sign_request("POST", url_path, params)


async def new_batch_order(self, batchOrders: list):
    params = {"batchOrders": batchOrders}
    url_path = "/fapi/v1/batchOrders"
    return await self.sign_request("POST", url_path, params, True)


async def query_order(self, symbol: str, orderId: int = None, origClientOrderId: str = None, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/order"
    return await self.sign_request("GET", url_path, params)


async def cancel_order(self, symbol: str, orderId: int = None, origClientOrderId: str = None, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    if orderId is not None:
        params["orderId"] = orderId
    if origClientOrderId is not None:
        params["origClientOrderId"] = origClientOrderId
    url_path = "/fapi/v1/order"
    return await self.sign_request("DELETE", url_path, params)


async def cancel_open_orders(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/allOpenOrders"
    return await self.sign_request("DELETE", url_path, params)


async def cancel_batch_order(self, symbol: str, orderIdList: list, origClientOrderIdList: list, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/batchOrders"
    return await self.sign_request("DELETE", url_path, params)


async def countdown_cancel_order(self, symbol: str, countdownTime: int, **kwargs):
    check_required_parameters([[symbol, "symbol"], [countdownTime, "countdownTime"]])
    params = {"symbol": symbol, "countdownTime": countdownTime, **kwargs}
    url_path = "/fapi/v1/countdownCancelAll"
    return await self.sign_request("POST", url_path, params)


async def get_open_orders(self, symbol: str, orderId: int = None, origClientOrderId: str = None, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    if orderId is not None:
        params["orderId"] = orderId
    if origClientOrderId is not None:
        params["origClientOrderId"] = origClientOrderId
    url_path = "/fapi/v1/openOrder"
    return await self.sign_request("GET", url_path, params)


async def get_orders(self, **kwargs):
    params = { **kwargs }
    url_path = "/fapi/v1/openOrders"
    return await self.sign_request("GET", url_path, params)


async def get_all_orders(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/allOrders"
    return await self.sign_request("GET", url_path, params)


async def balance(self, **kwargs):
    url_path = "/fapi/v2/balance"
    return await self.sign_request("GET", url_path, {**kwargs})


async def account(self, **kwargs):
    url_path = "/fapi/v2/account"
    return await self.sign_request("GET", url_path, {**kwargs})


async def change_leverage(self, symbol: str, leverage: int, **kwargs):
    check_required_parameters([[symbol, "symbol"],[leverage, "leverage"]])
    params = {"symbol": symbol, "leverage":leverage, **kwargs}
    url_path = "/fapi/v1/leverage"
    return await self.sign_request("POST", url_path, params)


async def change_margin_type(self, symbol: str, marginType: str, **kwargs):
    check_required_parameters([[symbol, "symbol"],[marginType, "marginType"]])
    params = {"symbol": symbol, "marginType": marginType, **kwargs}
    url_path = "/fapi/v1/marginType"
    return await self.sign_request("POST", url_path, params)


async def modify_isolated_position_margin(self, symbol: str, amount: float, type: int, **kwargs):
    check_required_parameters([[symbol, "symbol"], [amount, "amount"], [type, "type"]])
    params = {"symbol": symbol, "amount":amount, "type":type, **kwargs}
    url_path = "/fapi/v1/positionMargin"
    return await self.sign_request("POST", url_path, params)


async def get_position_margin_history(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/positionMargin/history"
    return await self.sign_request("GET", url_path, params)


async def get_position_risk(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v2/positionRisk"
    return await self.sign_request("GET", url_path, params)


async def get_account_trades(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol": symbol, **kwargs}
    url_path = "/fapi/v1/userTrades"
    return await self.sign_request("GET", url_path, params)


async def get_income_history(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/income"
    return await self.sign_request("GET", url_path, params)


async def leverage_brackets(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/leverageBracket"
    return await self.sign_request("GET", url_path, params)


async def adl_quantile(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/adlQuantile"
    return await self.sign_request("GET", url_path, params)


async def force_orders(self, **kwargs):
    params = {**kwargs}
    url_path = "/fapi/v1/forceOrders"
    return await self.sign_request("GET", url_path, params)


async def commission_rate(self, symbol: str, **kwargs):
    check_required_parameter(symbol, "symbol")
    params = {"symbol":symbol, **kwargs}
    url_path = "/fapi/v1/commissionRate"
    return await self.sign_request("GET", url_path, params)


