from unittest import mock

import pytest

from crostore import abstract, core, exceptions
from tests import FixtureRequest


@pytest.fixture()
def platform() -> abstract.AbstractPlatform:
    platform = mock.Mock(spec_set=abstract.AbstractPlatform)
    return platform


@pytest.fixture(params=["convertable_to_item", "not_convertable_to_item"])
def message(
    request: FixtureRequest[str],
) -> abstract.AbstractMessage:
    message = mock.Mock(spec_set=abstract.AbstractMessage)
    if (param := request.param) == "convertable_to_item":
        message.to_item.return_value = mock.Mock(spec_set=abstract.AbstractItem)
    elif param == "not_convertable_to_item":
        message.to_item.side_effect = exceptions.ItemIdNotFoundError
    else:
        raise ValueError(f"Invalid param: {param}")
    return message


@pytest.fixture()
def mailsystem(
    message: abstract.AbstractMessage,
) -> abstract.AbstractMailSystem:
    mailsystem = mock.Mock(spec_set=abstract.AbstractMailSystem)
    mailsystem.iter_sold_messages.return_value = [message].__iter__()
    return mailsystem


@pytest.fixture()
def datasystem() -> abstract.AbstractDataSystem:
    datasystem = mock.Mock(spec_set=abstract.AbstractDataSystem)
    datasystem.iter_related_items.return_value = [
        mock.Mock(spec_set=abstract.AbstractItem)
    ].__iter__()
    return datasystem


def test_iter_items_to_cancel(
    platform: abstract.AbstractPlatform,
    mailsystem: abstract.AbstractMailSystem,
    datasystem: abstract.AbstractDataSystem,
) -> None:
    _ = list(core.iter_items_to_cancel(platform, mailsystem, datasystem))
    # TODO: Implemets test codes
