import pytest
import pytest_mock
from selenium.webdriver.remote import webdriver

from crostore import exceptions
from crostore.platforms import yahoo_auction
from tests import FixtureRequest


@pytest.fixture()
def platform() -> yahoo_auction.Platform:
    return yahoo_auction.Platform()


@pytest.fixture(params=["abcde12345", "vwxyzABCDE"])
def item_id(request: FixtureRequest[str]) -> str:
    return request.param


@pytest.fixture()
def message_body(item_id: str) -> str:
    return f"""\
    Seller様

    おめでとうございます！　商品が落札されました。

    落札者からの連絡をお待ちください。

    オークション情報
    ￣￣￣￣￣￣￣￣￣￣
    商品：Product Name
    オークションID：{item_id}
    開始価格：10,000 円
    開始日時：1月 1日 0時 0分
    終了日時：12月 31日 0時 0分
    --------------------
    入札件数：1
    落札金額：10,000 円
    """


@pytest.fixture()
def message_subject(item_id: str) -> str:
    return f"ヤフオク!-終了（落札者あり）：商品名_{item_id}"


def describe_yahoo_auction() -> None:
    def test_code(platform: yahoo_auction.Platform) -> None:
        assert platform.code == "yahoo_auction"

    def test_email(platform: yahoo_auction.Platform) -> None:
        assert platform.email == "auction-master@mail.yahoo.co.jp"

    def test_home_url(platform: yahoo_auction.Platform) -> None:
        assert platform.home_url == "https://auctions.yahoo.co.jp/"

    @pytest.mark.selenium
    def test_is_accessible_to_userpage_when_accessible(
        platform: yahoo_auction.Platform,
        driver: webdriver.WebDriver,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        url_matches_mock = mocker.patch(
            "selenium.webdriver.support.expected_conditions.url_matches",
            return_value=lambda _: False,
        )
        assert platform.is_accessible_to_userpage(driver)
        assert url_matches_mock.call_args_list == [
            mocker.call(f"^{platform._login_url}")
        ]

    @pytest.mark.selenium
    def test_is_accessible_to_userpage_when_relogin_succeeds(
        platform: yahoo_auction.Platform,
        driver: webdriver.WebDriver,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        url_matches_mock = mocker.patch(
            "selenium.webdriver.support.expected_conditions.url_matches",
            side_effect=[lambda _: True, lambda _: False],
        )
        assert platform.is_accessible_to_userpage(driver)
        assert url_matches_mock.call_args_list == [
            mocker.call(f"^{platform._login_url}"),
            mocker.call(f"^{platform._login_url}"),
        ]

    @pytest.mark.selenium
    def test_is_accessible_to_userpage_when_not_accessible(
        platform: yahoo_auction.Platform,
        driver: webdriver.WebDriver,
    ) -> None:
        assert not platform.is_accessible_to_userpage(driver)

    def test_create_item(
        platform: yahoo_auction.Platform, item_id: str, crostore_id: str
    ) -> None:
        item = platform.create_item(item_id, crostore_id)
        assert item == yahoo_auction.Item(platform, item_id, crostore_id)

    def test_create_message(
        platform: yahoo_auction.Platform, message_subject: str, message_body: str
    ) -> None:
        message = platform.create_message(message_subject, message_body)
        assert message == yahoo_auction.Message(platform, message_subject, message_body)


def describe_yahoo_auction_item() -> None:
    @pytest.fixture()
    def item(platform: yahoo_auction.Platform, item_id: str) -> yahoo_auction.Item:
        return yahoo_auction.Item(
            platform=platform,
            item_id=item_id,
            crostore_id="",
        )

    def test_selling_page_url(item: yahoo_auction.Item) -> None:
        assert (
            item.selling_page_url
            == f"https://page.auctions.yahoo.co.jp/jp/auction/{item.item_id}"
        )

    @pytest.mark.selenium
    @pytest.mark.usefixtures("http_server")
    def test_cancel_when_page_exists(
        item: yahoo_auction.Item,
        driver: webdriver.WebDriver,
        urlbase: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.platforms.yahoo_auction.Item._cancel_page_url",
            new_callable=mocker.PropertyMock,
            return_value=urlbase + "/yahoo_auction_cancel_page.html",
        )
        item.cancel(driver)

    @pytest.mark.selenium
    @pytest.mark.usefixtures("http_server")
    @pytest.mark.parametrize("item_id", ["abcdeFGHIJ"])
    def test_cancel_when_page_does_not_exist(
        item: yahoo_auction.Item,
        driver: webdriver.WebDriver,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "selenium.webdriver.remote.webdriver.WebDriver.get", side_effect=Exception
        )
        with pytest.raises(exceptions.ItemNotCanceledError):
            item.cancel(driver)

    @pytest.mark.selenium
    @pytest.mark.usefixtures("http_server")
    @pytest.mark.parametrize("item_id", ["abcdeFGHIJ"])
    def test_cancel_when_suspend_button_does_not_exist(
        item: yahoo_auction.Item,
        driver: webdriver.WebDriver,
        urlbase: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.platforms.yahoo_auction.Item._cancel_page_url",
            new_callable=mocker.PropertyMock,
            return_value=urlbase + "/empty_page.html",
        )
        with pytest.raises(exceptions.ItemNotCanceledError):
            item.cancel(driver)


def describe_yahoo_auction_message() -> None:
    @pytest.fixture()
    def message(
        platform: yahoo_auction.Platform, message_subject: str, message_body: str
    ) -> yahoo_auction.Message:
        return yahoo_auction.Message(
            platform=platform,
            subject=message_subject,
            body=message_body,
        )

    def test_to_item(
        message: yahoo_auction.Message,
        platform: yahoo_auction.Platform,
        item_id: str,
    ) -> None:
        assert message.to_item() == yahoo_auction.Item(
            platform=platform,
            item_id=item_id,
            crostore_id="",
        )

    @pytest.mark.parametrize("item_id", [""], ids=["empty_id"])
    def test_to_item_when_item_id_is_not_found(
        message: yahoo_auction.Message,
    ) -> None:
        with pytest.raises(exceptions.ItemIdNotFoundError):
            message.to_item()
