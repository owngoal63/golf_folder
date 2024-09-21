from rest_framework.serializers import ModelSerializer, StringRelatedField, CharField, EmailField, IntegerField
from golf.models import Course, Score, GolfGroup, Buddy

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


class GolfGroupSerializer(ModelSerializer):
    class Meta:
        model = GolfGroup
        fields = '__all__'

# class BuddySerializer(ModelSerializer):
#     class Meta:
#         model = Buddy
#         fields = '__all__'

# class BuddySerializer(ModelSerializer):
#     group_name = CharField(source='group.group_name')
#     email = EmailField(source='buddy_email.email')
#     firstname = CharField(source='buddy_email.firstname')

#     class Meta:
#         model = Buddy
#         fields = ['group_name', 'email', 'firstname']

#     def to_representation(self, instance):
#         # This ensures that related fields are properly populated
#         representation = super().to_representation(instance)
#         representation['group_name'] = instance.group.group_name
#         representation['email'] = instance.buddy_email.email
#         representation['firstname'] = instance.buddy_email.firstname
#         return representation

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