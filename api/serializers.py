from rest_framework.serializers import ModelSerializer, StringRelatedField, CharField, EmailField, IntegerField
from rest_framework.fields import SerializerMethodField
from golf.models import Course, Score, GolfGroup, Buddy
from accounts.models import CustomUser

class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'


class ScoreSerializer(ModelSerializer):
    course = StringRelatedField(many=False) # Required for the model lookup
    group = StringRelatedField(many=False)  # Required for the model lookup
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


class GolfGroupSerializer(ModelSerializer):
    class Meta:
        model = GolfGroup
        fields = '__all__'

class BuddySerializer(ModelSerializer):
    group_id = IntegerField(source='group.id')
    group_name = CharField(source='group.group_name')
    user_id = IntegerField(source='buddy_email.id')
    email = EmailField(source='buddy_email.email')
    firstname = CharField(source='buddy_email.firstname')

    class Meta:
        model = Buddy
        fields = ['id', 'group_id', 'group_name', 'user_id', 'email', 'firstname']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['group_id'] = instance.group.id
        representation['group_name'] = instance.group.group_name
        representation['user_id'] = instance.buddy_email.id
        representation['email'] = instance.buddy_email.email
        representation['firstname'] = instance.buddy_email.firstname
        return representation
    
class UserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class ScoreSerializerExtended(ModelSerializer):
    player_a = UserSerializer()
    player_b = UserSerializer()
    player_c = UserSerializer()
    player_d = UserSerializer()
    group = GolfGroupSerializer()
    course_name = SerializerMethodField()  # Dynamically get only course name

    class Meta:
        model = Score
        fields = ['id', 'date', 'course_name', 'no_of_players', 'player_a', 'player_b', 'player_c', 'player_d', 'group']

    # Method to get the course name only
    def get_course_name(self, obj):
        return obj.course.name  # Access the 'name' field from the related Course model
