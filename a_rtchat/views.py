from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import ChatMessageCreateForm, NewGroupForm, ChatRoomEditForm
from django.http import Http404, HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.http import require_POST
import json
from django.urls import reverse


@login_required
def chat_view(request, chatroom_name = 'public-chat'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:100]
    form = ChatMessageCreateForm()

    other_user = None

    # if this chatroom is private
    if chat_group.is_private:

        # make sure user is in the chatroom
        if request.user not in chat_group.members.all():
            raise Http404() 
        
        # find the other user
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    if chat_group.groupchat_name:

        # Banned logic for groupchats
        if request.user in chat_group.banned_users.all():
            messages.warning(request, "You have been banned from this group.")
            return redirect('home')  # Redirect to a safe page

        # Add user to groupchat
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, "Please verify your email to join the group chat.")
                return redirect('profile-settings')

    # HTMX specified requests
    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid():
            new_message = form.save(commit=False)  # setting to commit to false to attach author and chatgroup.
            new_message.author = request.user
            new_message.group = chat_group
            new_message.save()
            context = {
                'message':new_message,
                'user':request.user,

            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)
        
    context = {
        'chat_messages':chat_messages,
        'form':form,
        'other_user':other_user,
        'chatroom_name':chatroom_name,
        'chat_group':chat_group
    }    
        
    return render(request, 'a_rtchat/chat.html', context) 

@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    # fetching user object and binding it to other_user
    other_user = User.objects.get(username=username)

    # checking if chatroom exists between the two users already
    my_chatrooms = request.user.chat_groups.filter(is_private = True)
    
    # if private chatroom exists
    if my_chatrooms.exists():
        for chatroom in my_chatrooms:

            # if chatroom exists, bind it to chatroom
            if other_user in chatroom.members.all():
                chatroom = chatroom
                break

            # if chatroom doesn't exist, create it
            else:
                chatroom = ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user,request.user)
    
    # if private chatroom doesn't exist, create it
    else:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(other_user,request.user)

    return redirect('chatroom',chatroom.group_name)

# creating group chat view
@login_required
def create_groupchat(request):
    form = NewGroupForm()

    if request.method == 'POST':
        form = NewGroupForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom',new_groupchat.group_name)



    context = {
        'form':form
    }
    return render(request, 'a_rtchat/create_groupchat.html',context)

# chatroom edit feature for admin
@login_required
def chatroom_edit_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    # if not admin then show error
    if request.user != chat_group.admin:
        raise Http404()
    
    form = ChatRoomEditForm(instance=chat_group)
    
    if request.method == 'POST':
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()

            # defining channel layer first before using 
            channel_layer = get_channel_layer()

            # Ban logic
            ban_members = request.POST.getlist('ban_members')
            for member_id in ban_members:
                member = User.objects.get(id=member_id)
                chat_group.ban_user(member)  # Calls the `ban_user` method in the model 

                # Notify frontend via WebSockets
                async_to_sync(channel_layer.group_send)(
                    chat_group.group_name,
                    {
                        "type": "user_banned",
                        "user_id": member.id,
                    }
                )
            
            # Unban logic 
            unban_members = request.POST.getlist('unban_members')
            for member_id in unban_members:
                member = User.objects.get(id=member_id)
                if member in chat_group.banned_users.all():
                    chat_group.banned_users.remove(member)  # Remove from ban list
                    
                    # Notify frontend via WebSockets
                    async_to_sync(channel_layer.group_send)(
                        chat_group.group_name,
                        {
                            "type": "user_unbanned",
                            "user_id": member.id,
                        }
                    )

            return redirect('chatroom', chatroom_name)
        
    context = {
        'form': form,
        'chat_group': chat_group,
    }
    return render(request, 'a_rtchat/chatroom_edit.html', context)

@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)

    # if not admin then show error
    if request.user != chat_group.admin:
        raise Http404()
    
    if request.method == 'POST':
        chat_group.delete()
        messages.success(request, 'Chatroom deleted successfully')
        return redirect('home')
    return render(request, 'a_rtchat/chatroom_delete.html',{'chat_group':chat_group})

# chatroom leave option
@login_required
def chatroom_leave_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    if request.method == 'POST':

        # removing the user from groupchat who clicked confirm for leaving
        chat_group.members.remove(request.user)
        messages.success(request, 'You have left the chat')
        return redirect('home')
    
    return redirect('chatroom', chatroom_name)

# upload file view
def chat_file_upload(request,chatroom_name):
    chat_group = get_object_or_404(ChatGroup,group_name=chatroom_name)

    # HTMX specified requests
    if request.htmx and request.FILES:

        # uploading the file
        file = request.FILES['file']

        # creating group message
        message = GroupMessage.objects.create(file=file,author=request.user,group=chat_group)


        # retrieve channel layer instance
        channel_layer = get_channel_layer()
        event = {
            'type':'message_handler',
            'message_id':message.id,
        }

        # calling the group_send fucntion to broadcast to everyone in the chat room
        async_to_sync(channel_layer.group_send)(
            chatroom_name,event
        )

        return HttpResponse()
    
@login_required
def mark_seen(request, message_id):
    # Make sure the message belongs to one of the user's chat groups
    message = get_object_or_404(
        GroupMessage,
        id=message_id,
        group__in=request.user.chat_groups.all()
    )
    message.is_seen = True
    message.save()

    # Prepare a response with an HX-Redirect header to redirect to the chatroom
    response = HttpResponse(status=204)
    redirect_url = reverse('chatroom', args=[message.group.group_name])
    response['HX-Redirect'] = redirect_url
    return response