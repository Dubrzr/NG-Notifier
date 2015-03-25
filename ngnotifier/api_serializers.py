from rest_framework import serializers

from ngnotifier.models import NGHost, NGGroup, NGNews


# Serializers
from ngnotifier.utils import ng_news_has_children


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
    creation_date = serializers.DateTimeField(source='date',
                                              format='%Y-%m-%dT%H:%M:%S%z')
    groups = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = NGNews
        fields = ('id', 'author', 'subject', 'content',
                  'creation_date', 'groups')


class NGNewsDetailSerializer(serializers.BaseSerializer):
    def to_representation(self, node):
        has_children = ng_news_has_children(node)
        return {
            'id': node.id,
            'author': node.email_from,
            'subject': node.subject,
            'content': node.contents,
            'creation_date': node.date.strftime('%Y-%m-%dT%H:%M:%S%z'),
            'groups': node.get_groups(),
            'children': sorted(
                [self.to_representation(c) for c in node.get_children()],
                key=lambda x: x['creation_date'],
                reverse=True
            ) if has_children else []
        }