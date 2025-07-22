from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FolderAccess, FileAccess, UserPermissions

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']

    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)


@admin.register(FolderAccess)
class FolderAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'folder_path', 'can_view', 'can_edit', 'can_delete')
    list_filter = ('can_view', 'can_edit', 'can_delete')
    search_fields = ('user__username', 'folder_path')

@admin.register(FileAccess)
class FileAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_path', 'can_view', 'can_edit', 'can_delete')
    list_filter = ('can_view', 'can_edit', 'can_delete')
    search_fields = ('user__username', 'file_path')

@admin.register(UserPermissions)
class UserPermssionsAdmin(admin.ModelAdmin):
    list_display=('user', 'can_upload_folder', 'can_upload_file')
    list_filter=('can_upload_folder', 'can_upload_file')