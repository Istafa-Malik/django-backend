from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
# Create your models here.

class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User')
    )
    role = models.CharField(max_length=10, choices=ROLES, default='viewer')

    def __str__(self):
        return self.username


class FolderAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    folder_path = models.CharField(max_length=500)
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.folder_path.startswith("djangobackend/"):
            self.folder_path = self.folder_path.replace("djangobackend/", "", 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} → {self.folder_path}"
    
class FileAccess(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.file_path.startswith("djangobackend/"):
            self.file_path = self.file_path.replace("djangobackend/", "", 1)
        super().save(*args, **kwargs)


class EnvironmentConfig(models.Model):
    ENV_CHOICES = [
        ('development', 'Development'),
        ('production', 'Production'),
    ]

    environment = models.CharField(max_length=20, choices=ENV_CHOICES, unique=True)
    base_url = models.URLField(help_text="Base domain URL like https://example.com")

    def __str__(self):
        return f"{self.environment} → {self.base_url}"
