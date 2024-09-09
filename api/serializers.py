from rest_framework.serializers import ModelSerializer, StringRelatedField
from golf.models import Course, Score

class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class ScoreSerializer(ModelSerializer):
    course = StringRelatedField(many=False)
    group = StringRelatedField(many=False)
    class Meta:
        model = Score
        fields = '__all__'

# Serlializer for Flet Score Listing
class ScoreListSerializer(ModelSerializer):
    course = StringRelatedField(many=False)
    group = StringRelatedField(many=False)
    class Meta:
        model = Score
        fields = ['id', 'date', 'course', 'group']
