from django.urls import path

from . import consumers

websocket_urlpatterns = [
	path('chat/', consumers.ChatConsumer.as_asgi()),
    path('groupchat/<int:group_id>/', consumers.GroupChatConsumer.as_asgi()),
]