"""Constants for the Xcel Energy integration."""

from logging import Logger, getLogger
from typing import Final

DOMAIN: Final[str] = "xcelenergy"
LOGGER: Final[Logger] = getLogger(__package__)

CONF_CERTIFICATE: Final[str] = "client_certificate"
CONF_KEY: Final[str] = "client_key"
