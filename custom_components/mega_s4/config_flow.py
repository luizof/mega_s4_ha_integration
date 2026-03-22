"""Config flow for the MEGA S4 integration."""

from __future__ import annotations

from typing import Any

from aiobotocore.session import AioSession
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, ConnectionError, ParamValidationError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_ACCESS_KEY_ID,
    CONF_BUCKET,
    CONF_PREFIX,
    CONF_REGION,
    CONF_SECRET_ACCESS_KEY,
    DEFAULT_REGION,
    DOMAIN,
    REGIONS,
    endpoint_url_for_region,
)

REGION_OPTIONS = [
    {"value": code, "label": f"{label} ({code})"}
    for code, label in REGIONS.items()
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCESS_KEY_ID): cv.string,
        vol.Required(CONF_SECRET_ACCESS_KEY): TextSelector(
            config=TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_BUCKET): cv.string,
        vol.Required(CONF_REGION, default=DEFAULT_REGION): SelectSelector(
            config=SelectSelectorConfig(
                options=REGION_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(CONF_PREFIX, default=""): cv.string,
    }
)


class MegaS4ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MEGA S4."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_prefix = user_input.get(CONF_PREFIX, "").strip("/")
            region = user_input[CONF_REGION]

            # Check for existing entries with same bucket + region + prefix
            for entry in self._async_current_entries(include_ignore=False):
                entry_prefix = (entry.data.get(CONF_PREFIX) or "").strip("/")
                if (
                    entry.data.get(CONF_BUCKET) == user_input[CONF_BUCKET]
                    and entry.data.get(CONF_REGION) == region
                    and entry_prefix == normalized_prefix
                ):
                    return self.async_abort(reason="already_configured")

            if region not in REGIONS:
                errors[CONF_REGION] = "invalid_region"
            else:
                endpoint_url = endpoint_url_for_region(region)
                try:
                    session = AioSession()
                    boto_config = BotoConfig(
                        s3={"addressing_style": "path"},
                        signature_version="s3v4",
                    )
                    async with session.create_client(
                        "s3",
                        endpoint_url=endpoint_url,
                        aws_secret_access_key=user_input[CONF_SECRET_ACCESS_KEY],
                        aws_access_key_id=user_input[CONF_ACCESS_KEY_ID],
                        region_name=region,
                        config=boto_config,
                    ) as client:
                        await client.head_bucket(Bucket=user_input[CONF_BUCKET])
                except ClientError:
                    errors["base"] = "invalid_credentials"
                except ParamValidationError as err:
                    if "Invalid bucket name" in str(err):
                        errors[CONF_BUCKET] = "invalid_bucket_name"
                    else:
                        errors["base"] = "unknown"
                except ValueError:
                    errors["base"] = "cannot_connect"
                except ConnectionError:
                    errors["base"] = "cannot_connect"
                except Exception:  # noqa: BLE001
                    errors["base"] = "unknown"
                else:
                    data = dict(user_input)
                    if not normalized_prefix:
                        data.pop(CONF_PREFIX, None)
                    else:
                        data[CONF_PREFIX] = normalized_prefix

                    title = f"MEGA S4 - {user_input[CONF_BUCKET]}"
                    if normalized_prefix:
                        title = f"{title}/{normalized_prefix}"

                    return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )
