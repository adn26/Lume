from django.forms import ModelForm
from django import forms
from .models import *
from django.core.exceptions import ValidationError

# Chat Messages
class ChatMessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Add message ...', 
                'autocomplete': 'off',  # Prevents autofill suggestions and adding other attributes to make it look more like a chat input field.
                'autocorrect': 'off',
                'autocapitalize': 'off',
                'spellcheck': 'false',
                'class':'p-4 text black',
                'maxlength':'300', 'autofocus': True}),
        }
    def clean(self):
        cleaned_data = super().clean()
        body = cleaned_data.get('body')
        file = cleaned_data.get('file')
        if not body and not file:
            raise ValidationError("You cannot send an empty message.")
        return cleaned_data

# Group Chat Creation Form
class NewGroupForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name':forms.TextInput(attrs={'placeholder': 'Add group name ...', 'class':'p-4 text black', 'maxlength':'128', 'autofocus': True}),
        }

# Group Chat Edit
class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name':forms.TextInput(attrs={    
                'class':'p-4 text-xl font-bold mb-4', 
                'maxlength':'300'}),
        }