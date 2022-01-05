import logging

from .const import (
	DOMAIN,
	UPDATE_INTERVAL,
	HA_ATTRIBUTION,
	HA_PHONENUMBER,
	HA_SPACE,
	HA_UNIT_OF_MEASUREMENT_SUBSCRIPTION,
	HA_USED,
	HA_USERNAME,
	HA_USERS,
	R_BALANCE,
	R_PHONENUMBER,
	R_USERNAME,
	STR_NAME,
	STR_PACKAGE,
	STR_USERS,
	STR_USED,
)
from homeassistant.const import DEVICE_CLASS_MONETARY, ATTR_ATTRIBUTION

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info = None):
	"""Setup sensor platform"""

	async def async_update_data():
		# try:
		client = hass.data[DOMAIN]["client"]
		await hass.async_add_executor_job(client.getData)
		# except Exception as e:
		# 	raise UpdateFailed(f"Error communicating with server: {e}")

	coordinator = DataUpdateCoordinator(
		hass,
		_LOGGER,
		name = "sensor",
		update_method = async_update_data,
		update_interval = timedelta(minutes = UPDATE_INTERVAL)
	)

	# Immediate refresh
	await coordinator.async_request_refresh()

	entities = []
	client = hass.data[DOMAIN]["client"]
	for subscription in client._subscriptions:
		entities.append(SubscriptionSensor(hass, coordinator, subscription))
	async_add_entities(entities)

class SubscriptionSensor(SensorEntity):
	def __init__(self, hass, coordinator, subscription) -> None:
		self._hass = hass
		self._coordinator = coordinator
		self._subscription = subscription
		self._client = hass.data[DOMAIN]["client"]

	@property
	def name(self) -> str:
		name = DOMAIN
		if len(self._subscription[STR_USERS]) > 1:
			name +=  HA_SPACE + self._subscription[STR_NAME]
		else:
			name = str(self._subscription[STR_USERS][0][R_PHONENUMBER])

		return name

	@property
	def state(self):
		return self._subscription[R_BALANCE]

	@property
	def unit_of_measurement(self) -> str:
		return HA_UNIT_OF_MEASUREMENT_SUBSCRIPTION

	@property
	def unique_id(self):
		return DOMAIN + "_" + str(self._subscription[STR_USERS][0])

	@property
	def device_class(self) -> str:
		return DEVICE_CLASS_MONETARY

	@property
	def extra_state_attributes(self):
		# Prepare a dictionary with attributes
		attr = { ATTR_ATTRIBUTION: HA_ATTRIBUTION, HA_USERS: [] }

		# Extract Username, Phonenumber and Consumption from the subscription
		for user in self._subscription[STR_USERS]:
			phoneNo = user[R_PHONENUMBER]
			attr[HA_USERS].append( { HA_USERNAME: user[R_USERNAME], HA_PHONENUMBER: phoneNo} )
			for key in self._client._packageAndConsumption[phoneNo][STR_USED]:
				newKey = key + HA_SPACE + HA_USED
				if newKey not in attr:
					attr[newKey] = 0
				attr[newKey] += self._client._packageAndConsumption[phoneNo][STR_USED][key]

		# Extract Package info from the first User
		phoneNo = self._subscription[STR_USERS][0][R_PHONENUMBER]
		for key in self._client._packageAndConsumption[phoneNo][STR_PACKAGE]:
			attr[key] = self._client._packageAndConsumption[phoneNo][STR_PACKAGE][key]

		return attr

	@property
	def should_poll(self):
		"""No need to poll. Coordinator notifies entity of updates."""
		return False

	@property
	def available(self):
		"""Return if entity is available."""
		return self._coordinator.last_update_success

	async def async_update(self):
		"""Update the entity. Only used by the generic entity update service."""
		await self._coordinator.async_request_refresh()

	async def async_added_to_hass(self):
		"""When entity is added to hass."""
		self.async_on_remove(
			self._coordinator.async_add_listener(
				self.async_write_ha_state
			)
		)