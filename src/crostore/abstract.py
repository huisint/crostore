from __future__ import annotations

import abc
import collections.abc
import dataclasses

from selenium.webdriver.remote import webdriver


@dataclasses.dataclass(frozen=True)
class AbstractPlatform(abc.ABC):
    """
    Abstract Class for Platform.

    Platform represents a service where users are selling items on.
    """

    name: str
    """The name of the platform."""

    @property
    @abc.abstractmethod
    def code(self) -> str:
        """The code of the platform."""

    @property
    @abc.abstractmethod
    def email(self) -> str:
        """The email address from which the platform sends messages to their users."""

    @property
    @abc.abstractmethod
    def home_url(self) -> str:
        """The homepage URL of the platform."""

    @abc.abstractmethod
    def is_accessible_to_userpage(
        self, driver: webdriver.WebDriver, timeout: int = 60
    ) -> bool:
        """
        Returns true if accessible to user specific pages.

        Parameters
        ----------
        driver : selenium.webdriver.remote.webdriver.Webdriver
            A selenium webdriver.
        timeout : int
            Time to wait in seconds.

        Returns
        -------
        bool
            Whether accessible to user specific pages.
        """

    @abc.abstractmethod
    def create_item(self, item_id: str, crostore_id: str) -> AbstractItem:
        """
        Creates an item for the platform.

        Parameters
        ----------
        item_id : str
            The item id assigned by the platform.
        crostore_id : str
            The ID assigned by Crostore.

        Returns
        -------
        crostore.abstract.AbstractItem
            The created item.
        """

    @abc.abstractmethod
    def create_message(self, subject: str, body: str) -> AbstractMessage:
        """
        Creates a message for the platform.

        Parameters
        ----------
        subject : str
            The subject of the message.
        body : str
            The body of the message.

        Returns
        -------
        crostore.abstract.AbstractMessage
            The created message.
        """


@dataclasses.dataclass(frozen=True)
class AbstractItem(abc.ABC):
    """
    Abstract class for Item.

    Item represents an item users selling on platforms.
    """

    platform: AbstractPlatform
    """The platform where the item is selling on."""
    item_id: str
    """The item id assigned by the platform."""
    crostore_id: str
    """The ID assigned by Crostore."""

    @property
    @abc.abstractmethod
    def selling_page_url(self) -> str:
        """The selling page URL of the item."""

    @abc.abstractmethod
    def cancel(self, driver: webdriver.WebDriver, timeout: int = 60) -> None:
        """
        Cancels selling of the item.

        Parameters
        ----------
        driver : selenium.webdriver.remote.webdriver.Webdriver
            A selenium webdriver.
        timeout : int
            Time to wait in seconds.

        Raises
        ------
        crostore.exceptions.ItemNotCanceledError
            If the cancellation could not be done.
        """


@dataclasses.dataclass(frozen=True)
class AbstractMessage(abc.ABC):
    """
    Abstract class for Message.

    Message represents a message that platforms sends to users when an event happens.
    """

    platform: AbstractPlatform
    """The platfrom who sends the message."""
    subject: str
    """The subject of the message."""
    body: str = dataclasses.field(repr=False)
    """The body of the message."""

    @abc.abstractmethod
    def to_item(self) -> AbstractItem:
        """
        Converts to an item.

        Returns
        -------
        crostore.abstract.AbstractItem
            The item constructed from the message.

        Raises
        ------
        crostore.exceptions.ItemIdNotFoundError
            If it could not be converted.
        """


class AbstractMailSystem(abc.ABC):
    @abc.abstractmethod
    def iter_sold_messages(
        self, platform: AbstractPlatform
    ) -> collections.abc.Generator[AbstractMessage, None, None]:
        """
        Iterates sold messages sent by platforms.

        Parameters
        ----------
        platform : crostore.abstract.AbstractPlatform
            The platform that sends mesaages.

        Returns
        -------
        collections.abc.Generator[AbstractMessage, None, None]
            An iterator of sold messages.
        """


class AbstractDataSystem(abc.ABC):
    @abc.abstractmethod
    def iter_related_items(
        self, item: AbstractItem
    ) -> collections.abc.Generator[AbstractItem, None, None]:
        """
        Iterates items that should be canceled when `item` is sold.

        Parameters
        ----------
        item : crostore.abstract.AbstractItem
            The item to which the retrieved items are related.

        Returns
        -------
        collections.abc.Generator[crostore.abstract.AbstractItem, None, None]
            An iterator of related items.
        """

    @abc.abstractmethod
    def update(self, item: AbstractItem) -> None:
        """
        Updates an item.

        Parameters
        ----------
        item : crostore.abstract.AbstractItem
            The item to update.
        """

    @abc.abstractmethod
    def delete(self, item: AbstractItem) -> None:
        """
        Deletes an item.

        Parameters
        ----------
        item : crostore.abstract.AbstractItem
            The item to delete.
        """
