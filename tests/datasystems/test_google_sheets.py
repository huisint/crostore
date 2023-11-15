import typing as t

import pytest
import pytest_mock

from crostore import abstract
from crostore.datasystems import google_sheets
from crostore.platforms import mercari, yahoo_auction
from tests import FixtureRequest

if t.TYPE_CHECKING:  # pragma: no cover
    from googleapiclient._apis.sheets.v4 import schemas


def test_build(mocker: pytest_mock.MockerFixture) -> None:
    build_mock = mocker.patch("googleapiclient.discovery.build")
    creds_mock = mocker.Mock()
    rsc = google_sheets.build(creds_mock)
    assert rsc == build_mock.return_value
    build_mock.assert_called_once_with(
        serviceName="sheets",
        version="v4",
        credentials=creds_mock,
    )


@pytest.mark.parametrize("spreadata_systemheet_id", ["sheetId1", "sheetId2"])
@pytest.mark.parametrize("range", ["A1:A5", "Sheet1!A1:A5"])
@pytest.mark.parametrize("values", [[]])
@pytest.mark.parametrize("major_dimension", ["ROWS", "COLUMNS"])
def test_get_values_returns(
    spreadata_systemheet_id: str,
    range: str,
    values: list[list[t.Any]],
    major_dimension: t.Literal["ROWS", "COLUMNS"],
    mocker: pytest_mock.MockerFixture,
) -> None:
    response: schemas.ValueRange = dict(
        range=range,
        majorDimension=major_dimension,
        values=values,
    )
    rsc_mock = mocker.Mock()
    get_mock = rsc_mock.spreadsheets().values().get
    get_mock.return_value.execute.return_value = response
    result = google_sheets.get_values(
        rsc_mock, spreadata_systemheet_id, range=range, major_dimension=major_dimension
    )
    assert result[0] == response.get("range", "")
    assert result[1] == response.get("majorDimension", "DIMENSION_UNSPECIFIED")
    assert result[2] == response.get("values", [[]])


