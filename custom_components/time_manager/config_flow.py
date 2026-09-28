"""Config Flow für den Zeitmanager."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_LANGUAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    SUPPORTED_LANGUAGES,
)


def _schema(values: dict):
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_LANGUAGE,
                default=values.get(CONF_LANGUAGE, DEFAULT_LANGUAGE),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SUPPORTED_LANGUAGES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="language",
                )
            ),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=300,
                    step=5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
        }
    )


class TimeManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id("time_manager_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, DEFAULT_NAME),
                data=user_input,
            )

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    def async_get_options_flow(config_entry):
        return TimeManagerOptionsFlow(config_entry)


class TimeManagerOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        current = dict(self.config_entry.data)
        current.update(self.config_entry.options)

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=_schema(current))
