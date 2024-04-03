from __future__ import annotations

import dataclasses
import logging
import typing as t
from collections import abc

from google.oauth2 import credentials
from googleapiclient import discovery

from crostore import abstract

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.sheets.v4 import resources

logger = logging.getLogger(__name__)


def build(creds: credentials.Credentials) -> resources.SheetsResource:
    """
    Constructs a new GmailResource object to request to Gmail API.

    Parameters
    ----------
    creds : google.oauth2.credentials.Credentials
        The credentials for Gmail API.

    Returns
    -------
    SheetsResource
        The Resource object for interacting with Goole Sheets API.
    """
    return discovery.build(serviceName="sheets", version="v4", credentials=creds)


def get_values(
    rsc: resources.SheetsResource,
    spreadsheet_id: str,
    *,
    range: str,
    major_dimension: t.Literal["ROWS", "COLUMNS"],
    value_render_option: t.Literal[
        "FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"
    ] = "FORMATTED_VALUE",
    datetime_render_option: t.Literal[
        "SERIAL_NUMBER", "FORMATTED_STRING"
    ] = "SERIAL_NUMBER",
) -> tuple[str, str, list[list[t.Any]]]:
    """
    Returns a range of values from a spreadsheet.

    Parameters
    ----------
    rsc : GmailResource
        The Resource object for interacting with Gmail API.
    spreadsheet_id : str
        The ID of the spreadsheet to retrieve data from.
    range : str
        The A1 notation or R1C1 notation of the range to retrieve values from.
    major_dimension : Literal["ROWS", "COLUMNS"]
        The major dimension that results should use.
    value_render_option : Literal["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
        How values should be represented in the output.
    datetime_render_option : Literal["SERIAL_NUMBER", "FORMATTED_STRING"]
        How dates, times, and durations should be represented in the output.
        This is ignored if valueRenderOption is FORMATTED_VALUE.

    Returns
    -------
    range : str
        The range the values cover, in A1 notation.
    major_dimension : str
        The major dimension of the values.
    values : list[list[Any]]
        The data that was read or to be written.

    See Also
    --------
    https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/get
    """
    response = (
        rsc.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range,
            majorDimension=major_dimension,
            valueRenderOption=value_render_option,
            dateTimeRenderOption=datetime_render_option,
        )
        .execute()
    )
    return (
        response.get("range", ""),
        response.get("majorDimension", "DIMENSION_UNSPECIFIED"),
        response.get("values", [[]]),
    )


@dataclasses.dataclass(frozen=True)
class GoogleSheetsDataSystem(abstract.AbstractDataSystem):
    creds: credentials.Credentials
    """The credentials for Google Sheets API."""
    sheet_id: str
    """The spreadsheet id."""
    platform_to_column: dict[abstract.AbstractPlatform, str]
    """The dictionary that identifies which column has the data of the platform."""
    sheet_name: str = ""
    """The name of the sheet that has data."""
    crostore_id_column = "A"
    """The column number of Crostore ID in Google Sheets."""

    def get_column_values(self, column: str) -> list[t.Any]:
        rsc = build(self.creds)
        _, _, values = get_values(
            rsc,
            self.sheet_id,
            range=f"{self.sheet_name}!{column}:{column}",
            major_dimension="COLUMNS",
        )
        return list(values[0])

    def iter_related_items(
        self, item: abstract.AbstractItem
    ) -> abc.Generator[abstract.AbstractItem, None, None]:
        if item.platform not in self.platform_to_column:  # pragma: no cover
            raise ValueError(f"{item.platform} is not supported.")
        crostre_id = self.get_column_values(self.crostore_id_column)
        data = {
            platform: self.get_column_values(column)
            for platform, column in self.platform_to_column.items()
        }
        try:
            item_index = data[item.platform].index(item.item_id)
        except ValueError:
            logger.warning(f"{item} is not registered")
            return
        for platform in filter(
            lambda p: p != item.platform, self.platform_to_column.keys()
        ):
            yield platform.create_item(
                item_id=data[platform][item_index],
                crostore_id=crostre_id[item_index],
            )

    def update(self, item: abstract.AbstractItem) -> None:
        if not item.crostore_id:
            raise ValueError(f"crostore_id is empty in item: {item}")
        try:
            item_index = self.get_column_values(self.crostore_id_column).index(
                item.crostore_id
            )
        except ValueError:
            raise ValueError(
                f"{item.crostore_id} was not found in column {self.crostore_id_column}"
            )

        rsc = build(self.creds)
        update_range = (
            f"{self.sheet_name}!"
            f"{self.platform_to_column[item.platform]}{item_index + 1}"
        )
        rsc.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=update_range,
            body=dict(
                range=update_range, majorDimension="COLUMNS", values=[[item.item_id]]
            ),
            valueInputOption="USER_ENTERED",
        ).execute()

    def delete(self, item: abstract.AbstractItem) -> None:
        if not item.crostore_id:
            raise ValueError(f"crostore_id is empty in item: {item}")
        try:
            item_index = self.get_column_values(self.crostore_id_column).index(
                item.crostore_id
            )
        except ValueError:
            raise ValueError(
                f"{item.crostore_id} was not found in column {self.crostore_id_column}"
            )

        rsc = build(self.creds)
        delete_range = (
            f"{self.sheet_name}!"
            f"{self.platform_to_column[item.platform]}{item_index + 1}"
        )
        rsc.spreadsheets().values().clear(
            spreadsheetId=self.sheet_id,
            range=delete_range,
            body=dict(),
        ).execute()
