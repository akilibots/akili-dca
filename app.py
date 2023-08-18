import datetime
import requests
import urllib
import threading
import time

import pyjson5

from dydx3 import Client
from dydx3.constants import *
from dydx3.helpers.request_helpers import generate_now_iso

from config import config, tokens


# Global Vars
xchange = None
signature = None
signature_time = None
account = None


def log(msg):
    def _log(_msg):
        conf = config()
        keys = tokens()
        _msg = conf["main"]["name"] + ":" + _msg
        print(datetime.datetime.now().isoformat(), _msg)

        if keys["telegram"]["chatid"] == "" or keys["telegram"]["bottoken"] == "":
            return

        params = {"chat_id": keys["telegram"]["chatid"], "text": _msg}
        payload_str = urllib.parse.urlencode(params, safe="@")
        requests.get(
            "https://api.telegram.org/bot"
            + keys["telegram"]["bottoken"]
            + "/sendMessage",
            params=payload_str,
        )

    threading.Thread(target=_log, args=[msg]).start()


def main():
    global orders
    global order_id
    global signature_time
    global signature
    global account
    global xchange

    startTime = datetime.datetime.now()

    # Load configuration
    conf = config()
    keys = tokens()

    log(f"Start {startTime.isoformat()}")

    log("Exchange Connect.")
    xchange = Client(
        network_id=NETWORK_ID_MAINNET,
        host=API_HOST_MAINNET,
        api_key_credentials={
            "key": keys["dydx"]["APIkey"],
            "secret": keys["dydx"]["APIsecret"],
            "passphrase": keys["dydx"]["APIpassphrase"],
        },
        stark_private_key=keys["dydx"]["stark_private_key"],
        default_ethereum_address=keys["dydx"]["default_ethereum_address"],
    )

    signature_time = generate_now_iso()
    signature = xchange.private.sign(
        request_path="/ws/accounts",
        method="GET",
        iso_timestamp=signature_time,
        data={},
    )

    while True:
        account = xchange.private.get_account().data["account"]

        conf = config()

        xchange.private.create_order(
            position_id=account["positionId"],
            market=conf["main"]["market"],
            side=ORDER_SIDE_BUY if conf["dca"]["side"] == "buy" else ORDER_SIDE_SELL,
            order_type=ORDER_TYPE_MARKET,
            limit_fee="0.1",
            post_only=False,
            price="1000000",
            time_in_force=TIME_IN_FORCE_IOC,
            expiration_epoch_seconds=int(time.time() + 120),
            size=str(conf["dca"]["size"]),
        )

        log(f"{conf['dca']['side']} order size {conf['dca']['size']}")
        time.sleep(conf["dca"]["freq"])


if __name__ == "__main__":
    main()
