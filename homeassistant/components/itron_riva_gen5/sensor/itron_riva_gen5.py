"""API for the Gen 5 Riva Itron power meters."""

# In my area, Xcel uses Gen 5 Riva Itron meters.
# See https://community.home-assistant.io/t/xcel-energy-itron-gen-5-riva/346943/58 for where the URLs came from.
# This *may* be able to be generified to a generic Itron integration for newer meters, but I don't know.
import asyncio
from datetime import timedelta
import os.path
import re
import ssl
import tempfile
from typing import Union

from defusedxml import ElementTree
import httpx

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HassJob, HassJobType, HomeAssistant

from ..const import LOGGER
from ..exceptions import CannotConnect, InvalidAuth

# The power reading only has the last second, but HA doesn't allow for <5s/update
SCAN_INTERVAL = timedelta(seconds=5)

# Hopefully this doesn't change. If it does,
# echo | openssl s_client -showcerts -servername ${IP} -connect ${IP}:8081 -xkey key.pem -xcert cert.pem -legacy_renegotiation -tls1_2 -cipher 'ALL:@SECLEVEL=0' 2>/dev/null | openssl x509 -inform pem -noout -text
# should get the new certificate
ITRON_CERT = """-----BEGIN CERTIFICATE-----
MIIBlDCCATmgAwIBAgIBATAKBggqhkjOPQQDAjArMQ4wDAYDVQQKDAVJdHJvbjEZ
MBcGA1UEAwwQSUVFRSAyMDMwLjUgUm9vdDAgFw0yMDEwMTYyMTI0NDhaGA85OTk5
MTIzMTIzNTk1OVowKzEOMAwGA1UECgwFSXRyb24xGTAXBgNVBAMMEElFRUUgMjAz
MC41IFJvb3QwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAARpgDgTQhc5zoATkAs9
UWbT9uRau6GEb1R/1iPGLk+HAAOyAu3SkKHTwVGgzUPl73P9KMH9ZD4nSIQ5o2qJ
Mpuuo0wwSjAOBgNVHQ8BAf8EBAMCAQYwFAYDVR0gAQH/BAowCDAGBgRVHSAAMA8G
A1UdEwEB/wQFMAMBAf8wEQYDVR0OBAoECE4E78JKsqrnMAoGCCqGSM49BAMCA0kA
MEYCIQC4QuurwLz8N3Vp8vQJeTrXTSKplgtW3o+GLpUzbwt2awIhAPHKAZEk3d4c
55Ksb/AIXwrGwsrbsD75WmfKX9DjOc60
-----END CERTIFICATE-----"""


class ItronApi:
    """An API instance."""

    def __init__(
        self,
        hass: HomeAssistant | None,
        host: str,
        certificate: str,
        key: str,
        cadata: str = ITRON_CERT,
    ) -> None:
        """Initialize the API.

        Note that you must wait for the certificates to be loaded prior to network calls

        @param hass The home assistant instance to use for async calls
        @param host The host to connect to
        @param certificate The client certificate to use (a path, not the actual cert)
        @param key The client key to use (a path, not the actual key)
        @param cadata The root certificate for the self-signed certificate for the power meter
        """
        self.session: httpx.Client = self._generate_session(
            hass=hass, host=host, certificate=certificate, key=key, cadata=cadata
        )
        self.certs_loaded: bool = False
        self.debug: Union[bool,str] = False

    async def wait_for_session(self) -> None:
        """Wait for the client session to be ready."""
        while not self.certs_loaded:
            await asyncio.sleep(0.5)

    def _generate_session(
        self, hass: HomeAssistant | None, host: str, certificate: str, key: str, cadata: str
    ) -> httpx.Client:
        ctx: ssl.SSLContext = self._setup_context(
            hass=hass, certificate=certificate, key=key, cadata=cadata
        )
        return httpx.Client(verify=ctx, base_url=host)

    def _setup_context(
        self,
        hass: HomeAssistant | None = None,
        certificate: str | None = None,
        key: str | None = None,
        cadata: str = ITRON_CERT,
    ) -> ssl.SSLContext:
        """Set up the SSL context for connecting to the power meter.

        @param certificate The client certificate to use for authentication (a path, not the actual cert)
        @param key The client key to use for authentication (a path, not the actual key)
        @param cadata The root certificate for the self-signed certificate for the power meter
        """
        # Yes, this is deprecated. Can't do anything about it right now.
        temp_context = ssl.SSLContext()#protocol=ssl.PROTOCOL_TLS_CLIENT)
        temp_context.hostname_checks_common_name = False
        temp_context.check_hostname = False
        temp_context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        # Only supports TLS_ECDHE_ECDSA_WITH_AES_128_CCM_8 (ECDHE-ECDSA-AES128-CCM8)
        temp_context.set_ciphers("@SECLEVEL=0:ALL")
        # Unfortunately this is necessary
        temp_context.options |= ssl.Options.OP_LEGACY_SERVER_CONNECT
        # Load the root certificate into memory so we don't have to turn verification off.
        temp_context.load_verify_locations(cadata=cadata)
        if certificate and key:
            if hass:
                hass.async_run_hass_job(
                    HassJob(
                        name="Itron: Load certificates",
                        target=self._load_certs,
                        job_type=HassJobType.Executor,
                    ),
                    temp_context,
                    certificate,
                    key,
                )
            else:
                asyncio.get_event_loop().run_in_executor(
                    None, self._load_certs, temp_context, certificate, key
                )
        return temp_context

    def _load_certs(self, ctx: ssl.SSLContext, certificate: str, key: str) -> None:
        certificate_path: str = ItronApi._check_file(
            certificate, "xcel_client_certificate.pem"
        )
        key_path: str = ItronApi._check_file(key, "xcel_client_key.pem")
        LOGGER.info("Loading certificates")
        ctx.load_cert_chain(certfile=certificate_path, keyfile=key_path)
        self.certs_loaded = True
        LOGGER.info("Certificates loaded")

    @staticmethod
    def _check_file(data: str, file_name: str) -> str:
        # I don't like this, but python does not support in-memory certificates
        # So we need to store the client certificate and key to file. For now, we write them to the /tmp directory.
        # If only so that they are (hopefully) cleaned up on reboot.
        if not os.path.isfile(data) and len(data) > 100:
            # The UI replaces newlines with spaces.
            if data.startswith("-----BEGIN ") and len(data.splitlines()) == 1:
                if (
                    m := re.search("(-----.+?-----)(.+?)(-----.+?-----)", data)
                ) and len(m.groups()) == 3:
                    data = (
                        m.group(1)
                        + os.linesep
                        + os.linesep.join(m.group(2).strip().split())
                        + os.linesep
                        + m.group(3)
                    )
                else:
                    raise InvalidAuth("Invalid certificate")
            data_path = os.path.join(tempfile.gettempdir(), file_name)
            # Minimize writes; if it already exists and has the right data, we're done.
            if os.path.isfile(data_path):
                with open(data_path, encoding="ascii") as cert_file:
                    if data == cert_file.read():
                        return data_path

            with open(data_path, "w", encoding="ascii") as cert_file_w:
                cert_file_w.write(data)
            return data_path
        return data

    def fetch(self, path: str) -> str:
        """Fetch data from the power meter using an appropriate SSL context.

        @param path The path on the host to fetch (GET)
        """
        try:
            response: httpx.Response = self.session.get(path)
        except httpx.ConnectError as e:
            raise CannotConnect from e

        LOGGER.warning(response.text)  # FIXME: Remove
        if not response.is_success:
            LOGGER.warning(response.text)

        if self.debug and type(self.debug) is str:
            with open(os.path.join(self.debug, response.headers['date'] + path.replace('/', '.') + '.xml'), 'w') as debug_file:
                debug_file.write(response.text)
        response.raise_for_status()
        return response.text


