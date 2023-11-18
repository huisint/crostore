from __future__ import annotations

import dataclasses
import logging
import re

from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common import by
from selenium.webdriver.remote import webdriver
from selenium.webdriver.support import expected_conditions, wait

from crostore import abstract, exceptions

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Platform(abstract.AbstractPlatform):
    name: str = dataclasses.field(default="ヤフオク!", init=False)

    @property
    def code(self) -> str:
        return "yahoo_auction"

    @property
    def email(self) -> str:
        return "auction-master@mail.yahoo.co.jp"

    @property
    def home_url(self) -> str:
        return "https://auctions.yahoo.co.jp/"

    @property
    def _login_url(self) -> str:
        return "https://login.yahoo.co.jp/config/login"

    @property
    def _login_button_xpath(self) -> str:
        return '//*[@id="topPageArea"]//a[text()="ログイン"]'

    @property
    def _my_auction_url(self) -> str:
        return "https://auctions.yahoo.co.jp/user/jp/show/mystatus"

    def is_accessible_to_userpage(
        self, driver: webdriver.WebDriver, timeout: int = 60
    ) -> bool:
        driver.implicitly_wait(timeout)
        driver.get(self._my_auction_url)
        try:
            wait.WebDriverWait(driver, timeout).until(
                expected_conditions.url_matches(f"^{self._login_url}")
            )
            if self._try_relogin(driver, timeout):
                return True
            logger.info("Relogin is required on Yahoo!Auction")
            return False
        except selenium_exceptions.TimeoutException:
            return True

    def _try_relogin(self, driver: webdriver.WebDriver, timeout: int = 60) -> bool:
        driver.implicitly_wait(timeout)
        driver.get(self.home_url)
        try:
            login_element = driver.find_element(by.By.XPATH, self._login_button_xpath)
        except selenium_exceptions.NoSuchElementException:  # pragma: no cover
            return False
        # To avoid ElementClickInterceptedException caused by the popup
        driver.execute_script("arguments[0].click();", login_element)  # type: ignore[no-untyped-call]
        try:
            wait.WebDriverWait(driver, timeout).until(
                expected_conditions.url_matches(f"^{self._login_url}")
            )
            return False
        except selenium_exceptions.TimeoutException:
            logger.info("Relogin succeeded on Yahoo!Auction")
            return True

    def create_item(self, item_id: str, crostore_id: str) -> Item:
        return Item(self, item_id, crostore_id)

    def create_message(self, subject: str, body: str) -> Message:
        return Message(self, subject, body)


@dataclasses.dataclass(frozen=True)
class Item(abstract.AbstractItem):
    platform: Platform

    @property
    def selling_page_url(self) -> str:
        return f"https://page.auctions.yahoo.co.jp/jp/auction/{self.item_id}"

    @property
    def _cancel_page_url(self) -> str:
        return f"https://page.auctions.yahoo.co.jp/jp/show/cancelauction?aID={self.item_id}"

    @property
    def _cancel_button_xpath(self) -> str:
        return "/html/body/center[1]/form/table/tbody/tr[3]/td/input"

    def cancel(self, driver: webdriver.WebDriver, timeout: int = 60) -> None:
        driver.implicitly_wait(timeout)
        try:
            driver.get(self._cancel_page_url)
            assert (
                driver.current_url == self._cancel_page_url
            ), "Make sure you logged in to Yahoo!Auction on the browser"
            logger.debug(f"Accessed {driver.current_url}")
        except Exception as err:
            raise exceptions.ItemNotCanceledError(
                f"Cannot access the cancel page: {err}"
            ) from err
        try:
            cancel_element = driver.find_element(by.By.XPATH, self._cancel_button_xpath)
            logger.debug(f"{self._cancel_button_xpath} was found on the page")
        except Exception as err:  # pragma: no cover
            raise exceptions.ItemNotCanceledError(
                f"Cannot find the cancel button: {err}"
            ) from err
        try:
            cancel_element.click()
            logger.debug("The cancel button was clicked")
        except Exception as err:  # pragma: no cover
            raise exceptions.ItemNotCanceledError(
                f"Cannot click the cancel button: {err}"
            ) from err
        wait.WebDriverWait(driver, timeout).until(
            expected_conditions.presence_of_all_elements_located(
                (
                    by.By.XPATH,
                    "/html/body",
                )
            )
        )


@dataclasses.dataclass(frozen=True)
class Message(abstract.AbstractMessage):
    platform: Platform

    @property
    def _item_id_pattern(self) -> str:
        return "(?<=オークションID：)[a-zA-Z0-9]+"

    def to_item(self) -> Item:
        if match := re.search(self._item_id_pattern, self.body):
            item_id = match.group(0)
        else:
            raise exceptions.ItemIdNotFoundError(
                f"Any item id is not found in the message body: {self.body}"
            )
        item = Item(self.platform, item_id, crostore_id="")
        return item
