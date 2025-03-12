from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from .models import ChatGroup, GroupMessage, User
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
import json

class ChatRoomConsumer(WebsocketConsumer):

    # Connect to WebSocket
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name=self.chatroom_name)

        # Implementing the channel layer communication system and making it asynchronous
        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )

        # To add and update online users
        if self.user not in self.chatroom.user_online.all():
            self.chatroom.user_online.add(self.user)
            self.update_online_count()

        self.accept()

    # Disconnect from WebSocket (to remove channel from chat room)
    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )

        # remove and update online users
        if self.user in self.chatroom.user_online.all():
            self.chatroom.user_online.remove(self.user)
            self.update_online_count()

    # Recieve message from WebSocket
    def receive(self,text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json.get('body','').strip()  # Trim whitespace

        # Prevent sending empty messages
        if not body:
            return  
        
        # Create message object and attach author and chatroom
        message = GroupMessage.objects.create(
            body=body,
            author=self.user,
            group=self.chatroom
        )

        event = {
            'type': 'message_handler',
            'message_id': message.id
        }

        # calling the group_send fucntion to broadcast to everyone in the chat room
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    # in order to send the htmx partial we create an event and an event handler

    def message_handler(self, event):

        message_id = event['message_id']
        message = GroupMessage.objects.get(id=message_id) # grabbing a message using message_id from event dict

        # Defining context for render_to_string
        context = {
            'message': message,
            'user': self.user,
            'chat_group': self.chatroom
        }

        html = render_to_string('a_rtchat/partials/chat_message_p.html', context = context)

        # Calling send function to send data back to frontend in form of html partial
        self.send(text_data=html)

        # Trigger notifications update for all other users in the chat.
        # For a group chat, iterate over members (excluding the sender).
        for member in self.chatroom.members.exclude(id=message.author.id):
            async_to_sync(self.channel_layer.group_send)(
                f'notifications_{member.id}',
                {'type': 'notification_handler'}
            )

    # To update the online count
    def update_online_count(self):
        online_count = self.chatroom.user_online.count() - 1

        event = {
            'type': 'online_count_handler',
            'online_count':online_count
        }
        
        async_to_sync(self.channel_layer.group_send)(self.chatroom_name,event)

    # Defining the event handler
    def online_count_handler(self,event):
        online_count = event['online_count']

        users = User.objects.all()

        chat_messages = ChatGroup.objects.get(group_name=self.chatroom_name).chat_messages.all()[:50]
        author_ids = set([message.author.id for message in chat_messages])

        # users list of those ids
        users = User.objects.filter(id__in=author_ids)

        context = {
            'online_count':online_count,
            'chat_group':self.chatroom,
            'users':users,
        }

        # Creating html partial
        html = render_to_string('a_rtchat/partials/online_count.html', context)

        # Calling send function to send data back to frontend in form of html partial
        self.send(text_data=html)


    # Ban user handler
    def user_banned(self, event):
        user_id = event["user_id"]
        if self.user.id == user_id:
            self.send(text_data=json.dumps({
                "action": "user_banned"
            }))
            self.close()  # Forcefully disconnect banned user

    # Unban user handler
    def user_unbanned(self, event):
        user_id = event["user_id"]
        if self.user.id == user_id:
            self.send(text_data=json.dumps({
                "action": "user_unbanned"
            }))

class OnlineStatusConsumer(WebsocketConsumer):

    def connect(self):
        # retrieving the user info
        self.user = self.scope['user']
        self.group_name = 'online-status'
        self.group = get_object_or_404(ChatGroup, group_name=self.group_name)

        # if user not present in database
        if self.user not in self.group.user_online.all():
            # add to user_online property
            self.group.user_online.add(self.user)

        # add user channel to channel layer group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )

        self.accept()
        self.online_status()

    
    def disconnect(self, close_code):

        # if user is present in user_online property
        if self.user in self.group.user_online.all():
            self.group.user_online.remove(self.user)

        # discard user channel from channel layer group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        self.online_status()

    def online_status(self):

        # the online_status_handler will render htmx partial for each user
        event = {
            'type': 'online_status_handler',  
        }

        async_to_sync(self.channel_layer.group_send)(
            self.group_name, event
        )

    def online_status_handler(self, event):

        # exclude current user and show other online users
        online_users = self.group.user_online.exclude(id=self.user.id)

        # to show online status in the header for public chats
        public_chat_users = ChatGroup.objects.get(group_name='public-chat').user_online.exclude(id=self.user.id)

        # online status for private chats logic
        my_chats = self.user.chat_groups.all()

        # using list comprehension to get all private chats with other users
        private_chats_with_users = [chat for chat in my_chats.filter(is_private=True) if chat.user_online.exclude(id=self.user.id)]
        group_chats_with_users = [chat for chat in my_chats.filter(groupchat_name__isnull=False) if chat.user_online.exclude(id=self.user.id)]

        if public_chat_users or private_chats_with_users or group_chats_with_users:
            online_in_chats = True
        else:
            online_in_chats = False
        
        context = {
            'online_users': online_users,
            'online_in_chats':online_in_chats,
            'public_chat_users':public_chat_users,
            'user':self.user,
        }

        # create html partial and return with send function
        html = render_to_string('a_rtchat/partials/online_status.html', context)
        self.send(text_data=html)

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        # Create a notifications group unique for each user.
        self.group_name = f'notifications_{self.user.id}'

        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
        self.accept()
        # Optionally, send initial notifications state
        self.send_notifications_update()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        
    def notification_handler(self, event):
        # Called when a notification update is triggered.
        self.send_notifications_update()

    def send_notifications_update(self):
        # Query for unread notifications or messages.
        # For this example, we assume unread messages are those with is_seen=False.
        unread_messages = GroupMessage.objects.filter(is_seen=False,group__in=self.user.chat_groups.all()).exclude(group__group_name='public-chat').exclude(author=self.user)

        # Create context for partial.
        context = {
            'unread_messages': unread_messages,
            'user': self.user,
        }
        # Render the notifications dropdown partial.
        html = render_to_string('a_rtchat/partials/notifications.html', context)
        self.send(text_data=html)