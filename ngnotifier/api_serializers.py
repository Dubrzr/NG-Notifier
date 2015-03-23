import re
from rest_framework import serializers

from ngnotifier.models import NGHost, NGGroup, NGNews


# Serializers
class NGHostSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    host_url = serializers.ReadOnlyField(source='host')
    nb_groups = serializers.ReadOnlyField()

    class Meta:
        model = NGHost
        fields = ('id', 'host_url', 'nb_groups')


class NGGroupSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    group_name = serializers.ReadOnlyField(source='name')
    topic_nb = serializers.ReadOnlyField(source='nb_news')

    class Meta:
        model = NGGroup
        fields = ('id', 'group_name', 'topic_nb')


class NGNewsSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    author = serializers.ReadOnlyField(source='email_from')
    subject = serializers.ReadOnlyField()
    content = serializers.ReadOnlyField(source='contents')
    creation_date = serializers.DateTimeField(source='date', format='%Y-%m-%dT%H:%M:%S%z')
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = NGNews
        fields = ('id', 'author', 'subject', 'content',
                  'creation_date', 'groups')


class RecursiveField(serializers.Serializer):
    def to_representation(self, instance):
        serializer = self.parent.parent.__class__(instance, context=self.context)
        return serializer.data


class NGNewsDetailSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.ReadOnlyField(source='pk')
    author = serializers.ReadOnlyField(source='email_from')
    subject = serializers.ReadOnlyField()
    content = serializers.ReadOnlyField(source='contents')
    creation_date = serializers.DateTimeField(source='date', format='%Y-%m-%dT%H:%M:%S%z')
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    children = RecursiveField(many=True, source='father')

    class Meta:
        model = NGNews
        fields = ('id', 'author', 'subject', 'content',
                  'creation_date', 'groups', 'children')