from .const import DOMAIN, ATTRIBUTION
from homeassistant.const import DEVICE_CLASS_MONETARY, ATTR_ATTRIBUTION
import logging

from datetime import datetime, timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
	"""Setup sensor platform"""

	async def async_update_data():
		#try:
		client = hass.data[DOMAIN]["client"]
		await hass.async_add_executor_job(client.getData)
		#except Exception as e:
		#    raise UpdateFailed(f"Error communicating with server: {e}")

	coordinator = DataUpdateCoordinator(
		hass,
		_LOGGER,
		name = "sensor",
		update_method = async_update_data,
		update_interval = timedelta(minutes = 60)
	)

	# Immediate refresh
	await coordinator.async_request_refresh()

	entities = []
	client = hass.data[DOMAIN]["client"]
	for subscription in client._subscriptions:
		entities.append(SubscriptionSensor(hass, coordinator, subscription))
	async_add_entities(entities)

class SubscriptionSensor(Entity):
	def __init__(self, hass, coordinator, subscription) -> None:
		self._hass = hass
		self._coordinator = coordinator
		self._subscription = subscription

	@property
	def name(self) -> str:
		name = DOMAIN
		if len(self._subscription['Users']) > 1:
			name +=  " " + self._subscription['Name']
		else:
			name +=  " " + str(self._subscription['Users'][0])
		return name

	@property
	def state(self):
		return self._subscription['Balance']

	@property
	def unit_of_measurement(self) -> str:
		return 'kroner'

	@property
	def unique_id(self):
		return DOMAIN + "_" + str(self._subscription['Users'][0])

	@property
	def device_class(self) -> str:
		return DEVICE_CLASS_MONETARY

	@property
	def extra_state_attributes(self):
		attributes = { ATTR_ATTRIBUTION: ATTRIBUTION }
		return attributes

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