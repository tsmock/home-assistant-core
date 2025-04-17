"""Test the Xcel Energy config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.components.xcelenergy.config_flow import CannotConnect, InvalidAuth
from homeassistant.components.xcelenergy.const import CONF_CERTIFICATE, CONF_KEY, DOMAIN
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

TEST_HOST: str = "https://192.168.1.104:8081"
TEST_CERTIFICATE: str = """-----BEGIN CERTIFICATE-----
FIXME: DO NOT COMMIT
-----END CERTIFICATE-----"""
TEST_KEY: str = """-----BEGIN PRIVATE KEY-----
FIXME: DO NOT COMMIT
-----END PRIVATE KEY-----"""


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.xcelenergy.itron_riva_gen5.ItronApi.fetch",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_CERTIFICATE: TEST_CERTIFICATE,
                CONF_KEY: TEST_KEY,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Name of the device"
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_CERTIFICATE: TEST_CERTIFICATE,
        CONF_KEY: TEST_KEY,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.xcelenergy.itron_riva_gen5.ItronApi.fetch",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_CERTIFICATE: TEST_CERTIFICATE,
                CONF_KEY: TEST_KEY,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.
    with patch(
        "homeassistant.components.xcelenergy.itron_riva_gen5.ItronApi.fetch",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_CERTIFICATE: TEST_CERTIFICATE,
                CONF_KEY: TEST_KEY,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Name of the device"
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_CERTIFICATE: TEST_CERTIFICATE,
        CONF_KEY: TEST_KEY,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.xcelenergy.itron_riva_gen5.ItronApi.fetch",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_CERTIFICATE: TEST_CERTIFICATE,
                CONF_KEY: TEST_KEY,
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    # Make sure the config flow tests finish with either an
    # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
    # we can show the config flow is able to recover from an error.

    with patch(
        "homeassistant.components.xcelenergy.itron_riva_gen5.ItronApi.fetch",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_HOST,
                CONF_CERTIFICATE: TEST_CERTIFICATE,
                CONF_KEY: TEST_KEY,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Name of the device"
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_CERTIFICATE: TEST_CERTIFICATE,
        CONF_KEY: TEST_KEY,
    }
    assert len(mock_setup_entry.mock_calls) == 1
