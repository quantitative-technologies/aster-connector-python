"""Request authentication schemes.

The V1 (legacy) API signs an urlencoded parameter string with HMAC-SHA256 over
the API secret and identifies the caller with an ``X-MBX-APIKEY`` header.  The
V3 (Pro API) surface instead signs an EIP-712 typed-data envelope with the API
wallet's private key and identifies the caller with the ``signer`` parameter.

Both are expressed as an authenticator object so that the transport in
``aster.api`` / ``aster.async_api`` stays scheme-agnostic.  Which one is used is
always an explicit choice by the caller -- it is never inferred from the shape
of a credential.
"""

import hashlib
import hmac
import threading
import time
from urllib.parse import urlencode

from aster.error import ParameterRequiredError
from aster.lib.utils import cleanNoneValue, encoded_string, get_timestamp

V1 = "v1"
V3 = "v3"

#: EIP-712 domain for ``AsterSignTransaction``.  ``chainId`` 1666 is an
#: AsterDex-specific off-chain signing identifier; it is unrelated to any
#: deposit chain and must not be confused with a network chain id.
V3_CHAIN_ID = 1666
V3_VERIFYING_CONTRACT = "0x0000000000000000000000000000000000000000"

#: Parameters that only mean something to the V1 HMAC surface.  V3 replaces
#: them with ``nonce``, so they are dropped rather than signed, which lets
#: callers share one call site across both schemes.
_V1_ONLY_PARAMS = ("timestamp", "recvWindow", "signature")

_nonce_lock = threading.Lock()
_last_nonce = 0


def get_nonce():
    """Return a strictly increasing microsecond nonce.

    AsterDex tracks nonces per agent address and keeps only the most recent
    100, rejecting any nonce below the retained minimum as expired, so
    concurrent requests from one agent must never go backwards.  Sharing the
    counter at module level keeps that guarantee across every client in the
    process.
    """
    global _last_nonce
    with _nonce_lock:
        now_us = int(time.time() * 1_000_000)
        _last_nonce = now_us if now_us > _last_nonce else _last_nonce + 1
        return _last_nonce


def _v3_value(value):
    """Render a parameter the way the V3 signing payload expects it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class HmacAuth(object):
    """Legacy V1 authentication: HMAC-SHA256 over the urlencoded parameters."""

    scheme = V1

    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret

    def headers(self):
        return {"X-MBX-APIKEY": self.key} if self.key is not None else {}

    def hmac_hex(self, data):
        """HMAC-SHA256 of ``data`` under the API secret, hex encoded."""
        return hmac.new(
            self.secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def sign(self, url_path, params, special=False):
        """Return ``(url_path, params)`` with timestamp and signature added."""
        params = dict(params or {})
        params["timestamp"] = get_timestamp()
        params["signature"] = self.hmac_hex(encoded_string(cleanNoneValue(params), special))
        return url_path, params


class Eip712Auth(object):
    """Pro API (V3) authentication: EIP-712 typed data signed by the API wallet.

    The signature covers the exact urlencoded parameter string that is sent, so
    :meth:`sign` returns the query already appended to ``url_path`` and an empty
    parameter mapping.  The transport must send those bytes verbatim.

    ``user`` (the master account wallet address) is accepted but optional: the
    exchange authenticates agent-signed ``TRADE`` / ``USER_DATA`` /
    ``USER_STREAM`` requests from ``signer`` alone.  When the master account is
    a Solana wallet, ``user`` is its base58 address; it is only ever carried as
    an opaque string, never used for signing.
    """

    scheme = V3

    def __init__(self, signer=None, private_key=None, user=None, chain_id=V3_CHAIN_ID):
        if not signer:
            raise ParameterRequiredError(["signer"])
        if not private_key:
            raise ParameterRequiredError(["privateKey"])
        self.signer = signer
        self.private_key = private_key
        self.user = user
        self.chain_id = chain_id
        self._account, self._encode = _load_eth_account()

    def headers(self):
        return {"Content-Type": "application/x-www-form-urlencoded"}

    def _typed_data(self, msg):
        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"},
                ],
                "Message": [{"name": "msg", "type": "string"}],
            },
            "primaryType": "Message",
            "domain": {
                "name": "AsterSignTransaction",
                "version": "1",
                "chainId": self.chain_id,
                "verifyingContract": V3_VERIFYING_CONTRACT,
            },
            "message": {"msg": msg},
        }

    def sign_payload(self, msg):
        """Sign an urlencoded parameter string, returning a 0x-prefixed hex signature."""
        signed = self._account.sign_message(
            self._encode(self._typed_data(msg)), private_key=self.private_key
        )
        signature = signed.signature.hex()
        return signature if signature.startswith("0x") else "0x" + signature

    def signed_query(self, params):
        """Return the full query string, signature included, for ``params``."""
        signable = {
            key: _v3_value(value)
            for key, value in cleanNoneValue(dict(params or {})).items()
            if key not in _V1_ONLY_PARAMS
        }
        signable["nonce"] = str(get_nonce())
        signable["signer"] = self.signer
        if self.user:
            signable["user"] = self.user
        # Sorted key order is what the published V3 signing reference specifies,
        # and it makes the signed payload deterministic and testable.
        query_string = urlencode(sorted(signable.items()))
        return query_string + "&signature=" + self.sign_payload(query_string)

    def sign(self, url_path, params, special=False):
        separator = "&" if "?" in url_path else "?"
        return url_path + separator + self.signed_query(params), {}


def _load_eth_account():
    """Import ``eth_account`` lazily and adapt to its typed-data API."""
    try:
        from eth_account import Account
    except ImportError as exc:  # pragma: no cover - exercised by install shape
        raise ImportError(
            "V3 (Pro API) authentication requires eth-account; install it with "
            '`pip install "aster-connector-python[v3]"`.'
        ) from exc
    try:
        from eth_account.messages import encode_typed_data

        def encode(typed_data):
            return encode_typed_data(full_message=typed_data)
    except ImportError:  # eth-account < 0.11
        from eth_account.messages import encode_structured_data as encode
    return Account, encode


def make_auth(scheme=V1, key=None, secret=None, signer=None, private_key=None, user=None):
    """Build an authenticator for ``scheme``, which must be ``"v1"`` or ``"v3"``.

    ``key``/``secret`` double as ``signer``/``private_key`` for V3 so that a
    two-field credential store can drive either scheme.
    """
    if scheme == V1:
        return HmacAuth(key=key, secret=secret)
    if scheme == V3:
        return Eip712Auth(
            signer=signer if signer is not None else key,
            private_key=private_key if private_key is not None else secret,
            user=user,
        )
    raise ValueError('auth scheme must be "v1" or "v3", got %r' % (scheme,))
