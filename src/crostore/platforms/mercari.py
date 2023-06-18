from __future__ import annotations

import dataclasses
import logging
import re

from selenium.common import exceptions as selenium_exceptions
from selenium.webdriver.common import by
from selenium.webdriver.remote import webdriver, webelement
from selenium.webdriver.support import expected_conditions, wait

from crostore import abstract, config, exceptions

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class Platform(abstract.AbstractPlatform):
    name: str = dataclasses.field(default="メルカリ", init=False)

    @property
    def code(self) -> str:
        return "mercari"

    @property
    def email(self) -> str:
        return "no-reply@mercari.jp"

    @property
    def home_url(self) -> str:
        return "https://jp.mercari.com/"

    @property
    def _signin_url(self) -> str:
        return "https://login.jp.mercari.com/signin"

    @property
    def _mypage_url(self) -> str:
        return "https://jp.mercari.com/mypage"

    def is_accessible_to_userpage(self, driver: webdriver.WebDriver) -> bool:
        driver.get(self._mypage_url)
        try:
            wait.WebDriverWait(driver, config.SELENIUM_WAIT).until(
                expected_conditions.url_matches(f"^{self._signin_url}")
            )
            logger.info("Relogin is required on Mercari")
            return False
        except selenium_exceptions.TimeoutException:
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
        return f"https://jp.mercari.com/item/{self.item_id}"

    @property
    def _edit_page_url(self) -> str:
        return f"https://jp.mercari.com/sell/edit/{self.item_id}"

    @property
    def _suspend_button_xpath(self) -> str:
        return '//*[@id="main"]/form/div[2]/div[2]/button'

    def cancel(self, driver: webdriver.WebDriver) -> None:
        url = self._edit_page_url
        try:
            driver.get(url)
            assert (
                driver.current_url == url
            ), "Make sure you logged in to Mercari on the browser"
            logger.debug(f"Accessed {url}")
        except Exception as err:
            raise exceptions.ItemNotCanceledError(
                f"Cannot access the edit page: {url}"
            ) from err
        try:
            suspend_element = driver.find_element(
                by.By.XPATH, self._suspend_button_xpath
            )
            assert isinstance(suspend_element, webelement.WebElement)
            logger.debug(f"{self._suspend_button_xpath} was found on the page")
        except Exception as err:
            raise exceptions.ItemNotCanceledError(
                f"Cannot find the suspend button: {self._suspend_button_xpath}"
            ) from err
        try:
            suspend_element.click()
            logger.debug("The suspend button was clicked")
        except Exception as err:  # pragma: no cover
            raise exceptions.ItemNotCanceledError(
                f"Cannot click the suspend button: {self._suspend_button_xpath}"
            ) from err
        wait.WebDriverWait(driver, config.SELENIUM_WAIT).until(
            expected_conditions.url_to_be(self.selling_page_url)
        )


@dataclasses.dataclass(frozen=True)
class Message(abstract.AbstractMessage):
    platform: Platform

    @property
    def _item_id_pattern(self) -> str:
        return "(?<=商品ID : )[a-zA-Z0-9]+"

    def to_item(self) -> Item:
        if match := re.search(self._item_id_pattern, self.body):
            item_id = match.group(0)
        else:
            raise exceptions.ItemIdNotFoundError(
                f"Any item id is not found in the message body: {self.body}"
            )
        item = Item(self.platform, item_id, crostore_id="")
        return item
