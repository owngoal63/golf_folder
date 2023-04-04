from rest_framework.serializers import ModelSerializer
from golf.models import Course, Score

class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class ScoreSerializer(ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'
