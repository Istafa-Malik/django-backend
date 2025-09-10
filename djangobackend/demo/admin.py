from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, FolderAccess, FileAccess, UserPermissions, Folder

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('role',)}),
    )

class FolderAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_folder_path', 'can_view', 'can_edit', 'can_delete')
    list_filter = ('can_view', 'can_edit', 'can_delete')
    search_fields = ('user__username', 'folder__folder_path')

    def get_folder_path(self, obj):
        return obj.folder.folder_path
    get_folder_path.short_description = 'Folder Path'

class FileAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_path', 'can_view', 'can_edit', 'can_delete')
    list_filter = ('can_view', 'can_edit', 'can_delete')
    search_fields = ('user__username', 'file_path')

class UserPermissionsAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_upload_folder', 'can_upload_file')
    list_filter = ('can_upload_folder', 'can_upload_file')

class FolderAdmin(admin.ModelAdmin):
    list_display = ('name', 'folder_path', 'owner', 'created_at', 'is_trashed')
    list_filter = ('is_trashed', 'owner')
    search_fields = ('name', 'folder_path', 'owner__username')

admin.site.register(User, CustomUserAdmin)
admin.site.register(FolderAccess, FolderAccessAdmin)
admin.site.register(FileAccess, FileAccessAdmin)
admin.site.register(UserPermissions, UserPermissionsAdmin)
admin.site.register(Folder, FolderAdmin)
