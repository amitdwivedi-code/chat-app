from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime

def notify_user(user_id, message):
    """
    Sends a real-time notification to a specific user via Django Channels.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "send_notification",
            "data": {
                "message": message,
                "timestamp": str(datetime.now())
            }
        }
    )
