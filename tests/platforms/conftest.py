import os
import threading
from collections import abc
from http import server

import pytest
from crostore import config
from selenium import webdriver

from tests import FixtureRequest

HOSTNAME = os.environ.get("HOSTNAME", "localhost")
PORT = int(os.environ.get("PORT", "0"))


@pytest.fixture(params=["c00000", "c12345"])
def crostore_id(request: FixtureRequest[str]) -> str:
    return request.param


@pytest.fixture(scope="session")
def http_server() -> abc.Generator[server.HTTPServer, None, None]:
    http_server = server.HTTPServer(("", PORT), server.SimpleHTTPRequestHandler)
    httpthread = threading.Thread(target=http_server.serve_forever)
    httpthread.start()
    yield http_server
    http_server.server_close()
    http_server.shutdown()
    httpthread.join()


@pytest.fixture()
def urlbase(http_server: server.HTTPServer) -> str:
    port = http_server.server_port
    return f"http://{HOSTNAME}:{port}/tests/platforms/pages"


@pytest.fixture(params=["chrome"])
def driver(request: FixtureRequest[str]) -> abc.Generator[webdriver.Remote, None, None]:
    selenium_url = request.config.getoption("--selenium")
    if not selenium_url:
        return
    match request.param:
        case "chrome":
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  # type: ignore[no-untyped-call]
        case _:
            raise NotImplementedError
    driver = webdriver.Remote(selenium_url, options=options)
    driver.implicitly_wait(config.SELENIUM_WAIT)
    try:
        yield driver
    finally:
        driver.quit()