class ItronRivaGen5(SensorEntity):
    """Parent class for Itron Riva Gen5 sensors."""

    def __init__(self, api: ItronApi, path: str) -> None:
        """Initialize the sensor.

        @param host The host to connect to
        @param certificate The client certificate to use (a path, not the actual cert)
        @param key The client key to use (a path, not the actual key)
        """
        self.api = api
        self.path = path

    def async_update(self) -> int | None:
        """Update the sensor.

        @return The updated sensor value.
        """
        text = self.api.fetch(self.path)
        et = ElementTree.fromstring(text)
        # There should be one of each of these.
        values = et.findall("./{urn:ieee:std:2030.5:ns}value")
        # duration is almost always 1. Which means that anything using the instant power reading cannot be
        # used to sanity check consumption.
        duration = et.findall(
            "./{urn:ieee:std:2030.5:ns}timePeriod/{urn:ieee:std:2030.5:ns}duration"
        )
        start = et.findall(
            "./{urn:ieee:std:2030.5:ns}timePeriod/{urn:ieee:std:2030.5:ns}start"
        )
        quality_flags = et.findall("./{urn:ieee:std:2030.5:ns}qualityFlags")
        # Sometimes there is a significant jump for consumption using the original scripts. No clue what happens.
        # This is an attempt to figure out what is going on.
        if (
            len(values) == 1
            and len(duration) == 1
            and len(start) == 1
            and len(quality_flags) == 1
        ):
            value: int = int(values[0].text)
            if self._validate(value):
                self._attr_native_value = value
                return value
        else:
            LOGGER.warning(text)  # TODO Might want to raise. I don't know yet.
        return None

    def _validate(self, value: int) -> bool:
        return True


class ItronRivaGen5Power(ItronRivaGen5):
    """Get the current power usage in the past second."""

    _attr_name = "Itron Riva Gen 5 Power Meter"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def __init__(self, api: ItronApi) -> None:
        """Initialize the sensor.

        @param host The host to connect to
        @param certificate The client certificate to use (a path, not the actual cert)
        @param key The client key to use (a path, not the actual key)
        """
        super().__init__(api, "/upt/1/mr/1/r")


class ItronRivaGen5Consumption(ItronRivaGen5):
    """Get the power consumption total."""

    _attr_name = "Itron Riva Gen 5 Power Consumption"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR

    def __init__(self, api: ItronApi) -> None:
        """Initialize the sensor.

        @param host The host to connect to
        @param certificate The client certificate to use (a path, not the actual cert)
        @param key The client key to use (a path, not the actual key)
        """
        super().__init__(api, "/upt/1/mr/3/r")

    def _validate(self, value: int) -> bool:
        # Don't reset power consumption.
        return value > 0


class ItronRivaGen5Production(ItronRivaGen5):
    """Get the power production total."""

    _attr_name = "Itron Riva Gen 5 Power Production"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR

    def __init__(self, api: ItronApi) -> None:
        """Initialize the sensor.

        @param host The host to connect to
        @param certificate The client certificate to use (a path, not the actual cert)
        @param key The client key to use (a path, not the actual key)
        """
        super().__init__(api, "/upt/1/mr/2/r")
