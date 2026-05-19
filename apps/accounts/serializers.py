from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'nome_completo']
        read_only_fields = fields

    def get_nome_completo(self, obj):
        return obj.get_full_name() or obj.username
