import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger('django')


class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        """
        Connect a client to the backend via a websocket.

        This method runs when a connection is requested from the front end.
        """
        # Use the game id to create a dynamic channel layer group.
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.game_group_name = f'game_{self.game_id}'

        self.player_id = self.scope['cookies']['hearts_player_id']
        self.player_group_name = f'game_{self.game_id}_player_{self.player_id}'

        # Add this connection to the channel layer groups.
        # Game specific group.
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name,
        )
        # Player specific group.
        await self.channel_layer.group_add(
            self.player_group_name,
            self.channel_name,
        )

        await self.accept()

    async def disconnect(self, close_code):
        """
        Disconnect a client's websocket.

        This is just a callback and is not necessary to handle. Use for any
        kind of clean up.
        """
        # Remove connection from groups.
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name,
        )
        await self.channel_layer.group_discard(
            self.player_group_name,
            self.channel_name,
        )

    async def receive(self, text_data: str, **kwargs) -> None:
        """
        Handle an incoming websocket message from the client.

        We aren't using this right now. We will use this to handle any game
        interactions in the future.
        """
        text_data_json = json.loads(text_data)
        logger.info(f'Received websocket event: {text_data_json=}')

    async def send_payload(self, event: dict) -> None:
        """
        Send a payload to all connections.

        This method is currently used to send the game state to the front end.
        """
        await self.send(text_data=json.dumps(event))
