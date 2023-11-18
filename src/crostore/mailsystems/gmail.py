from __future__ import annotations

import base64
import dataclasses
import functools
import logging
import typing as t
from collections import abc

from google.oauth2 import credentials
from googleapiclient import discovery

from crostore import abstract, platforms

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.gmail.v1 import resources, schemas

logger = logging.getLogger(__name__)


@functools.singledispatch
def get_sold_mail_query(platform: abstract.AbstractPlatform) -> str:  # pragma: no cover
    raise ValueError(f"{platform} is not supported")


@get_sold_mail_query.register
def _(platform: platforms.mercari.Platform) -> str:
    return f'from:({platform.email}) AND "購入しました"'


@get_sold_mail_query.register
def _(platform: platforms.yahoo_auction.Platform) -> str:
    return f"from:({platform.email})" + ' AND {subject:("Yahoo!オークション - 終了（落札者あり）")}'


def build(creds: credentials.Credentials) -> resources.GmailResource:
    """
    Constructs a new GmailResource object to request to Gmail API.

    Parameters
    ----------
    creds : google.oauth2.credentials.Credentials
        The credentials for Gmail API.

    Returns
    -------
    GmailResource
        The Resource object for interacting with Gmail API.
    """
    return discovery.build(serviceName="gmail", version="v1", credentials=creds)


def list_label(
    rsc: resources.GmailResource, user_id: str = "me"
) -> list[schemas.Label]:
    """
    Lists all labels in the user's mailbox of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.

    Returns
    -------
    list[Label]
        A list of Label objects.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.labels#Label for Label.

    See also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.labels/list
    """
    response = rsc.users().labels().list(userId=user_id).execute()
    labels = response.get("labels", list())
    return labels


def create_label(
    rsc: resources.GmailResource, user_id: str = "me", *, label: schemas.Label
) -> schemas.Label:
    """
    Creates a new label of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    label : Label
        The label to create.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.labels#Label for Label.

    Returns
    -------
    Label
        The create Label object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.labels#Label for Label.

    See also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.labels/create
    """
    response = (
        rsc.users()
        .labels()
        .create(
            userId=user_id,
            body=label,
        )
        .execute()
    )
    return response


def list_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    query: str = "",
    max_results: int = 100,
    page_token: str | None = None,
    label_ids: list[str] | None = None,
    include_spam_trash: bool = False,
) -> tuple[list[schemas.Message], str, int]:
    """
    Lists the messages in the user's mailbox of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    query : str
        The same query format as that of the Gmail search box.
    max_results : int
        The maximum number of messages to return.
    page_token : str | None
        The page token to retrieve a specific page of results in the list.
    label_ids : list[str] | None
        The list of label IDs of messages to retrieve.
    include_spam_trash : bool
        If true, messages from SPAM and TRASH are included in the results.

    Returns
    -------
    messages : list[Message]
        A list of Message objects.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.
    next_page_token : str
        The token to retrieve the next page.
    result_size_estimate : int
        The estimated total number of results.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list
    """
    response = (
        rsc.users()
        .messages()
        .list(
            userId=user_id,
            q=query,
            maxResults=max_results,
            pageToken=page_token or "",
            labelIds=label_ids or [],
            includeSpamTrash=include_spam_trash,
        )
        .execute()
    )
    return (
        response.get("messages", list()),
        response.get("nextPageToken", ""),
        response.get("resultSizeEstimate", 0),
    )


def get_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    id: str,
    format: t.Literal["minimal", "full", "raw", "metadata"] = "full",
) -> schemas.Message:
    """
    Gets the specified message of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    id : str
        The ID of the message to retrieve.
    format : Literal["minimal", "full", "raw", "metadata"]
        The format to return the message in.
        See also https://developers.google.com/gmail/api/reference/rest/v1/Format.

    Returns
    -------
    Message
        The retrieved Message object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/get
    """
    response = (
        rsc.users().messages().get(userId=user_id, id=id, format=format).execute()
    )
    return response


def modify_message(
    rsc: resources.GmailResource,
    user_id: str = "me",
    *,
    id: str,
    add_label_ids: list[str] | None = None,
    remove_label_ids: list[str] | None = None,
) -> schemas.Message:
    """
    Modifies the labels on the specified message of Gmail.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    user_id : str
        The user's email address.
    id : str
        The ID of the message to retrieve.
    add_label_ids : list[str] | None
        A list of IDs of labels to add to this message.
        You can add up to 100 labels with each update.
    remove_label_ids : list[str] | None
        A list IDs of labels to remove from this message.
        You can remove up to 100 labels with each update.
    Returns
    -------
    Message
        The retrieved Message object.
        See also https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message for Message.

    See Also
    --------
    https://developers.google.com/gmail/api/reference/rest/v1/users.messages/modify
    """
    response = (
        rsc.users()
        .messages()
        .modify(
            userId=user_id,
            id=id,
            body=dict(
                addLabelIds=add_label_ids or list(),
                removeLabelIds=remove_label_ids or list(),
            ),
        )
        .execute()
    )
    return response


@dataclasses.dataclass(frozen=True)
class GmailMailSystem(abstract.AbstractMailSystem):
    creds: credentials.Credentials
    """The credentials for Gmail API."""
    user_id: str = "me"
    """The user's email address used when interacting Gmail API."""
    done_label_name: str = "crostored"
    """The name of the label which will be added to the message handled by Crostore."""

    def get_donelabel(self) -> schemas.Label:
        rsc = build(self.creds)
        labels = list_label(rsc, self.user_id)
        donelabels = [
            label for label in labels if label.get("name", "") == self.done_label_name
        ]
        if len(donelabels) >= 1:
            donelabel = donelabels[0]
        else:
            donelabel = create_label(
                rsc, self.user_id, label=dict(name=self.done_label_name)
            )
        logger.debug(f"Got {donelabel} as a done-label")
        return donelabel

    def iter_sold_message_ids(
        self,
        platform: abstract.AbstractPlatform,
    ) -> abc.Generator[str, None, None]:
        sold_mail_query = get_sold_mail_query(platform)
        rsc = build(self.creds)
        messages, _, _ = list_message(
            rsc,
            self.user_id,
            query=sold_mail_query + " AND -{label:" + self.done_label_name + "}",
        )
        donelabel = self.get_donelabel()
        for message in messages:
            yield message["id"]
            modify_message(
                rsc,
                self.user_id,
                id=message["id"],
                add_label_ids=[donelabel["id"]],
            )
            logger.info(f"Added {donelabel} to {message}")

    def iter_sold_messages(
        self, platform: abstract.AbstractPlatform
    ) -> abc.Generator[abstract.AbstractMessage, None, None]:
        rsc = build(self.creds)
        for sold_message_id in self.iter_sold_message_ids(platform):
            gmail_message = get_message(rsc, self.user_id, id=sold_message_id)
            payload = gmail_message["payload"]
            headers = {header["name"]: header["value"] for header in payload["headers"]}
            try:
                yield platform.create_message(
                    subject=headers.get("subject", ""),
                    body=base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                        "utf-8"
                    ),
                )
            except Exception as err:  # pragma: no cover
                logger.error(f"Cannot deal with {gmail_message}: {err}")
