from __future__ import annotations

import base64
import typing as t

import pytest
import pytest_mock
from crostore import abstract
from crostore.mailsystems import gmail
from crostore.platforms import mercari, yahoo_auction

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.gmail.v1 import schemas


def create_messages() -> list[schemas.Message]:
    messages: list[schemas.Message] = [
        {
            "id": f"messageId{i}",
            "payload": {
                "headers": [{"name": "subject", "value": f"message{i}"}],
                "body": {
                    "data": base64.urlsafe_b64encode(
                        f"This is test message {i}.".encode("utf-8")
                    ).decode("utf-8")
                },
            },
        }
        for i in range(3)
    ]
    return messages


def test_build(mocker: pytest_mock.MockerFixture) -> None:
    build_mock = mocker.patch("googleapiclient.discovery.build")
    creds_mock = mocker.Mock()
    rsc = gmail.build(creds_mock)
    assert rsc == build_mock.return_value
    build_mock.assert_called_once_with(
        serviceName="gmail",
        version="v1",
        credentials=creds_mock,
    )


@pytest.mark.parametrize("label", [{}])
def test_list_label_returns(
    label: schemas.Label,
    mocker: pytest_mock.MockerFixture,
) -> None:
    response = dict(labels=[label])
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().labels().list
    list_mock.return_value.execute.return_value = response
    assert gmail.list_label(rsc_mock) == response.get("labels", list())


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
def test_list_label_api_call(
    user_id: str,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail.list_label(rsc_mock, user_id)
    list_mock = rsc_mock.users().labels().list
    list_mock.assert_called_once_with(userId=user_id)
    list_mock.return_value.execute.assert_called_once_with()


@pytest.mark.parametrize("label", [{}])
def test_create_label_returns(
    label: schemas.Label,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    create_mock = rsc_mock.users().labels().create
    create_mock.return_value.execute.return_value = label
    assert gmail.create_label(rsc_mock, label=label) == label


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("label", [{}])
def test_create_label_api_call(
    user_id: str,
    label: schemas.Label,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail.create_label(rsc_mock, user_id, label=label)
    create_mock = rsc_mock.users().labels().create
    create_mock.assert_called_once_with(
        userId=user_id,
        body=label,
    )
    create_mock.return_value.execute.assert_called_once_with()


@pytest.mark.parametrize("messages", [create_messages(), [], None])
@pytest.mark.parametrize("next_page_token", ["page_token", None])
@pytest.mark.parametrize("result_size_estimate", [0, 100, None])
def test_list_message_returns(
    messages: list[schemas.Message] | None,
    next_page_token: str | None,
    result_size_estimate: int,
    mocker: pytest_mock.MockerFixture,
) -> None:
    response: schemas.ListMessagesResponse = dict()
    if messages is not None:
        response["messages"] = messages
    if next_page_token is not None:
        response["nextPageToken"] = next_page_token
    if result_size_estimate is not None:
        response["resultSizeEstimate"] = result_size_estimate
    rsc_mock = mocker.Mock()
    list_mock = rsc_mock.users().messages().list
    list_mock.return_value.execute.return_value = response
    result = gmail.list_message(rsc_mock)
    assert result[0] == response.get("messages", list())
    assert result[1] == response.get("nextPageToken", "")
    assert result[2] == response.get("resultSizeEstimate", 0)


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("query", ["", "query"])
@pytest.mark.parametrize("max_results", [100, 200])
@pytest.mark.parametrize("page_token", [None, "page_token"])
@pytest.mark.parametrize("label_ids", [None, ["label"]])
@pytest.mark.parametrize("include_spam_trash", [True, False])
def test_list_message_api_call(
    user_id: str,
    query: str,
    max_results: int,
    page_token: str | None,
    label_ids: list[str] | None,
    include_spam_trash: bool,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail.list_message(
        rsc_mock,
        user_id,
        query=query,
        max_results=max_results,
        page_token=page_token,
        label_ids=label_ids,
        include_spam_trash=include_spam_trash,
    )
    list_mock = rsc_mock.users().messages().list
    list_mock.assert_called_once_with(
        userId=user_id,
        q=query,
        maxResults=max_results,
        pageToken=page_token or "",
        labelIds=label_ids or [],
        includeSpamTrash=include_spam_trash,
    )
    list_mock.return_value.execute.assert_called_once_with()


@pytest.mark.parametrize("message", create_messages())
def test_get_message_returns(
    message: schemas.Message,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    get_mock = rsc_mock.users().messages().get
    get_mock.return_value.execute.return_value = message
    assert gmail.get_message(rsc_mock, id="id") == message


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("id", ["foo", "bar"])
@pytest.mark.parametrize("format", ["minimal", "full", "raw", "metadata"])
def test_get_message_api_call(
    user_id: str,
    id: str,
    format: t.Literal["minimal", "full", "raw", "metadata"],
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail.get_message(rsc_mock, user_id, id=id, format=format)
    get_mock = rsc_mock.users().messages().get
    get_mock.assert_called_once_with(userId=user_id, id=id, format=format)
    get_mock.return_value.execute_assert_called_once_with()


@pytest.mark.parametrize("message", create_messages())
def test_modify_message_returns(
    message: schemas.Message,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    modify_mock = rsc_mock.users().messages().modify
    modify_mock.return_value.execute.return_value = message
    assert gmail.modify_message(rsc_mock, id="id") == message


@pytest.mark.parametrize("user_id", ["me", "foo@example.com"])
@pytest.mark.parametrize("id", ["messageId1", "messageId2"])
@pytest.mark.parametrize(
    "add_label_ids", [["labelId1"], ["labelId1", "labelId2"], None]
)
@pytest.mark.parametrize(
    "remove_label_ids", [["labelId1"], ["labelId1", "labelId2"], None]
)
def test_modify_message_api_call(
    user_id: str,
    id: str,
    add_label_ids: list[str] | None,
    remove_label_ids: list[str] | None,
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    gmail.modify_message(
        rsc_mock,
        user_id,
        id=id,
        add_label_ids=add_label_ids,
        remove_label_ids=remove_label_ids,
    )
    modify_mock = rsc_mock.users().messages().modify
    modify_mock.assert_called_once_with(
        userId=user_id,
        id=id,
        body=dict(
            addLabelIds=add_label_ids or list(),
            removeLabelIds=remove_label_ids or list(),
        ),
    )
    modify_mock.return_value.execute_assert_called_once_with()


def describe_gmail_mail_system() -> None:
    platforms = [
        mercari.Platform(),
        yahoo_auction.Platform(),
    ]

    @pytest.fixture()
    def mail_system() -> gmail.GmailMailSystem:
        return gmail.GmailMailSystem(
            creds={},
        )

    def test_donelabel_when_donelabel_has_been_created(
        mail_system: gmail.GmailMailSystem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        donelabel = dict(name=mail_system.done_label_name)
        list_label_mock = mocker.patch(
            "crostore.mailsystems.gmail.list_label",
            return_value=[donelabel, dict(name="dummy_label")],
        )
        create_label_mock = mocker.patch(
            "crostore.mailsystems.gmail.create_label", return_value=donelabel
        )
        build_mock = mocker.patch("crostore.mailsystems.gmail.build")
        assert mail_system.get_donelabel() == donelabel
        list_label_mock.assert_called_once_with(
            build_mock.return_value,
            mail_system.user_id,
        )
        create_label_mock.assert_not_called()

    def test_donelabel_when_donelabel_has_not_been_created(
        mail_system: gmail.GmailMailSystem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        donelabel = dict(name=mail_system.done_label_name)
        list_label_mock = mocker.patch(
            "crostore.mailsystems.gmail.list_label",
            return_value=[dict(name="dummy_label")],
        )
        create_label_mock = mocker.patch(
            "crostore.mailsystems.gmail.create_label", return_value=donelabel
        )
        build_mock = mocker.patch("crostore.mailsystems.gmail.build")
        assert mail_system.get_donelabel() == create_label_mock.return_value
        list_label_mock.assert_called_once_with(
            build_mock.return_value,
            mail_system.user_id,
        )
        create_label_mock.assert_called_once_with(
            build_mock.return_value,
            mail_system.user_id,
            label=donelabel,
        )

    @pytest.mark.parametrize("platform", platforms)
    def test_iter_sold_message_ids(
        mail_system: gmail.GmailMailSystem,
        platform: abstract.AbstractPlatform,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        messages = create_messages()
        build_mock = mocker.patch("crostore.mailsystems.gmail.build")
        list_message_mock = mocker.patch(
            "crostore.mailsystems.gmail.list_message",
            return_value=(
                messages,
                "",
                "",
            ),
        )
        modify_message_mock = mocker.patch(
            "crostore.mailsystems.gmail.modify_message",
        )
        donelabel = dict(id="donelabel", name=mail_system.done_label_name)
        get_donelabel_mock = mocker.patch(
            "crostore.mailsystems.gmail.GmailMailSystem.get_donelabel",
            return_value=donelabel,
        )
        for i, message_id in enumerate(mail_system.iter_sold_message_ids(platform)):
            assert message_id == messages[i]["id"]
        list_message_mock.assert_called_once_with(
            build_mock.return_value,
            mail_system.user_id,
            query=gmail.get_sold_mail_query(platform)
            + " AND -{label:"
            + mail_system.done_label_name
            + "}",
        )
        get_donelabel_mock.assert_called_once_with()
        for i, call in enumerate(modify_message_mock.call_args_list):
            assert call == mocker.call(
                build_mock.return_value,
                mail_system.user_id,
                id=messages[i]["id"],
                add_label_ids=[donelabel["id"]],
            )

    @pytest.mark.parametrize("platform", platforms)
    def test_iter_sold_messages(
        mail_system: gmail.GmailMailSystem,
        platform: abstract.AbstractPlatform,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        messages = create_messages()
        build_mock = mocker.patch("crostore.mailsystems.gmail.build")
        iter_sold_message_ids_mock = mocker.patch(
            "crostore.mailsystems.gmail.GmailMailSystem.iter_sold_message_ids",
            return_value=[message["id"] for message in messages],
        )
        get_message_mock = mocker.patch(
            "crostore.mailsystems.gmail.get_message", side_effect=messages
        )
        for i, message in enumerate(mail_system.iter_sold_messages(platform)):
            payload = messages[i]["payload"]
            headers = {header["name"]: header["value"] for header in payload["headers"]}
            assert message == platform.create_message(
                subject=headers.get("subject", ""),
                body=base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8"),
            )
        iter_sold_message_ids_mock.assert_called_once_with(platform)
        for i, call in enumerate(get_message_mock.call_args_list):
            assert call == mocker.call(
                build_mock.return_value,
                mail_system.user_id,
                id=messages[i]["id"],
            )
