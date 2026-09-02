"""User data stream endpoints (V3).

Pro API (V3) counterpart of :mod:`aster.rest_api.data_stream_listen_key_async`.
V3 classifies these as ``USER_STREAM``, so unlike V1 -- which identified the
caller with an ``X-MBX-APIKEY`` header alone -- every call is signed.
"""


async def new_listen_key(self):
    url_path = "/fapi/v3/listenKey"
    return await self.sign_request("POST", url_path)


async def renew_listen_key(self, listenKey: str = None):
    url_path = "/fapi/v3/listenKey"
    return await self.sign_request("PUT", url_path, {"listenKey": listenKey})


async def close_listen_key(self, listenKey: str = None):
    url_path = "/fapi/v3/listenKey"
    return await self.sign_request("DELETE", url_path, {"listenKey": listenKey})
