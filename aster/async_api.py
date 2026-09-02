import json
import logging
from json import JSONDecodeError

import aiohttp
from yarl import URL

from .__version__ import __version__
from aster.auth import V3, HmacAuth
from aster.error import ClientError, ServerError
from aster.lib.utils import cleanNoneValue
from aster.lib.utils import encoded_string
from aster.lib.utils import check_required_parameter


class AsyncAPI(object):
    def __init__(
        self,
        key=None,
        secret=None,
        base_url=None,
        timeout=None,
        proxies=None,
        show_limit_usage=False,
        show_header=False,
        auth=None,
    ):
        self.key = key
        self.secret = secret
        self.auth = auth if auth is not None else HmacAuth(key=key, secret=secret)
        self.timeout = timeout
        self.show_limit_usage = False
        self.show_header = False
        self.proxies = None
        self._session = None
        self._default_headers = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "aster-connector/" + __version__,
        }
        # Only set identifying headers the scheme actually uses, to avoid None values
        self._default_headers.update(self.auth.headers())

        if base_url:
            self.base_url = base_url

        if show_limit_usage is True:
            self.show_limit_usage = True

        if show_header is True:
            self.show_header = True

        if type(proxies) is dict:
            self.proxies = proxies

        return

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession(headers=self._default_headers)

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def query(self, url_path, payload=None):
        return await self.send_request("GET", url_path, payload=payload)

    async def limit_request(self, http_method, url_path, payload=None):
        """limit request is for those endpoints require API key in the header"""

        check_required_parameter(self.key, "apiKey")
        return await self.send_request(http_method, url_path, payload=payload)

    async def sign_request(self, http_method, url_path, payload=None, special=False):
        url_path, payload = self.auth.sign(url_path, payload or {}, special)
        return await self.send_request(http_method, url_path, payload, special)

    async def limited_encoded_sign_request(self, http_method, url_path, payload=None):
        """This is used for some endpoints has special symbol in the url.
        In some endpoints these symbols should not encoded
        - @
        - [
        - ]

        so we have to append those parameters in the url
        """
        if self.auth.scheme == V3:
            return await self.sign_request(http_method, url_path, payload)
        payload = dict(payload or {})
        _, payload = self.auth.sign(url_path, payload)
        signature = payload.pop("signature")
        query_string = self._prepare_params(payload)
        url_path = url_path + "?" + query_string + "&signature=" + signature
        return await self.send_request(http_method, url_path)

    async def send_request(self, http_method, url_path, payload=None, special=False):
        if payload is None:
            payload = {}
        url = self.base_url + url_path
        logging.debug("url: " + url)

        # query_string = self._prepare_params(payload, special)
        # if query_string:
        #     separator = "&" if ("?" in url) else "?"
        #     url = url + separator + query_string
        
        params = cleanNoneValue(
            {
                "url": self._request_url(url),
                "params": self._prepare_params(payload, special),
                "timeout": self.timeout,
                "proxies": self.proxies,
            }
        )

        await self._ensure_session()

        # timeout = None
        # if self.timeout is not None:
        #     timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with self._session.request(method=http_method, **params) as response:
            text = await response.text()
            logging.debug("raw response from server:" + text)
            await self._handle_exception(response, text)

            try:
                data = json.loads(text)
            except ValueError:
                data = text
            result = {}

            if self.show_limit_usage:
                limit_usage = {}
                for key in response.headers.keys():
                    header_key = key.lower()
                    if (
                        header_key.startswith("x-mbx-used-weight")
                        or header_key.startswith("x-mbx-order-count")
                        or header_key.startswith("x-sapi-used")
                    ):
                        limit_usage[header_key] = response.headers[key]
                result["limit_usage"] = limit_usage

            if self.show_header:
                result["header"] = response.headers

            if len(result) != 0:
                result["data"] = data
                return result

            return data

    def _prepare_params(self, params, special=False):
        return encoded_string(cleanNoneValue(params), special)

    def _request_url(self, url):
        """Hand aiohttp the exact bytes when the query is already signed.

        A V3 signature covers the urlencoded query verbatim, so the query must
        reach the wire unmodified; yarl would otherwise re-quote it.
        """
        if self.auth.scheme == V3 and "?" in url:
            return URL(url, encoded=True)
        return url

    async def _handle_exception(self, response, text=None):
        status_code = response.status
        if status_code < 400:
            return
        if 400 <= status_code < 500:
            try:
                err = json.loads(text if text is not None else await response.text())
            except JSONDecodeError:
                raise ClientError(status_code, None, text, response.headers)
            raise ClientError(status_code, err.get("code"), err.get("msg"), response.headers)
        raise ServerError(status_code, text if text is not None else await response.text())


