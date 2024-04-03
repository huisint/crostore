import pytest
import pytest_mock
from crostore import abstract, core, exceptions

from tests import FixtureRequest


@pytest.fixture()
def platform(mocker: pytest_mock.MockerFixture) -> abstract.AbstractPlatform:
    platform = mocker.Mock(spec_set=abstract.AbstractPlatform)
    assert isinstance(platform, abstract.AbstractPlatform)
    return platform


@pytest.fixture(params=["convertable_to_item", "not_convertable_to_item"])
def message(
    request: FixtureRequest[str],
    mocker: pytest_mock.MockerFixture,
) -> abstract.AbstractMessage:
    message = mocker.Mock(spec_set=abstract.AbstractMessage)
    if (param := request.param) == "convertable_to_item":
        message.to_item.return_value = mocker.Mock(spec_set=abstract.AbstractItem)
    elif param == "not_convertable_to_item":
        message.to_item.side_effect = exceptions.ItemIdNotFoundError
    else:
        raise ValueError(f"Invalid param: {param}")
    assert isinstance(message, abstract.AbstractMessage)
    return message


@pytest.fixture()
def mailsystem(
    message: abstract.AbstractMessage,
    mocker: pytest_mock.MockerFixture,
) -> abstract.AbstractMailSystem:
    mailsystem = mocker.Mock(spec_set=abstract.AbstractMailSystem)
    mailsystem.iter_sold_messages.return_value = [message].__iter__()
    assert isinstance(mailsystem, abstract.AbstractMailSystem)
    return mailsystem


@pytest.fixture()
def datasystem(mocker: pytest_mock.MockerFixture) -> abstract.AbstractDataSystem:
    datasystem = mocker.Mock(spec_set=abstract.AbstractDataSystem)
    datasystem.iter_related_items.return_value = [
        mocker.Mock(spec_set=abstract.AbstractItem)
    ].__iter__()
    assert isinstance(datasystem, abstract.AbstractDataSystem)
    return datasystem


def test_iter_items_to_cancel(
    platform: abstract.AbstractPlatform,
    mailsystem: abstract.AbstractMailSystem,
    datasystem: abstract.AbstractDataSystem,
) -> None:
    _ = list(core.iter_items_to_cancel(platform, mailsystem, datasystem))
    # TODO: Implemets test codes
