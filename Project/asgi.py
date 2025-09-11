# import os
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# import Chat.routing  # <-- make sure your app is named 'chat'

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),  # HTTP requests
#     "websocket": AuthMiddlewareStack(  # WebSocket requests
#         URLRouter(
#             Chat.routing.websocket_urlpatterns
#         )
#     ),
# })

# Project/asgi.py
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

# 1. Tell Django where settings are
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")  # <-- replace with your real settings module

# 2. Create Django ASGI app early so registry is loaded
django_asgi_app = get_asgi_application()

# 3. Define application
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            __import__("Chat.routing").routing.websocket_urlpatterns  # lazy import
        )
    ),
})
