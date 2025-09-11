import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # room_name expected like: chat_1_3
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        parts = self.room_name.split('_')
        if len(parts) != 3 or parts[0] != 'chat':
            await self.close(code=4000)
            return
        try:
            uid1 = int(parts[1]); uid2 = int(parts[2])
        except ValueError:
            await self.close(code=4001)
            return

        user = self.scope.get('user')
        if not user or not user.is_authenticated or user.id not in (uid1, uid2):
            # Not allowed to join this room
            await self.close(code=4003)
            return

        self.other_user_id = uid2 if user.id == uid1 else uid1
        # normalized group name
        a, b = min(uid1, uid2), max(uid1, uid2)
        self.room_group_name = f'chat_{a}_{b}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        message = data.get('message') or data.get('content')
        if not message:
            return

        sender = self.scope['user']
        receiver_id = data.get('receiver_id') or self.other_user_id

        # Save message (sync DB call)
        saved = await self._save_message(sender.id, receiver_id, message)

        # Broadcast to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',          # -> calls chat_message()
                'id': saved['id'],
                'message': saved['message'],
                'sender_id': saved['sender_id'],
                'receiver_id': saved['receiver_id'],
                'timestamp': saved['timestamp'],
            }
        )

    async def chat_message(self, event):
        # Send JSON to websocket client
        await self.send(text_data=json.dumps({
            'id': event['id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'receiver_id': event['receiver_id'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def _save_message(self, sender_id, receiver_id, message_text):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        m = Message.objects.create(sender=sender, receiver=receiver, message=message_text)
        return {
            'id': m.id,
            'message': m.message,
            'sender_id': m.sender.id,
            'receiver_id': m.receiver.id,
            'timestamp': m.timestamp.isoformat(),
        }
