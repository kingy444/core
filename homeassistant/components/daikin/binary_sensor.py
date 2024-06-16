"""Support for Daikin AC binary sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from pydaikin.daikin_base import Appliance

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN as DAIKIN_DOMAIN, DaikinApi
from .const import ATTR_FILTER_DIRTY


@dataclass(frozen=True, kw_only=True)
class DaikinBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Daikin binary sensor entity."""

    state_func: Callable[[Appliance], bool]


BINARY_SENSOR_TYPES: tuple[DaikinBinarySensorEntityDescription, ...] = (
    DaikinBinarySensorEntityDescription(
        key=ATTR_FILTER_DIRTY,
        translation_key="filter_dirty",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:air-filter",
        state_func=lambda device: bool(device.filter_dirty),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Daikin climate based on config_entry."""
    daikin_api = hass.data[DAIKIN_DOMAIN].get(entry.entry_id)

    binary_sensors = []
    if daikin_api.device.support_filter_dirty:
        binary_sensors.append(ATTR_FILTER_DIRTY)

    entities = [
        DaikinBinarySensor(daikin_api, description)
        for description in BINARY_SENSOR_TYPES
        if description.key in binary_sensors
    ]
    async_add_entities(entities)


class DaikinBinarySensor(BinarySensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True
    entity_description: DaikinBinarySensorEntityDescription

    def __init__(
        self, api: DaikinApi, description: DaikinBinarySensorEntityDescription
    ) -> None:
        """Initialize the binary sensor."""
        self.entity_description = description
        self._attr_device_info = api.device_info
        self._attr_unique_id = f"{api.device.mac}-{description.key}"
        self._api = api

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        return self.entity_description.state_func(self._api.device)

    async def async_update(self) -> None:
        """Retrieve latest state."""
        await self._api.async_update()
