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

class CardInitialForm(forms.Form):

    course = forms.ChoiceField()
    player_A = forms.IntegerField()
    player_B = forms.IntegerField()
    player_C = forms.IntegerField()
    player_D = forms.IntegerField()
    no_of_players = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.no_of_players = kwargs.pop('no_of_players')
        self.player_a = kwargs.pop('player_a')
        self.player_b = kwargs.pop('player_b')
        if self.no_of_players == 3:
            self.player_c = kwargs.pop('player_c')
        elif self.no_of_players == 4:
            self.player_c = kwargs.pop('player_c')
            self.player_d = kwargs.pop('player_d')
        super(CardInitialForm, self).__init__(*args,**kwargs)
        self.fields['course'] = forms.ChoiceField(
            choices=[(c.id, str(c.name)) for c in Course.objects.all()]
        )
        self.fields['player_A'].label = self.player_a
        self.fields['player_B'].label = self.player_b
        if self.no_of_players == 3:
            self.fields['player_C'].label = self.player_c
        if self.no_of_players == 4:
            self.fields['player_C'].label = self.player_c
            self.fields['player_D'].label = self.player_d
        self.fields['no_of_players'].initial = self.no_of_players
        if self.no_of_players < 3:
            self.fields['player_C'].initial = 0
            self.fields['player_C'].disabled = True
            self.fields['player_D'].initial = 0
            self.fields['player_D'].disabled = True
        elif self.no_of_players == 3:
            self.fields['player_D'].initial = 0
            self.fields['player_D'].disabled = True

class CardEntryForm(forms.Form):

    player_A = forms.IntegerField()
    player_B = forms.IntegerField()
    player_C = forms.IntegerField()
    player_D = forms.IntegerField()

    def __init__(self, *args, **kwargs):
        no_of_players = len(kwargs)
        # print(no_of_players)
        # if no_of_players != 0:   # If 0 - must be request.method == POST so do not pop kwargs
        self.player_a = kwargs.pop('player_a')
        self.player_b = kwargs.pop('player_b')
        if no_of_players == 3:
            self.player_c = kwargs.pop('player_c')
        elif no_of_players == 4:
            self.player_c = kwargs.pop('player_c')
            self.player_d = kwargs.pop('player_d')
        super(CardEntryForm, self).__init__(*args,**kwargs)
        # self.fields['player_A'].label = self.player_a
        self.fields['player_A'].label = ''
        # self.fields['player_B'].label = self.player_b
        self.fields['player_B'].label = ''
        if no_of_players == 3:
            # self.fields['player_C'].label = self.player_c
            self.fields['player_C'].label = ''
        if no_of_players == 4:
            # self.fields['player_C'].label = self.player_c
            self.fields['player_C'].label = ''
            # self.fields['player_D'].label = self.player_d
            self.fields['player_D'].label = ''
        if no_of_players < 3:
            # self.fields['player_C'].initial = 0
            # self.fields['player_C'].disabled = True
            # self.fields['player_D'].initial = 0
            # self.fields['player_D'].disabled = True
            self.fields['player_C'].required = False
            self.fields['player_D'].required = False
        elif no_of_players == 3:
            self.fields['player_D'].initial = 0
            self.fields['player_D'].disabled = True
    