@pytest.mark.parametrize("spreadata_systemheet_id", ["sheetId1", "sheetId2"])
@pytest.mark.parametrize("range", ["A1:A5", "Sheet1!A1:A5"])
@pytest.mark.parametrize("major_dimension", ["ROWS", "COLUMNS"])
@pytest.mark.parametrize(
    "value_render_option", ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"]
)
@pytest.mark.parametrize(
    "datetime_render_option", ["SERIAL_NUMBER", "FORMATTED_STRING"]
)
def test_get_values_api_call(
    spreadata_systemheet_id: str,
    range: str,
    major_dimension: t.Literal["ROWS", "COLUMNS"],
    value_render_option: t.Literal["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
    datetime_render_option: t.Literal["SERIAL_NUMBER", "FORMATTED_STRING"],
    mocker: pytest_mock.MockerFixture,
) -> None:
    rsc_mock = mocker.Mock()
    google_sheets.get_values(
        rsc_mock,
        spreadata_systemheet_id,
        range=range,
        major_dimension=major_dimension,
        value_render_option=value_render_option,
        datetime_render_option=datetime_render_option,
    )
    get_mock = rsc_mock.spreadsheets().values().get
    get_mock.assert_called_once_with(
        spreadsheetId=spreadata_systemheet_id,
        range=range,
        majorDimension=major_dimension,
        valueRenderOption=value_render_option,
        dateTimeRenderOption=datetime_render_option,
    )
    get_mock.return_value.execute.assert_called_once_with()


def describe_google_sheets_data_system() -> None:
    crostore_id = [f"c{i:05}" for i in range(10)]
    platform_to_column = {
        mercari.Platform(): "B",
        yahoo_auction.Platform(): "C",
    }

    @pytest.fixture(params=["sheetId1", "sheetId2"])
    def sheet_id(request: FixtureRequest[str]) -> str:
        return request.param

    @pytest.fixture(params=["Sheet1", "Sheet2"])
    def sheet_name(request: FixtureRequest[str]) -> str:
        return request.param

    @pytest.fixture()
    def data_system(
        sheet_id: str, sheet_name: str
    ) -> google_sheets.GoogleSheetsDataSystem:
        return google_sheets.GoogleSheetsDataSystem(
            creds={},
            sheet_id=sheet_id,
            platform_to_column=platform_to_column,
            sheet_name=sheet_name,
        )

    @pytest.mark.parametrize("column", "ABC")
    def test_get_column_values(
        data_system: google_sheets.GoogleSheetsDataSystem,
        column: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        response = {
            "range": f"{data_system.sheet_name}!{column}:{column}",
            "majorDimension": "COLUMNS",
            "values": [[f"{column}001", f"{column}002", f"{column}003"]],
        }
        get_values_mock = mocker.patch(
            "crostore.datasystems.google_sheets.get_values",
            return_value=(
                response["range"],
                response["majorDimension"],
                response["values"],
            ),
        )
        build_mock = mocker.patch("crostore.datasystems.google_sheets.build")
        values = data_system.get_column_values(column)
        assert values == response.get("values", [[]])[0]
        get_values_mock.assert_called_once_with(
            build_mock.return_value,
            data_system.sheet_id,
            range=f"{data_system.sheet_name}!{column}:{column}",
            major_dimension="COLUMNS",
        )

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}{i:03}", crostore_id=crostore_id[i])
            for platform, column in platform_to_column.items()
            for i in range(4)
        ],
    )
    def test_iter_related_items(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        def get_column_values(
            _: google_sheets.GoogleSheetsDataSystem, column: str
        ) -> list[str]:
            if column == data_system.crostore_id_column:
                return crostore_id
            return [f"{column}{i:03}" for i in range(3)]

        mocker.patch(
            "crostore.datasystems.google_sheets.GoogleSheetsDataSystem.get_column_values",
            get_column_values,
        )
        for related_item in data_system.iter_related_items(item):
            assert related_item.platform != item.platform
            assert related_item.crostore_id == item.crostore_id

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}{i:03}", crostore_id=crostore_id[i])
            for platform, column in platform_to_column.items()
            for i in range(3)
        ],
    )
    def test_update(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.GoogleSheetsDataSystem.get_column_values",
            return_value=crostore_id,
        )
        build_mock = mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        data_system.update(item)
        item_index = crostore_id.index(item.crostore_id)
        update_range = f"{data_system.sheet_name}!{data_system.platform_to_column[item.platform]}{item_index + 1}"
        update_mock = build_mock.return_value.spreadsheets().values().update
        update_mock.assert_called_once_with(
            spreadsheetId=data_system.sheet_id,
            range=update_range,
            body=dict(
                range=update_range, majorDimension="COLUMNS", values=[[item.item_id]]
            ),
            valueInputOption="USER_ENTERED",
        )
        update_mock.return_value.execute.assert_called_once_with()

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}000", crostore_id="")
            for platform, column in platform_to_column.items()
        ],
    )
    def test_update_crostore_id_is_empty(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        with pytest.raises(ValueError):
            data_system.update(item)

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}000", crostore_id="c00001")
            for platform, column in platform_to_column.items()
        ],
    )
    def test_update_crostore_id_is_not_on_sheet(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.GoogleSheetsDataSystem.get_column_values",
            return_value=[],
        )
        mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        with pytest.raises(ValueError):
            data_system.update(item)

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}{i:03}", crostore_id=crostore_id[i])
            for platform, column in platform_to_column.items()
            for i in range(3)
        ],
    )
    def test_delete(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.GoogleSheetsDataSystem.get_column_values",
            return_value=crostore_id,
        )
        build_mock = mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        data_system.delete(item)
        item_index = crostore_id.index(item.crostore_id)
        delete_range = f"{data_system.sheet_name}!{data_system.platform_to_column[item.platform]}{item_index + 1}"
        clear_mock = build_mock.return_value.spreadsheets().values().clear
        clear_mock.assert_called_once_with(
            spreadsheetId=data_system.sheet_id,
            range=delete_range,
            body=dict(),
        )
        clear_mock.return_value.execute.assert_called_once_with()

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}000", crostore_id="")
            for platform, column in platform_to_column.items()
        ],
    )
    def test_delete_crostore_id_is_empty(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        with pytest.raises(ValueError):
            data_system.delete(item)

    @pytest.mark.parametrize(
        "item",
        [
            platform.create_item(item_id=f"{column}000", crostore_id="c00001")
            for platform, column in platform_to_column.items()
        ],
    )
    def test_delete_crostore_id_is_not_on_sheet(
        data_system: google_sheets.GoogleSheetsDataSystem,
        item: abstract.AbstractItem,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            "crostore.datasystems.google_sheets.GoogleSheetsDataSystem.get_column_values",
            return_value=[],
        )
        mocker.patch(
            "crostore.datasystems.google_sheets.build",
        )
        with pytest.raises(ValueError):
            data_system.delete(item)
