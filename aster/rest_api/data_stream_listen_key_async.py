from aster.lib.utils import check_required_parameter


async def new_listen_key(self):
    url_path = "/fapi/v1/listenKey"
    return await self.send_request("POST", url_path)


async def renew_listen_key(self, listenKey: str):
    check_required_parameter(listenKey, "listenKey")
    url_path = "/fapi/v1/listenKey"
    return await self.send_request("PUT", url_path, {"listenKey": listenKey})


async def close_listen_key(self, listenKey: str):
    url_path = "/fapi/v1/listenKey"
    return await self.send_request("DELETE", url_path)


