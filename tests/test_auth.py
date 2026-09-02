"""Request-signing contract for both authentication schemes.

The V1 tests are regression guards: V1 signing moved out of the transport and
into an authenticator, and production accounts still depend on it, so the
resulting query and signature must stay byte-for-byte what they were.

The V3 tests pin the parts of the Pro API signing payload that are easy to get
subtly wrong and that fail as an opaque "Signature check failed" when wrong:
key ordering, value rendering, which parameters are signed, and nonce
monotonicity under concurrency.

No network and no credentials: V3 signatures are checked by recovering the
signer address from the signature.
"""

import hashlib
import hmac
import inspect
import re
import threading
import urllib.parse

import pytest

from aster.auth import V1, V3, Eip712Auth, HmacAuth, get_nonce, make_auth
from aster.error import ParameterRequiredError
from aster.lib.utils import cleanNoneValue, encoded_string
from aster.rest_api import AsyncClient, AsyncClientV3, Client

eth_account = pytest.importorskip("eth_account", reason="V3 signing needs the 'v3' extra")
from eth_account import Account
from eth_account.messages import encode_typed_data

KEY = "a" * 64
SECRET = "b" * 64
# Throwaway key; only ever used to sign locally and recover the address back.
ACCOUNT = Account.from_key(
    "0x4fd0a42218f3eae43a6ce26d22544e986139a01e5b34a62db53757ffca81bae1"
)
SIGNER = ACCOUNT.address
PRIVATE_KEY = ACCOUNT.key.hex()


PINNED_TIMESTAMP = 1748310859508


@pytest.fixture
def pinned_clock(monkeypatch):
    """Freeze the V1 timestamp so signatures are reproducible."""
    monkeypatch.setattr("aster.auth.get_timestamp", lambda: PINNED_TIMESTAMP)


def legacy_v1_sign(payload, secret, special=False):
    """The pre-authenticator V1 implementation, inlined as the oracle."""
    payload = dict(payload)
    payload["timestamp"] = PINNED_TIMESTAMP
    query = encoded_string(cleanNoneValue(payload), special)
    return query, hmac.new(
        secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def v3_query(auth, params=None, url_path="/fapi/v3/balance"):
    path, transport_params = auth.sign(url_path, params or {})
    assert transport_params == {}, "V3 must not hand params to the transport separately"
    query, _, signature = path.partition("?")[2].rpartition("&signature=")
    return query, signature


# --- V1: unchanged behaviour -------------------------------------------------


@pytest.mark.parametrize(
    "payload,special",
    [
        ({"symbol": "BTCUSDT", "side": "BUY"}, False),
        ({"symbol": "BTCUSDT", "orderId": None}, False),
        # special=True rewrites %27 -> %22 so list payloads carry double quotes.
        ({"batchOrders": [{"symbol": "BTCUSDT", "side": "BUY"}]}, True),
        ({"symbol": "BTCUSDT", "origClientOrderIdList": '["a","b"]'}, True),
    ],
)
def test_v1_signature_is_byte_identical_to_the_legacy_implementation(
    payload, special, pinned_clock
):
    _, signed = HmacAuth(key=KEY, secret=SECRET).sign("/fapi/v1/order", dict(payload), special)
    signature = signed.pop("signature")
    query = encoded_string(cleanNoneValue(signed), special)
    expected_query, expected_signature = legacy_v1_sign(payload, SECRET, special)
    assert query == expected_query
    assert signature == expected_signature


def test_v1_keeps_parameters_out_of_the_path_and_identifies_by_header():
    auth = HmacAuth(key=KEY, secret=SECRET)
    path, params = auth.sign("/fapi/v1/order", {"symbol": "BTCUSDT"})
    assert path == "/fapi/v1/order"
    assert "timestamp" in params and "signature" in params
    assert auth.headers() == {"X-MBX-APIKEY": KEY}


def test_v1_omits_the_key_header_when_no_key_is_configured():
    assert HmacAuth().headers() == {}


@pytest.mark.parametrize("client_cls", [Client, AsyncClient])
def test_get_sign_shim_still_returns_legacy_hmac(client_cls):
    # Retained for V1 subclasses that called or overrode the private helper.
    client = client_cls(key=KEY, secret=SECRET)
    assert client._get_sign("payload") == hmac.new(
        SECRET.encode(), b"payload", hashlib.sha256
    ).hexdigest()


# --- V3: signing payload -----------------------------------------------------


def test_v3_signature_recovers_to_the_signer_address():
    auth = Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY)
    query, signature = v3_query(auth)
    recovered = Account.recover_message(
        encode_typed_data(full_message=auth._typed_data(query)), signature=signature
    )
    assert recovered == SIGNER


