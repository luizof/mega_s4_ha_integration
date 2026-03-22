"""The MEGA S4 Object Storage integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import cast

from aiobotocore.client import AioBaseClient as S3Client
from aiobotocore.session import AioSession
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, ConnectionError, ParamValidationError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady

from .const import (
    CONF_ACCESS_KEY_ID,
    CONF_BUCKET,
    CONF_REGION,
    CONF_SECRET_ACCESS_KEY,
    DATA_BACKUP_AGENT_LISTENERS,
    DEFAULT_REGION,
    DOMAIN,
    endpoint_url_for_region,
)

_LOGGER = logging.getLogger(__name__)

type MegaS4ConfigEntry = ConfigEntry[MegaS4RuntimeData]


@dataclass
class MegaS4RuntimeData:
    """Runtime data for the MEGA S4 integration."""

    client: S3Client
    bucket: str
    region: str


async def async_setup_entry(hass: HomeAssistant, entry: MegaS4ConfigEntry) -> bool:
    """Set up MEGA S4 from a config entry."""
    data = cast(dict, entry.data)
    region = data.get(CONF_REGION, DEFAULT_REGION)
    endpoint_url = endpoint_url_for_region(region)

    try:
        session = AioSession()
        boto_config = BotoConfig(
            s3={"addressing_style": "path"},
            signature_version="s3v4",
        )
        # pylint: disable-next=unnecessary-dunder-call
        client = await session.create_client(
            "s3",
            endpoint_url=endpoint_url,
            aws_secret_access_key=data[CONF_SECRET_ACCESS_KEY],
            aws_access_key_id=data[CONF_ACCESS_KEY_ID],
            region_name=region,
            config=boto_config,
        ).__aenter__()
        await client.head_bucket(Bucket=data[CONF_BUCKET])
    except ClientError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="invalid_credentials",
        ) from err
    except ParamValidationError as err:
        if "Invalid bucket name" in str(err):
            raise ConfigEntryError(
                translation_domain=DOMAIN,
                translation_key="invalid_bucket_name",
            ) from err
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="unknown",
        ) from err
    except (ValueError, ConnectionError) as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
        ) from err

    entry.runtime_data = MegaS4RuntimeData(
        client=client,
        bucket=data[CONF_BUCKET],
        region=region,
    )

    def notify_backup_listeners() -> None:
        for listener in hass.data.get(DATA_BACKUP_AGENT_LISTENERS, []):
            listener()

    entry.async_on_unload(entry.async_on_state_change(notify_backup_listeners))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MegaS4ConfigEntry) -> bool:
    """Unload a config entry."""
    runtime_data = entry.runtime_data
    await runtime_data.client.__aexit__(None, None, None)
    return True
