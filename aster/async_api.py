import hmac
import json
import logging
import hashlib
from json import JSONDecodeError

import aiohttp

from .__version__ import __version__
from aster.error import ClientError, ServerError
from aster.lib.utils import get_timestamp
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
    ):
        self.key = key
        self.secret = secret
        self.timeout = timeout
        self.show_limit_usage = False
        self.show_header = False
        self.proxies = None
        self._session = None
        self._default_headers = {
            "Content-Type": "application/json;charset=utf-8",
            "User-Agent": "aster-connector/" + __version__,
        }
        # Only set the API key header if a key is provided to avoid None header values
        if key is not None:
            self._default_headers["X-MBX-APIKEY"] = key

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
        if payload is None:
            payload = {}
        payload["timestamp"] = get_timestamp()
        query_string = self._prepare_params(payload, special)
        signature = self._get_sign(query_string)
        payload["signature"] = signature
        return await self.send_request(http_method, url_path, payload, special)

    async def limited_encoded_sign_request(self, http_method, url_path, payload=None):
        """This is used for some endpoints has special symbol in the url.
        In some endpoints these symbols should not encoded
        - @
        - [
        - ]

        so we have to append those parameters in the url
        """
        if payload is None:
            payload = {}
        payload["timestamp"] = get_timestamp()
        query_string = self._prepare_params(payload)
        signature = self._get_sign(query_string)
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
                "url": url,
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

    def _get_sign(self, data):
        m = hmac.new(self.secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256)
        return m.hexdigest()

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