def test_v3_domain_matches_the_published_signing_envelope():
    domain = Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY)._typed_data("x")["domain"]
    assert domain == {
        "name": "AsterSignTransaction",
        "version": "1",
        # An AsterDex off-chain signing identifier, not a network chain id.
        "chainId": 1666,
        "verifyingContract": "0x0000000000000000000000000000000000000000",
    }


def test_v3_payload_is_sorted_and_carries_nonce_and_signer():
    query, _ = v3_query(
        Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY), {"symbol": "BTCUSDT"}
    )
    pairs = urllib.parse.parse_qsl(query)
    assert [key for key, _ in pairs] == sorted(key for key, _ in pairs)
    fields = dict(pairs)
    assert fields["signer"] == SIGNER
    assert fields["nonce"].isdigit() and len(fields["nonce"]) == 16


def test_v3_drops_v1_only_parameters_and_renders_booleans_as_json():
    query, _ = v3_query(
        Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY),
        {"timestamp": 1, "recvWindow": 5000, "signature": "stale", "reduceOnly": True},
    )
    fields = dict(urllib.parse.parse_qsl(query))
    # V3 replaces timestamp/recvWindow with nonce; signing them would be wrong
    # and carrying a stale signature into the payload doubly so.
    assert not {"timestamp", "recvWindow"} & set(fields)
    assert fields["reduceOnly"] == "true"


def test_v3_drops_none_valued_parameters():
    query, _ = v3_query(
        Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY),
        {"symbol": "BTCUSDT", "orderId": None},
    )
    assert "orderId" not in dict(urllib.parse.parse_qsl(query))


def test_v3_user_is_optional_and_opaque():
    without = Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY)
    assert "user" not in dict(urllib.parse.parse_qsl(v3_query(without)[0]))
    # A Solana master account is a base58 string and is never signed with.
    solana = "6mSp4BuWCNgRSwv8JopQwCma26hmBT8jrcgJNadq23Gt"
    with_user = Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY, user=solana)
    assert dict(urllib.parse.parse_qsl(v3_query(with_user)[0]))["user"] == solana


def test_v3_appends_to_an_existing_query_rather_than_starting_a_second_one():
    auth = Eip712Auth(signer=SIGNER, private_key=PRIVATE_KEY)
    path, _ = auth.sign("/fapi/v3/order?already=1", {})
    assert path.count("?") == 1


def test_v3_requires_both_signer_and_private_key():
    with pytest.raises(ParameterRequiredError):
        Eip712Auth(signer=None, private_key=PRIVATE_KEY)
    with pytest.raises(ParameterRequiredError):
        Eip712Auth(signer=SIGNER, private_key=None)


# --- V3: nonce ---------------------------------------------------------------


