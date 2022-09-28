import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--selenium",
        action="store",
        metavar="URL",
        help="Run tests with Selenium of URL",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "selenium: mark test to run with selenium")


def pytest_runtest_setup(item: pytest.Item) -> None:
    has_marked_selenium = bool(list(item.iter_markers("selenium")))
    has_specified_selenium_url = item.config.getoption("--selenium")
    if has_marked_selenium and not has_specified_selenium_url:
        pytest.skip("--selenium option is not specified")
