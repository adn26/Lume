from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import shortuuid # create chats dynamically using shortuuid
import os
from PIL import Image

# chat groups
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True,blank=True) # for single users
    groupchat_name = models.CharField(max_length=128, null=True, blank=True) # for groupchats
    banned_users = models.ManyToManyField(User, related_name="banned_from_groups", blank=True)

    # admin
    admin = models.ForeignKey(User, related_name='groupchats', blank=True,null=True, on_delete=models.SET_NULL)

    user_online = models.ManyToManyField(User,related_name='online_in_groups', blank=True) # how many users online
    members = models.ManyToManyField(User,related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.group_name
    
    
    def save(self,*args,**kwargs):
        # no group name
        if not self.group_name:

            # then create group name using shortuuid
            self.group_name =  shortuuid.uuid()
        super().save(*args,**kwargs) # Overrides save method

    
    def ban_user(self, user):
        # Remove user from members and add to banned list.
        self.members.remove(user)
        self.banned_users.add(user)
    
# chat messages
class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300,blank=True,null=True)
    file = models.FileField(upload_to='files/', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    # get only file name
    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        else:
            return None


    def __str__(self):
        if self.body:
            return f"{self.author.username} : {self.body}"
        elif self.file:
            return f"{self.author.username} : {self.filename}"
        return f"{self.author.username} : (empty message)"
    
    def clean(self):
        if not (self.body and self.body.strip()) and not self.file:
            raise ValidationError("You cannot send an empty message.")

    def save(self, *args, **kwargs):
        self.full_clean()  # This will call the clean() method
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-created']


    # Checks if the uploaded file is an image
    @property
    def is_image(self):
        try:
            image = Image.open(self.file) # open image
            image.verify()  # verify the image
            return True
        
        # if the file is not an image
        except:
            return False
        
