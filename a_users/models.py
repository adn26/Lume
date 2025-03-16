from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    info = models.TextField(null=True, blank=True) 
    
    def __str__(self):
        return str(self.user)
    
    @property
    def name(self):
        if self.displayname:
            return self.displayname
        return self.user.username 
    
    @property
    def avatar(self):
        if self.image and self.image.name:
            try:
                return self.image.url
            except Exception as e:
                print(f"Error generating URL: {e}")
                # Fallback to direct URL
                bucket_name = settings.AWS_STORAGE_BUCKET_NAME
                region = settings.AWS_S3_REGION_NAME
                return f"https://{bucket_name}.s3.{region}.amazonaws.com/{self.image.name}"
        return f'{settings.STATIC_URL}images/avatar.svg'