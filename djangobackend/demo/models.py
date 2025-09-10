from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -------------------- Custom User --------------------
class User(AbstractUser):
    ROLES = (
        ('admin', 'Admin'),
        ('user', 'User')
    )
    role = models.CharField(max_length=10, choices=ROLES, default='user')

    def __str__(self):
        return self.username


# -------------------- Folder --------------------
class Folder(models.Model):
    folder_path = models.CharField(max_length=500, unique=True)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_folders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.folder_path.startswith("djangobackend/"):
            self.folder_path = self.folder_path.replace("djangobackend/", "", 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.folder_path}) owned by {self.owner.username}"


# -------------------- User Permissions --------------------
class UserPermissions(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    can_upload_folder = models.BooleanField(default=False)
    can_upload_file = models.BooleanField(default=False)

    def __str__(self):
        return f"Permissions for {self.user.username}"


# -------------------- Folder Access --------------------
class FolderAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='access',
        null=True,   # ✅ make it optional so migrations won’t break
        blank=True   # ✅ allow blank in forms/admin
    )
    can_view = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_download = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'folder')

    def __str__(self):
        # handle case when folder is NULL
        folder_name = self.folder.folder_path if self.folder else "No Folder"
        return f"{self.user.username} → {folder_name}"


# -------------------- File Access --------------------
class FileAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_download = models.BooleanField(default=False)
    last_modified = models.DateTimeField(auto_now=True)
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.file_path.startswith("djangobackend/"):
            self.file_path = self.file_path.replace("djangobackend/", "", 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} → {self.file_path}"


# -------------------- Environment Config --------------------
class EnvironmentConfig(models.Model):
    ENV_CHOICES = [
        ('development', 'Development'),
        ('production', 'Production'),
    ]
    environment = models.CharField(max_length=20, choices=ENV_CHOICES, unique=True)
    base_url = models.URLField(help_text="Base domain URL like https://example.com")

    def __str__(self):
        return f"{self.environment} → {self.base_url}"
