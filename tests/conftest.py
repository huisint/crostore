import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--selenium",
        action="store",
        metavar="URL",
        help="Run tests with Selenium of URL",
    )
    parser.addoption(
        "--e2e",
        action="store_true",
        help="Run end-to-end tests",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "selenium: mark test to run with selenium")
    config.addinivalue_line("markers", "e2e: mark test to be an end-to-end test")


def pytest_runtest_setup(item: pytest.Item) -> None:
    # For `selenium` marker
    has_marked_selenium = bool(list(item.iter_markers("selenium")))
    has_specified_selenium_url = item.config.getoption("--selenium")
    if has_marked_selenium and not has_specified_selenium_url:
        pytest.skip("--selenium option is not specified")
    # For `e2e` marker
    has_marked_e2e = bool(list(item.iter_markers("e2e")))
    should_run_e2e_test = item.config.getoption("--e2e")
    if has_marked_e2e and not should_run_e2e_test:
        pytest.skip("--e2e option is not specified")
