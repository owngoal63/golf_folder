from rest_framework.serializers import ModelSerializer
from golf.models import Course

class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
