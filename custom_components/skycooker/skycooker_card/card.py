"""Обработчик WebSocket и регистрация событий обновления карточки SkyCooker."""

import voluptuous as vol
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.components.websocket_api import decorators, async_register_command


@decorators.websocket_command(
    {
        vol.Required("type"): "skycooker_card_updated",
    }
)
@decorators.async_response
async def handle_subscribe_updates(hass, connection, msg):
    """Обработка подписки на обновления."""

    @callback
    def handle_event(event: str, data: dict = {}):
        """Пересылка событий через websocket."""
        connection.send_message(
            {"id": msg["id"], "type": "event", "event": {"data": data}}
        )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, "skycooker_card_event", handle_event
    )
    connection.send_result(msg["id"])


async def async_register_card(hass):
    """Публикация события в lovelace при изменении карточки."""
    async_register_command(hass, handle_subscribe_updates)