from django import forms
from django.forms import ModelForm
#from django.views.generic.edit import CreateView
from .models import Course, Round, GolfGroup, Buddy


class CourseForm(ModelForm):

    class Meta:
        model = Course
        fields = ('name', 'tee_name', 'par', 'course_rating', 'slope_rating')

class RoundForm(ModelForm):

    class Meta:
        model = Round
        fields = ('date', 'course', 'score')
        widgets={
            'date': forms.TextInput(attrs={'type': 'date'}),
            }

class GolfGroupForm(ModelForm):

    class Meta:
        model = GolfGroup
        fields = ('group_name',)

class BuddyForm(ModelForm):

    class Meta:
        model = Buddy
        fields = ('buddy_email',)
