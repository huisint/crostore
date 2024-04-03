import pytest
import pytest_mock
from crostore import exceptions
from crostore.platforms import mercari
from selenium.webdriver.remote import webdriver

from tests import FixtureRequest


@pytest.fixture()
def platform() -> mercari.Platform:
    return mercari.Platform()


@pytest.fixture(params=["m100000000", "m123456789"])
def item_id(request: FixtureRequest[str]) -> str:
    return request.param


@pytest.fixture()
def message_body(item_id: str) -> str:
    return f"""\
    Sellerさん

    メルカリをご利用いただきありがとうございます。
    下記の商品をWannabuyさんが購入しました。

    支払い方法にコンビニまたはATMを選択しているためしばらくお待ちください。
    支払い完了後に発送をお願いいたします。

    ■商品情報
    商品ID : {item_id}
    商品名 : Product Name
    商品価格 : 10,000円

    アプリを起動しホーム画面右上のアイコンから「やることリスト」が確認できます。
    """


@pytest.fixture()
def message_subject(item_id: str) -> str:
    return f"「商品名_{item_id}」の発送をお願いします"


def describe_mercari() -> None:
    def test_code(platform: mercari.Platform) -> None:
        assert platform.code == "mercari"

    def test_email(platform: mercari.Platform) -> None:
        assert platform.email == "no-reply@mercari.jp"

    def test_home_url(platform: mercari.Platform) -> None:
        assert platform.home_url == "https://jp.mercari.com/"

    @pytest.mark.selenium
    def test_is_accessible_to_userpage_when_accessible(
        platform: mercari.Platform,
        driver: webdriver.WebDriver,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        url_matches_mock = mocker.patch(
            "selenium.webdriver.support.expected_conditions.url_matches",
            return_value=lambda _: False,
        )
        assert platform.is_accessible_to_userpage(driver, timeout=10)
        assert url_matches_mock.call_args_list == [
            mocker.call(f"^{platform._signin_url}")
        ]

    @pytest.mark.selenium
    def test_is_accessible_to_userpage_when_not_accessible(
        platform: mercari.Platform,
        driver: webdriver.WebDriver,
    ) -> None:
        assert not platform.is_accessible_to_userpage(driver, timeout=10)

    def test_create_item(
        platform: mercari.Platform, item_id: str, crostore_id: str
    ) -> None:
        item = platform.create_item(item_id, crostore_id)
        assert item == mercari.Item(platform, item_id, crostore_id)

    def test_create_message(
        platform: mercari.Platform, message_subject: str, message_body: str
    ) -> None:
        message = platform.create_message(message_subject, message_body)
        assert message == mercari.Message(platform, message_subject, message_body)


def describe_mercari_item() -> None:
    @pytest.fixture()
    def item(platform: mercari.Platform, item_id: str) -> mercari.Item:
        return mercari.Item(
            platform=platform,
            item_id=item_id,
            crostore_id="",
        )

    def test_selling_page_url(item: mercari.Item) -> None:
        assert item.selling_page_url == f"https://jp.mercari.com/item/{item.item_id}"

    @pytest.mark.selenium
    @pytest.mark.usefixtures("http_server")
    @pytest.mark.parametrize("item_id", ["m000000000"])
    def test_cancel_when_page_does_not_exist(
        item: mercari.Item,
        driver: webdriver.WebDriver,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "selenium.webdriver.remote.webdriver.WebDriver.get", side_effect=Exception
        )
        with pytest.raises(exceptions.ItemNotCanceledError):
            item.cancel(driver, timeout=10)

    @pytest.mark.selenium
    @pytest.mark.usefixtures("http_server")
    @pytest.mark.parametrize("item_id", ["m000000000"])
    def test_cancel_when_suspend_button_does_not_exist(
        item: mercari.Item,
        driver: webdriver.WebDriver,
        urlbase: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.platforms.mercari.Item._edit_page_url",
            new_callable=mocker.PropertyMock,
            return_value=urlbase + "/empty_page.html",
        )
        with pytest.raises(exceptions.ItemNotCanceledError):
            item.cancel(driver, timeout=10)


def describe_mercari_message() -> None:
    @pytest.fixture()
    def message(
        platform: mercari.Platform, message_subject: str, message_body: str
    ) -> mercari.Message:
        return mercari.Message(
            platform=platform,
            subject=message_subject,
            body=message_body,
        )

    def test_to_item(
        message: mercari.Message, platform: mercari.Platform, item_id: str
    ) -> None:
        assert message.to_item() == mercari.Item(
            platform=platform,
            item_id=item_id,
            crostore_id="",
        )

    @pytest.mark.parametrize("item_id", [""], ids=["empty_id"])
    def test_to_item_when_item_id_is_not_found(message: mercari.Message) -> None:
        with pytest.raises(exceptions.ItemIdNotFoundError):
            message.to_item()
