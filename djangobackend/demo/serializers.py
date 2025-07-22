from django.contrib.auth import authenticate
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import FolderAccess, FileAccess
User = get_user_model


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            data['user'] = user
            return data
        raise serializers.ValidationError("Invalid username or password")


class BulkFolderAccessSerializer(serializers.Serializer):
    username = serializers.CharField()
    folder_path = serializers.CharField()
    can_view = serializers.BooleanField(default=True)
    can_edit = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)

    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError(f"User '{value} does not exist")
        return value
    



class FolderAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FolderAccess
        fields = '__all__'

class FileAccessSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAccess
        fields = '__all__'