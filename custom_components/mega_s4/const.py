"""Constants for the MEGA S4 integration."""

from collections.abc import Callable
from typing import Final

from homeassistant.util.hass_dict import HassKey

DOMAIN: Final = "mega_s4"

CONF_ACCESS_KEY_ID = "access_key_id"
CONF_SECRET_ACCESS_KEY = "secret_access_key"
CONF_BUCKET = "bucket"
CONF_REGION = "region"
CONF_PREFIX = "prefix"

MEGA_S4_DOMAIN = "s4.mega.io"

# Available MEGA S4 regions
REGIONS: dict[str, str] = {
    "eu-central-1": "Amsterdam (Netherlands)",
    "eu-central-2": "Bettembourg (Luxembourg)",
    "ca-central-1": "Montreal (Canada)",
    "ca-west-1": "Vancouver (Canada)",
}

DEFAULT_REGION = "eu-central-1"


def endpoint_url_for_region(region: str) -> str:
    """Return the S3 endpoint URL for a given MEGA S4 region."""
    return f"https://s3.{region}.{MEGA_S4_DOMAIN}"


DATA_BACKUP_AGENT_LISTENERS: HassKey[list[Callable[[], None]]] = HassKey(
    f"{DOMAIN}.backup_agent_listeners"
)
