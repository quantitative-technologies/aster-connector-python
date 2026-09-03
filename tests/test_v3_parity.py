"""The V3 route modules must not drift from their V1 counterparts.

`account_v3_async` and `market_v3_async` are the V1 modules with `/fapi/v1` and
`/fapi/v2` routes rewritten to `/fapi/v3`. Nothing enforces that at runtime, so
a fix landing on a V1 module is silently absent from V3 -- which has already
happened once, losing the `query_order` identifier forwarding and the optional
`get_account_trades` symbol.

These tests make that drift a test failure: every method the two async clients
share must be identical apart from its route, except for a small, named set of
deliberate divergences.
"""

import asyncio
import inspect
import re

import pytest

from aster.rest_api import AsyncClient, AsyncClientV3

# V3 reclassifies the listen-key flow as USER_STREAM, so these three are signed
# where V1 relied on the X-MBX-APIKEY header. Any other divergence is drift.
INTENTIONAL_DIVERGENCE = {"new_listen_key", "renew_listen_key", "close_listen_key"}

SHARED_METHODS = sorted(
    {n for n in vars(AsyncClient) if not n.startswith("_")}
    & {n for n in vars(AsyncClientV3) if not n.startswith("_")}
)


def route_agnostic_source(fn):
    return re.sub(r'url_path = "[^"]+"', 'url_path = "<ROUTE>"', inspect.getsource(fn))


def test_the_clients_share_the_whole_v1_surface():
    assert {n for n in vars(AsyncClient) if not n.startswith("_")} <= set(SHARED_METHODS)


@pytest.mark.parametrize(
    "method", [m for m in SHARED_METHODS if m not in INTENTIONAL_DIVERGENCE]
)
def test_v3_method_differs_from_v1_only_by_its_route(method):
    assert route_agnostic_source(getattr(AsyncClientV3, method)) == route_agnostic_source(
        getattr(AsyncClient, method)
    ), f"{method} has drifted from its V1 counterpart beyond the route rewrite"


@pytest.mark.parametrize("method", sorted(INTENTIONAL_DIVERGENCE))
def test_declared_divergences_really_do_diverge(method):
    # Keeps the allowlist honest: if V1 ever adopts signing too, this fails and
    # the entry should be removed rather than left as a permanent exemption.
    assert route_agnostic_source(getattr(AsyncClientV3, method)) != route_agnostic_source(
        getattr(AsyncClient, method)
    )


class _CapturingClient:
    """Stands in for the transport so route modules can be called directly."""

    scheme = "v3"

    async def sign_request(self, http_method, url_path, payload=None, special=False):
        self.captured = {"method": http_method, "url_path": url_path, "payload": payload}
        return self.captured


def test_query_order_forwards_order_identifiers():
    # Regression: without this the identifiers are dropped and the endpoint
    # answers for the wrong order. Fixed on V1 in PR #1; V3 must carry it too.
    client = _CapturingClient()
    asyncio.run(
        AsyncClientV3.query_order(client, symbol="BTCUSDT", orderId=7, origClientOrderId="abc")
    )
    assert client.captured["payload"]["orderId"] == 7
    assert client.captured["payload"]["origClientOrderId"] == "abc"
    assert client.captured["url_path"] == "/fapi/v3/order"


def test_get_account_trades_symbol_is_optional():
    # Regression: the account-trade endpoint accepts an account-wide query.
    # Fixed on V1 in PR #2; V3 must carry it too.
    client = _CapturingClient()
    asyncio.run(AsyncClientV3.get_account_trades(client, limit=5))
    assert "symbol" not in client.captured["payload"]
    assert client.captured["payload"]["limit"] == 5

    asyncio.run(AsyncClientV3.get_account_trades(client, symbol="BTCUSDT"))
    assert client.captured["payload"]["symbol"] == "BTCUSDT"
