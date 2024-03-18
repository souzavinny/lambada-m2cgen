from os import environ
import logging
import requests

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
logger.info(f"HTTP rollup_server url is {rollup_server}")

data = requests.get(rollup_server + "/get_tx")
logger.info(f"Got tx {data.content}")

requests.post(rollup_server + "/finish", json={})