def test_nonce_is_unique_and_monotonic_under_concurrency():
    # Nonces are tracked per agent address and only the most recent 100 are
    # retained, so parallel requests must never repeat a nonce or go backwards.
    batches = []
    lock = threading.Lock()

    def collect():
        values = [get_nonce() for _ in range(500)]
        with lock:
            batches.append(values)

    threads = [threading.Thread(target=collect) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    flat = [value for batch in batches for value in batch]
    assert len(set(flat)) == len(flat)
    for batch in batches:
        assert batch == sorted(batch)


# --- scheme selection --------------------------------------------------------


def test_make_auth_selects_by_scheme_and_falls_back_to_key_and_secret():
    assert isinstance(make_auth(V1, key=KEY, secret=SECRET), HmacAuth)
    # A two-field credential store drives either scheme.
    v3 = make_auth(V3, key=SIGNER, secret=PRIVATE_KEY)
    assert isinstance(v3, Eip712Auth)
    assert v3.signer == SIGNER


def test_make_auth_rejects_an_unknown_scheme():
    with pytest.raises(ValueError, match='must be "v1" or "v3"'):
        make_auth("v2", key=KEY, secret=SECRET)


# --- client wiring -----------------------------------------------------------


def test_v3_client_defaults_and_headers():
    client = AsyncClientV3(key=SIGNER, secret=PRIVATE_KEY)
    assert client.base_url == "https://fapi.asterdex.com"
    assert client.auth.scheme == V3
    headers = client._default_headers
    # V3 identifies by the signer parameter, so the V1 key header must be absent.
    assert "X-MBX-APIKEY" not in headers
    assert headers["Content-Type"] == "application/x-www-form-urlencoded"


def test_v1_client_is_unaffected_by_the_v3_addition():
    client = AsyncClient(key=KEY, secret=SECRET)
    assert client.base_url == "https://fapi.asterdex.com"
    assert client.auth.scheme == V1
    assert client._default_headers["X-MBX-APIKEY"] == KEY


def _route(client_cls, method):
    return re.search(
        r'url_path = "([^"]+)"', inspect.getsource(getattr(client_cls, method))
    ).group(1)


@pytest.mark.parametrize(
    "method,route",
    [
        ("account", "/fapi/v3/accountWithJoinMargin"),
        ("balance", "/fapi/v3/balance"),
        ("get_position_risk", "/fapi/v3/positionRisk"),
        ("get_orders", "/fapi/v3/openOrders"),
        ("get_open_orders", "/fapi/v3/openOrder"),
        ("get_all_orders", "/fapi/v3/allOrders"),
        ("get_account_trades", "/fapi/v3/userTrades"),
        ("new_order", "/fapi/v3/order"),
        ("query_order", "/fapi/v3/order"),
        ("cancel_order", "/fapi/v3/order"),
        ("cancel_open_orders", "/fapi/v3/allOpenOrders"),
        ("change_leverage", "/fapi/v3/leverage"),
        ("leverage_brackets", "/fapi/v3/leverageBracket"),
        ("commission_rate", "/fapi/v3/commissionRate"),
        ("new_listen_key", "/fapi/v3/listenKey"),
        ("ticker_price", "/fapi/v3/ticker/price"),
        ("depth", "/fapi/v3/depth"),
    ],
)
def test_v3_routes(method, route):
    # V3 renames only the account snapshot; every other route keeps its V1 name
    # under /fapi/v3, which is what lets callers swap clients unchanged.
    assert _route(AsyncClientV3, method) == route


def test_v3_client_exposes_the_same_surface_as_the_v1_client():
    v1_methods = {n for n in vars(AsyncClient) if not n.startswith("_")}
    assert v1_methods - {n for n in vars(AsyncClientV3) if not n.startswith("_")} == set()


@pytest.mark.parametrize(
    "method", ["new_listen_key", "renew_listen_key", "close_listen_key"]
)
def test_v3_listen_key_calls_are_signed(method):
    # V3 reclassifies the listen-key flow as USER_STREAM; V1 relied on the
    # X-MBX-APIKEY header alone.
    assert "sign_request" in inspect.getsource(getattr(AsyncClientV3, method))
    assert "send_request" in inspect.getsource(getattr(AsyncClient, method))
