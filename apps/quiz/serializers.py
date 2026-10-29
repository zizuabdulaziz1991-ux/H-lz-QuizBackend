from rest_framework import serializers


class CategorySerializer(serializers.Serializer):
    slug = serializers.CharField()
    name = serializers.CharField()
    icon = serializers.CharField()
    color = serializers.CharField()
    question_count = serializers.IntegerField()


class CreateSessionSerializer(serializers.Serializer):
    category = serializers.CharField()


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField(allow_null=True)


class SubmitNameSerializer(serializers.Serializer):
    player_name = serializers.CharField(allow_blank=True, max_length=100)
