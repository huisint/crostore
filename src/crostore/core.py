import logging
from collections import abc

from crostore import abstract

logger = logging.getLogger(__name__)


def _try_message_to_item(
    message: abstract.AbstractMessage,
) -> abstract.AbstractItem | None:
    """
    Trys to_item of Message.

    Parameters
    ----------
    message : crostore.abstract.AbstractMessage[crostore.abstract.AbstractPlatform]
        The message to be tried.

    Returns
    -------
    crostore.abstract.AbstractItem[crostore.abstract.AbstractPlatform] | None
        Item object if success.
        Otherwise None.
    """
    try:
        return message.to_item()
    except Exception as err:
        logger.error(f"Cannot convert {message} to item: {err}")
        return None


def iter_items_to_cancel(
    platform: abstract.AbstractPlatform,
    ms: abstract.AbstractMailSystem,
    ds: abstract.AbstractDataSystem,
) -> abc.Generator[abstract.AbstractItem, None, None]:
    """
    Iterates items to cancel according to sold messages.

    Parameters
    ----------
    platform : crostore.abstract.AbstractPlatform
        The platform that sends sold messages.
    ms : crostore.abstract.AbstractMailSystem
        A mailsystem.
    ds : crostore.abstract.AbstractDataSystem
        A datasytem.

    Returns
    -------
    collections.abc.Generator[abstract.AbstractItem, None, None]
        A generator of items to cancel.
    """
    sold_messages = ms.iter_sold_messages(platform)
    optional_sold_items = map(_try_message_to_item, sold_messages)
    sold_items = filter(None, optional_sold_items)
    for sold_item in sold_items:
        for related_item in ds.iter_related_items(sold_item):
            yield related_item
