from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import serializers
from .models import User, DataBefore, DataAfter, DataFormat, DataFormatClues
from django.contrib.auth.models import Group


# first we define the serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', "first_name", "last_name")


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("name", )


class DataBeforeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataBefore
        fields = ("id", "name", "file")


class DataFormatCluesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataFormatClues
        fields = ("id", "column_name", "clues")


class DataFormatSerializer(serializers.HyperlinkedModelSerializer):
    ignore_columns = serializers.CharField(max_length=150, allow_blank=True)
    use_columns = serializers.CharField(max_length=150, allow_blank=True)
    class Meta:
        model = DataFormat
        fields = ("id", "name", "file", "ignore_columns", "use_columns")


class DataAfterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataAfter
        fields = ("id", "name", "file", "data_before", "data_format")

