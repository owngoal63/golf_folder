# golf/views.py
from django.db.models import Avg, Min, Max, Count, F
from django.db.models.functions import Round as DBRound
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from random import randrange
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .forms import CourseForm, RoundForm, GolfGroupForm, BuddyForm, CardInitialForm, CardEntryForm, UserForm
from .models import *

from django.shortcuts import render, get_object_or_404
# from django.db.models import Sum
from django.http import JsonResponse
# from django.db.models import F, Func, Value, CharField
# from django.db.models.functions import Concat

from django.contrib.auth.decorators import login_required
import json
import datetime

# from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse

# Langchain imports
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser

from django.conf import settings

from collections import defaultdict

# ~~~~~~~ Course Table CRUD views ~~~~~~~

class CourseAddView(CreateView):
    form_class = CourseForm
    success_url = "/golf/list_courses/"
    template_name = "golf/course_form.html"

class CourseDetailView(DetailView):
    model = Course
    template_name = 'golf/course_detail.html'
    # context_object_name = 'course'

class CourseUpdateView(UpdateView):
    model = Course
    form_class = CourseForm
    success_url = "/golf/list_courses/"
    template_name = "golf/course_form.html"

class CourseListView(ListView):
    model = Course
    ordering = ['name']
    paginate_by = 10

class CourseListDifficultyView(ListView):
    model = Course
    paginate_by = 10
    # ordering = ['-slope_rating']
    template_name = 'golf/course_list_difficulty.html'

    def get_queryset(self):

        stats = Course.objects.aggregate(
            min_course_rating=Min('course_rating'),
            max_course_rating=Max('course_rating'),
            min_slope_rating=Min('slope_rating'),
            max_slope_rating=Max('slope_rating')
        )

        # Difficulty Calculation - First Normalise the Course and Slope rating based upon the min and max values of the courses on the database. Then split the ratio of the calculation 50:50
        # CR_norm = (CR - stats["min_course_rating"]) / (stats["max_course_rating"] - stats["min_course_rating"])
        # SR_norm = (SR - stats["min_slope_rating"]) / (stats["max_slope_rating"] - stats["min_slope_rating"])
        # difficulty  = (0.5 * CR_norm) + (0.5 * SR_norm)
        # difficulty  = (0.5 * (CR - stats["min_course_rating"]) / (stats["max_course_rating"] - stats["min_course_rating"])) + (0.5 * (SR - stats["min_slope_rating"]) / (stats["max_slope_rating"] - stats["min_slope_rating"]))

        # print(stats)
        return Course.objects.annotate(
            difficulty  = DBRound((0.5 * (F('course_rating') - stats["min_course_rating"]) / (stats["max_course_rating"] - stats["min_course_rating"])) +
              (0.5 * (F('slope_rating') - stats["min_slope_rating"]) / (stats["max_slope_rating"] - stats["min_slope_rating"])) , 2)
        ).order_by('-difficulty')  # Hardest first, use 'difficulty' for easiest first

class CourseDeleteView(DeleteView):
    model = Course
    success_url = "/golf/list_courses/"
    template_name = "golf/course_confirm_delete.html"

# ~~~~~~~ Round Table CRUD views ~~~~~~~

class RoundAddView(CreateView):
    form_class = RoundForm
    success_url = "/golf/list_rounds/"
    template_name = "golf/round_form.html"

    def form_valid(self, RoundForm):
        # Default the currently signed in user as the Round->player value on update
        RoundForm.instance.player = self.request.user
        # Check for duplicate record
        duplicate_exists = Round.objects.filter(
            player=RoundForm.instance.player,
            date=RoundForm.instance.date,
            course=RoundForm.instance.course
        ).exists()

        if duplicate_exists:
            print('A round for this player, date, and course already exists. Will not add.')
            return self.form_invalid(RoundForm)
        
        # Update net_score value
        net_score = RoundForm.instance.score - RoundForm.instance.course.par
        RoundForm.instance.net_score = "+" + str(net_score) if net_score > 0 else str(net_score) 
        
        # Update handicap_differential value
        RoundForm.instance.handicap_differential = round((RoundForm.instance.score - RoundForm.instance.course.course_rating) * 113 / RoundForm.instance.course.slope_rating, 1)
        
        return super().form_valid(RoundForm)

class RoundListView(ListView):
    model = Round
    ordering = ['-date']
    paginate_by = 10

    # Filter queryset to show only rounds for this signed in user
    def get_queryset(self, **kwargs):
       qs = super().get_queryset(**kwargs)
       return qs.filter(player=self.request.user)

class RoundDetailView(DetailView):
    model = Round
    template_name = 'golf/round_detail.html'

    # Calculate net_score from round and course join and pass as context to template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        round_obj = self.object
        context['object'] = round_obj
        #course_obj = Course.objects.filter(round = round_obj )[0]   
        net_score = self.object.score - round_obj.course.par
        # net_score = (self.object.score - round_obj.course.course_rating) * 113 / round_obj.course.slope_rating
        net_score = "+" + str(net_score) if net_score > 0 else str(net_score)
        # print(round_obj.course.par)
        context['net_score'] = net_score
        return context


class RoundUpdateView(UpdateView):
    model = Round
    form_class = RoundForm
    success_url = "/golf/list_rounds/"
    template_name = "golf/round_form.html"

    def form_valid(self, RoundForm):
        # Default the currently signed in user as the Round->player value on update
        RoundForm.instance.player = self.request.user
        # Update net_score value
        net_score = RoundForm.instance.score - RoundForm.instance.course.par
        RoundForm.instance.net_score = "+" + str(net_score) if net_score > 0 else str(net_score) 
        # Update handicap_differential value
        RoundForm.instance.handicap_differential = round((RoundForm.instance.score - RoundForm.instance.course.course_rating) * 113 / RoundForm.instance.course.slope_rating, 1)
        return super().form_valid(RoundForm)

class RoundDeleteView(DeleteView):
    model = Round
    success_url = "/golf/list_rounds/"
    template_name = "golf/round_confirm_delete.html"

# ~~~~~~~ Golf Handicap Calculated views ~~~~~~~
class RoundListHandicapView(ListView):
    model = Round
    template_name = 'golf/round_list_handicap.html'
    ordering = ['-date']
    # paginate_by = 20  (pagination removed - only show last 20 rounds)

    # Filter queryset to show only rounds for this signed in user
    # def get_queryset(self, **kwargs):
    #     qs = super().get_queryset(**kwargs)
    #     # Filter rounds for user (default) or for player if id passed as parameter (for buddy groups)
    #     player_id = self.request.user
    #     if len(self.request.GET.keys()) == 0:
    #         player_qs = qs.filter(player=player_id)
    #     else:
    #         if 'p' in self.request.GET.keys():
    #             player_id = self.request.GET.get('p')
    #             player_qs = qs.filter(player=player_id)
    #         if 'd' in self.request.GET.keys():
    #             date_parameter = self.request.GET.get('d')
    #             if date_parameter == '4weeks':
    #                 date_filter = datetime.datetime.now() - datetime.timedelta(weeks=46)
    #             if date_parameter == '6months':
    #                 date_filter = datetime.datetime.now() - datetime.timedelta(weeks=47)
    #             if date_parameter == '1year':
    #                 date_filter = datetime.datetime.now() - datetime.timedelta(weeks=48)
    #             player_qs = qs.filter(player=player_id, date__lte = date_filter)
    #     # player_qs = qs.filter(player=player_id)
    #     # print(player_qs)
    #     return player_qs

    # Calculate net_score from round and course join and pass as context to template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_parameter'] = ' Today' # set to empty string as default
        context['buddy_text'] = '' # set to empty string by default
        date_parameter = '' # Default set to empty string

        # Filter rounds for user (default) or for player if id passed as parameter (for buddy groups)
        player_id = self.request.user
        if len(self.request.GET.keys()) == 0:   # No parameters passed
            round_obj = Round.objects.filter(player = player_id ).order_by('-date')[0:20] # Most recent 20 rounds
            # pass
        else:
            if 'p' in self.request.GET.keys():  # Buddy Player parameter passed
                player_id = self.request.GET.get('p')
                round_obj = Round.objects.filter(player = player_id ).order_by('-date')[0:20] # Most recent 20 rounds
                context['buddy_text'] = 'Your buddy:'
            if 'd' in self.request.GET.keys():  # Date parameter passed
                date_parameter = self.request.GET.get('d')
                context['date_parameter'] = f"for {date_parameter} Ago"
                if date_parameter == '4weeks':
                    date_filter = datetime.datetime.now() - datetime.timedelta(weeks=4)
                if date_parameter == '6months':
                    date_filter = datetime.datetime.now() - datetime.timedelta(weeks=26)
                if date_parameter == '1year':
                    date_filter = datetime.datetime.now() - datetime.timedelta(weeks=52)
                if date_parameter == 'YearStart':
                    date_filter = datetime.datetime(datetime.datetime.now().year, 1,1)
                    context['date_parameter'] = "at Start of Year"
                if date_parameter == 'LastYearStart':
                    date_filter = datetime.datetime(datetime.datetime.now().year - 1, 1,1)
                    context['date_parameter'] = "at Start of Last Year"

                    # player_qs = qs.filter(player=player_id, date__lte = date_filter)
                # isApple = True if fruit == 'Apple' else False
                # context['date_parameter'] = "at Start of Year" if date_parameter == "YearStart" or date_parameter == "LastYearStart" else f"{date_parameter} Ago"
                round_obj = Round.objects.filter(player = player_id, date__lte = date_filter ).order_by('-date')[0:20] # Most recent 20 rounds
        # round_obj = self.object
        # round_obj = Round.objects.filter(player = player_id ).order_by('-date')[0:20] # Most recent 20 rounds
        # print(date_parameter)
        context['object'] = round_obj
        # Determine if weighting factor needs to be applied
        # num_score_differentials = len(Round.objects.filter(player = player_id ))
        num_score_differentials = len(round_obj)
        # print("num_score_differentials", num_score_differentials)
        context['total_number_of_rounds'] = num_score_differentials
        if(num_score_differentials >= 3 and num_score_differentials <= 20):
            diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = num_score_differentials )[0]
        elif(num_score_differentials > 20):
            diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = 20 )[0]
        # List that is passed to template with ID's of rounds which make up the handicap
        # lowest_round_id_list = []
        context['player'] = CustomUser.objects.filter(email=round_obj[0].player)[0].firstname if num_score_differentials > 0 else ''

        # remember to remove ths !!!!!!!!
        r = get_list_of_rounds_with_valid_hcp(player_id)
        # print("no of rounds", len(r))
        # print("calc factor",diffadjustment_obj.calculation_factor)
        # print("adjustment", diffadjustment_obj.adjustment)
        # for x in xx:
        #     print(calculate_handicap_on_date(x))
        hcp_history_list = build_handicap_list_over_time(r, player_id)
        print(hcp_history_list)
        # hcp_history_list.reverse()
        # print(hcp_history_list)
        worst_hcp = max(hcp_history_list, key=lambda item: item[1])[1]
        best_hcp = min(hcp_history_list, key=lambda item: item[1])[1]
        worst_hcp_date = max(hcp_history_list, key=lambda item: item[1])[0]
        best_hcp_date = min(hcp_history_list, key=lambda item: item[1])[0]
        print("worst hcp", worst_hcp)
        print("best", best_hcp)

        if(num_score_differentials < 3):
            context['message'] = 'Minimum of 3 rounds is required to calculate handicap'

        else:   # This is where the magic happens!
            print("greater than 3")
            round_obj_bylowest = sorted(round_obj, key=lambda o: o.handicap_differential)[:diffadjustment_obj.calculation_factor]    
            lowest_round_id_list = [ o.id for o in round_obj_bylowest ]
            context['calculated_handicap'] = round(sum([i.handicap_differential for i in round_obj_bylowest]) / len(round_obj_bylowest) + diffadjustment_obj.adjustment,1)
            context['number_of_lowest_rounds'] = str(diffadjustment_obj.calculation_factor)
            context['lowest_round_id_list'] = lowest_round_id_list
            context['worst_hcp'] = worst_hcp
            context['best_hcp'] = best_hcp
            context['worst_hcp_date'] = worst_hcp_date
            context['best_hcp_date'] = best_hcp_date

        return context

class HandicapDetailView(TemplateView):
    # model = Round
    template_name = 'golf/handicap_detail_view.html'

# ~~~~~~~ Golf Group CRUD views ~~~~~~~

class GolfGroupAddView(CreateView):
    form_class = GolfGroupForm
    success_url = "/golf/list_golf_groups/"
    template_name = "golf/golfgroup_form.html"

    # Default the currently signed in user as the GolfGroup->administrator
    def form_valid(self, GolfGroupForm):
        GolfGroupForm.instance.administrator = self.request.user
        return super().form_valid(GolfGroupForm)

    # Create record in Buddy model with Group ID and Group Administrator email  
    def get_success_url(self):
        # print(self.object.id)
        Buddy_instance = Buddy.objects.create(group = self.object, buddy_email = self.request.user)
        # print(Buddy_instance)
        return reverse('golfgrouplist')


class GolfGroupListView(ListView):
    model = GolfGroup
    ordering = ['group_name']
    paginate_by = 10

    # Filter queryset to show only rounds for this signed in user
    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        return qs.filter(administrator=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups_user_is_in'] = GolfGroup.objects.filter(buddy__buddy_email = self.request.user )
        return context

class GolfGroupDetailView(DetailView):
    model = GolfGroup
    template_name = 'golf/golfgroup_detail.html'

class GolfGroupUpdateView(UpdateView):
    model = GolfGroup
    form_class = GolfGroupForm
    success_url = "/golf/list_golf_groups/"
    template_name = "golf/golfgroup_form.html"


class GolfGroupDeleteView(DeleteView):
    model = GolfGroup
    success_url = "/golf/list_golf_groups/"
    template_name = "golf/golfgroup_confirm_delete.html"

# ~~~~~~~ Buddies CRUD views ~~~~~~~

class BuddyAddView(CreateView):
    form_class = BuddyForm
    template_name = "golf/buddy_form.html"

    # Default the currently selected group into the form submission
    def form_valid(self, BuddyForm):
        BuddyForm.instance.group_id = self.kwargs.get("group")
        return super().form_valid(BuddyForm)

    # Pass parameter of group id back to success_url
    def get_success_url(self):
        return reverse('buddylist', kwargs={'group': self.kwargs.get("group") })


class BuddyListView(ListView):
    model = Buddy
    # ordering = ['buddy_email']
    paginate_by = 10

    # Filter queryset to show only buddies for this signed in user
    def get_queryset(self, **kwargs):
       qs = super().get_queryset(**kwargs)
       return qs.filter(group = self.kwargs.get("group"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_is_administrator'] = GolfGroup.objects.filter(buddy__buddy_email = self.request.user )
        # print(self.kwargs.get("group"))
        group_administrator_obj = GolfGroup.objects.filter(id=self.kwargs.get("group"), administrator = self.request.user )
        context['user_is_administrator'] = group_administrator_obj
        return context
    
class BuddyListAllView(ListView):
    model = CustomUser
    template_name = 'golf/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        return CustomUser.objects.filter(player_type='REGULAR')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from datetime import date
        today = date.today()
        
        # Add today's handicap to each user object
        for user in context['users']:
            user.handicap = calculate_handicap_on_date(today, user.id)[1]
            
        return context

class BuddyUpdateView(UpdateView):
    model = Buddy
    form_class = BuddyForm
    template_name = "golf/buddy_form.html"

    # Pass parameter of group id back to success_url
    def get_success_url(self):
        return reverse('buddylist', kwargs={'group': self.kwargs.get("group") })

class BuddyDeleteView(DeleteView):
    model = Buddy
    # success_url = "/golf/list_golf_groups/"
    template_name = "golf/buddy_confirm_delete.html"

    # Pass parameter of group id back to success_url
    def get_success_url(self):
        return reverse('buddylist', kwargs={'group': self.kwargs.get("group") })

# ~~~~~~~ Chart views ~~~~~~~

class MyObject:
    def __init__(self, d=None):
        if d is not None:
            for key, value in d.items():
                setattr(self, key, value)

class Object:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

@login_required
def chart_rounds_page(request):
    return render(request, 'golf/chart_rounds_page.html')

@login_required
def chart_rounds_graph(request):
    labels = []
    data = []

    queryset = Round.objects.all().values('date','score').filter(player=request.user).order_by('date')

    for entry in queryset:
        labels.append(entry['date'])
        data.append(entry['score'])
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required
def chart_historical_hcp_page(request):
    return render(request, 'golf/chart_historical_hcp_page.html')


@login_required
def chart_historical_hcp_graph(request):
    labels = []
    data = []

    player_id = request.user
    r = get_list_of_rounds_with_valid_hcp(player_id)
    hcp_history_list = build_handicap_list_over_time(r, player_id)
    # hcp_history_list.reverse()      # Sort oldest to most recent
    monthly_averages = average_per_month(hcp_history_list)
    monthly_averages_list = [(k,v) for k,v in sorted(monthly_averages.items())]

    for hcp_on_date in monthly_averages_list:
        labels.append(hcp_on_date[0])
        data.append(hcp_on_date[1])
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })


@login_required
def chart_handicap_page(request):
    # player_id = request.user if len(request.GET.keys()) == 0 else request.GET.get('p')
    # print(player_id)
    return render(request, 'golf/chart_handicap_page.html')

@login_required
def chart_handicap_graph(request):
    # player_id = request.user if len(request.GET.keys()) == 0 else request.GET.get('p')
    # print("******************************************")
    # print(player_id)
    labels = []
    data = []
    backgroundcolors = []
    roundcourses = []
    coursesplayed = []
    coursesplayedcolor = []
    defaultColors = [
    "#3366CC", "#DC3912", "#FF9900", "#109618", "#990099", "#3B3EAC", "#0099C6",
    "#DD4477", "#66AA00", "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
    "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6", "#651067",
    "#FF6B35", "#2E8B57", "#9370DB", "#CD853F", "#4682B4", "#D2691E", 
    "#8FBC8F", "#DA70D6", "#20B2AA", "#F4A460"
    ]
    course_colours = dict()

    # queryset = Round.objects.all().values('date','handicap_differential').filter(player=request.user).order_by('date')
    queryset = Round.objects.all().values('date', 'course__name','handicap_differential').filter(player=request.user).order_by('date')
    # print(queryset)
    queryset_courses = Round.objects.values('course__name').annotate(dcount=Count('course__name')).filter(player=request.user).order_by()
    # print(queryset_courses)
    for course in enumerate(queryset_courses):
        course_colours[course[1].get("course__name")] = defaultColors[course[0]]
        coursesplayed.append(course[1].get("course__name"))
        coursesplayedcolor.append(defaultColors[course[0]])
    # print(coursesplayed)
    # print(coursesplayedcolor)

    _min = queryset.aggregate(min = Min('handicap_differential'))
    _max = queryset.aggregate(max = Max('handicap_differential'))
    _avg = queryset.aggregate(avg = Avg('handicap_differential'))
    average_handicap = _avg.get("avg")
    max_height = max(_min.get("min"), _max.get("max")) - average_handicap
    suggested_min = 0-max_height
    suggested_max = max_height

    # Limit to last x rounds
    # This is now done in chart.js

    # print(queryset)
    for entry in queryset:
        labels.append(entry['date'])
        data.append(entry['handicap_differential'] - average_handicap)
        # print(course_colours[entry['course__name']])
        backgroundcolors.append(course_colours[entry['course__name']])
        roundcourses.append(entry['course__name'])
    # print(roundcourses)
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
        's_min': suggested_min,
        's_max': suggested_max,
        'average': str(round(average_handicap,2)),
        'backgroundcolors': backgroundcolors,
        'roundcourses': roundcourses,
        'coursesplayed': coursesplayed,
        'coursesplayedcolor': coursesplayedcolor
    })

def make_stars(num):
    return "*" * num

def find_best_hole(golf_data):
    all_performances = []
    player_best = {}
    
    # Extract all performances and track each player's best
    for player_key, player_data in golf_data.items():
        firstname = player_data['firstname']
        player_performances = []
        
        for hole_data in player_data['holes_attr']:
            hole_num = hole_data[0]      # Position 0: hole number
            par = hole_data[1]           # Position 1: par
            stroke_index = hole_data[2]  # Position 2: stroke index  
            gross_score = hole_data[4]   # Position 4: gross score
            
            score_vs_par = gross_score - par
            
            performance = {
                'player': firstname,
                'hole': hole_num,
                'score_vs_par': score_vs_par,
                'stroke_index': stroke_index,
                'gross_score': gross_score,
                'par': par
            }
            
            all_performances.append(performance)
            player_performances.append(performance)
        
        # Find this player's best hole
        player_performances.sort(key=lambda x: (x['score_vs_par'], x['stroke_index']))
        player_best[firstname] = player_performances[0]
    
    # Find overall winner
    all_performances.sort(key=lambda x: (x['score_vs_par'], x['stroke_index']))
    overall_winner = all_performances[0]
    
    return {
        'overall_winner': overall_winner,
        'player_best_holes': player_best
    }

def get_adjusted_scores_string(data):
    scores = []
    
    # Check each player in order
    for i in range(1, 5):  # player1 to player4
        player_key = f'player{i}'
        if player_key in data:
            # Get the 10th entry (index 9) from running_totals
            adjusted_score = data[player_key]['running_totals'][9]
            scores.append(str(adjusted_score))
    
    return ','.join(scores)



def calculate_positions(numbers_list):
    sorted_numbers = sorted(numbers_list, reverse=True)
    positions = []
    for number in numbers_list:
        position = sorted_numbers.index(number) + 1
        if position == 1:
            positions.append("Gold")
        elif position == 2:
            positions.append("Silver")
        elif position == 3:
            positions.append("DarkGoldenRod")
        elif position == 4:
            positions.append("#008080")
        else:
            # Handle ties
            same_rank = sorted_numbers.count(number)
            if same_rank == 1:
                positions.append(str(position) + "th")
            else:
                rank_range = list(range(position, position+same_rank))
                rank_str = '-'.join([str(rank) for rank in rank_range])
                positions.append(rank_str + " equal")
    return positions

def compare_and_return_color(par, score):
    if score > par + 2:
        return "#A52A2A"
    elif score > par + 1:
        return "#D2691E"
    elif score < par - 2:
        return "#0000FF"  # gold
    elif score <par - 1:
        return "#1E90FF"  # silver
    else:
        return "#009688"  # background colour

def set_colour_for_handicap_adjustment(par, gross_score, net_score):
    handicap_adjustment = gross_score - (par + 2 + (gross_score - net_score))
    if handicap_adjustment > 0:
       if handicap_adjustment > 2:
           return ("#581845", 3)
       if handicap_adjustment == 2:
           return ("#A52A2A", handicap_adjustment)
       if handicap_adjustment == 1:
           return ("#D2691E", handicap_adjustment)
    else:
        return ("#009688", 0)  # background colour
    
    
def sort_by_value_and_describe(list_to_sort, sort_by_index):
    """
    Sorts a list of paired values based on the value at a specified index and returns a string describing the sorted outcome.

    Args:
        list_to_sort (list): A list of paired values.
        sort_by_index (int): The index of the value to sort by.

    Returns:
        str: A string describing the sorted outcome.
    """
    list_length = len(list_to_sort)
    sorted_list = sorted(list_to_sort, key=lambda x: x[sort_by_index], reverse=True)
    description = ""
    for i, pair in enumerate(sorted_list):
        if i == 0:
            description += "leading the charge is "
        elif sorted_list[i - 1][sort_by_index] == pair[sort_by_index]:
            description += ", tied with "
        elif i == len(sorted_list) - 1:
            if list_length > 2:
                description += "and finally, "
            else:
                description += "and trailing is "
        else:
            description += ". Next is "

        description += f"{pair[0]} with {pair[1]} points "

    return description

def siri_message_for_shots_left(player_firstname, hole_no, score_target, current_no_shots):
    if score_target != 0:
        strokes_left = score_target - current_no_shots
        if strokes_left >= 0:
            if hole_no > 18:
                strokes_left_message = f" {player_firstname}, great job! You have beaten your handicap target today by {strokes_left} shots "
            else:
                strokes_left_message = f" {player_firstname} you have {strokes_left} shots left to improve your handicap "
        else:
            if hole_no > 18:
                strokes_left_message = f" {player_firstname}, get back to the range! I'm afraid you have not improved your handicap today "
            else:
                strokes_left_message = f" {player_firstname} I'm afraid you have 0 shots left to improve your handicap "    
    else: strokes_left_message = f" {player_firstname} you do not have enough rounds yet for a handicap "

    return strokes_left_message

def llm_translate(input_message):

    api_key = settings.OPEN_AI_KEY

    chat_model = ChatOpenAI(openai_api_key = api_key)

    template = """You are a sarcastic golf commentator. You should paraphrame the text provided, ensuring that you say all the relevent details
                    but in wording that is sarcastically humourous."""
    human_template = input_message

    chat_prompt = ChatPromptTemplate.from_messages([
            ("system", template),
            ("human", human_template)
    ])

    messages = chat_prompt.format_messages(problem = human_template)
    result = chat_model.predict_messages(messages)

    return str(result.content.replace('\n', ' '))


def format_firstnames_for_report(names):
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    elif len(names) > 2:
        formatted_names = ", ".join(names[:-1])
        return f"{formatted_names}, and {names[-1]}"
    else:
        return ", ".join(names)


# @login_required   ---- Switched off to allow non-authenticated Siri execution
def trackmatch(request, score_id, hole_no, extraparam = False, makereport = False, towho = "You"):
    # Get Functional Parameters and Initaliase variables
    if extraparam == "colourize":
        colourize = True
    else:
        colourize = False
    if extraparam == "Siri":
        siri = True
    else:
        siri = False
    score_instance = Score.objects.get(id = score_id)
    no_of_players = score_instance.no_of_players
    player_hcps = []
    player_hcps.append(score_instance.player_a_course_hcp)
    player_hcps.append(score_instance.player_b_course_hcp)
    player_hcps.append(score_instance.player_c_course_hcp)
    player_hcps.append(score_instance.player_d_course_hcp)
    holes_attr=[]
    running_totals = []
    stableford_dict = {
        "1": 1,
        "0": 2,
        "-1": 3,
        "-2": 4,
        "-3": 5,
        "-4": 6,
        "-5": 7
    }

    cq = Course.objects.all().get(id = score_instance.course.id)      
    buddy_queryset = Buddy.objects.all().filter(group = score_instance.group)
    adjusted_gross = 0

    # Set Round Meta Parameters for passing to form
    round_meta = {}
    round_meta["round_id"] = score_instance.id
    round_meta["buddy_group"] = score_instance.group
    round_meta["name"] = score_instance.name
    round_meta["round_admin"] = score_instance.player_a.email
    round_meta["round_date"] = score_instance.date
    round_meta["no_of_players"] = no_of_players
    round_meta["hole_no"] = hole_no
    round_meta["previous_hole_no"] = hole_no - 1
    round_meta["next_hole_no"] = hole_no + 1
    round_meta["holes_completed"] = hole_no - 1
    round_meta["course_name"] = score_instance.course
    round_meta["course_par"] = cq.par
    round_meta["course_rating"] = cq.course_rating
    round_meta["slope_rating"] = cq.slope_rating
    round_meta["player_a_course_hcp"] = score_instance.player_a_course_hcp
    round_meta["player_b_course_hcp"] = score_instance.player_b_course_hcp
    round_meta["player_c_course_hcp"] = score_instance.player_c_course_hcp
    round_meta["player_d_course_hcp"] = score_instance.player_d_course_hcp
    round_meta["player_a_score_target"] = score_instance.player_a_score_target
    round_meta["player_b_score_target"] = score_instance.player_b_score_target
    round_meta["player_c_score_target"] = score_instance.player_c_score_target
    round_meta["player_d_score_target"] = score_instance.player_d_score_target
    round_meta["outpar"] = cq.hole1par + cq.hole2par + cq.hole3par + cq.hole4par + cq.hole5par + cq.hole6par + cq.hole7par + cq.hole8par + cq.hole9par
    round_meta["inpar"] = cq.hole10par + cq.hole11par + cq.hole12par + cq.hole13par + cq.hole14par + cq.hole15par + cq.hole16par + cq.hole17par + cq.hole18par
    round_meta["totalpar"] = round_meta["outpar"] + round_meta["inpar"]
    round_meta["scores_posted"] = score_instance.scores_posted

    if score_instance.player_a_s18 is not None:     # Is the Match Completed
        round_meta["match_status"] = "Completed"
    else:
        round_meta["match_status"] = "In Progress"

    round_meta["last_hole_scored"] = 18         # Default for completed round
    for i in range(1, 19):
        if getattr(score_instance,"player_a_s{0}".format(i)) is None:
            round_meta["last_hole_scored"] = i - 1
            break



    # List of Stroke Indexes for Course
    holesSI = [cq.hole1SI, cq.hole2SI, cq.hole3SI, cq.hole4SI, cq.hole5SI, cq.hole6SI, cq.hole7SI, cq.hole8SI, cq.hole9SI, 
               cq.hole10SI, cq.hole11SI, cq.hole12SI, cq.hole13SI, cq.hole14SI, cq.hole15SI, cq.hole16SI, cq.hole17SI, cq.hole18SI ]
    
    # Main Loop for Building Handicaps and Scores for all players
    for count, player_hcp in enumerate(player_hcps):
        playerSI = []
        alt_playerSI = []
        if player_hcp <= 18:
            for holeSI in holesSI:
                playerSI.append(1) if holeSI <= player_hcp else playerSI.append(0)
        if player_hcp > 18 and player_hcp <=36:
            for holeSI in holesSI:
                playerSI.append(2) if holeSI <= player_hcp - 18 else playerSI.append(1)
        if player_hcp > 36 and player_hcp <=54:
            for holeSI in holesSI:
                playerSI.append(3) if holeSI <= player_hcp - 36 else playerSI.append(2)

        # Logic for 2 Player Match play calculations
        if count == 0 and no_of_players == 2:   # Get the SI for the 2nd player
            if player_hcps[1] <= 18:
                for holeSI in holesSI:
                    alt_playerSI.append(1) if holeSI <= player_hcps[1] else alt_playerSI.append(0)
            if player_hcps[1] > 18 and player_hcps[1] <=36:
                for holeSI in holesSI:
                    alt_playerSI.append(2) if holeSI <= player_hcps[1] - 18 else alt_playerSI.append(1)
            if player_hcps[1] > 36 and player_hcps[1] <=54:
                for holeSI in holesSI:
                    alt_playerSI.append(3) if holeSI <= player_hcps[1] - 36 else alt_playerSI.append(2)

        # Logic for 2 Player Match play calculations
        if count == 1 and no_of_players == 2:   # Get the SI for the 1st player
            if player_hcps[0] <= 18:
                for holeSI in holesSI:
                    alt_playerSI.append(1) if holeSI <= player_hcps[0] else alt_playerSI.append(0)
            if player_hcps[0] > 18 and player_hcps[0] <=36:
                for holeSI in holesSI:
                    alt_playerSI.append(2) if holeSI <= player_hcps[0] - 18 else alt_playerSI.append(1)
            if player_hcps[0] > 36 and player_hcps[0] <=54:
                for holeSI in holesSI:
                    alt_playerSI.append(3) if holeSI <= player_hcps[0] - 36 else alt_playerSI.append(2)

        # Assign letter for player variable in list ( for use with getattr function retrieving record data from model )
        if count == 0:
            p_letter = "a"
        elif count == 1:
            p_letter = "b"
        elif count == 2:
            p_letter = "c"
        else:
            p_letter = "d"


        # Logic and Calculation for each hole
        hole_obj = ()
        outcome = 0
        for i in range(1, 19):
            gross_score = getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) if not getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) is None else 0
            net_score = gross_score - playerSI[i-1]
            compare_to_par = net_score - eval("cq.hole" + str(i) + "par")
            if no_of_players == 2 and p_letter == 'a' and round_meta["holes_completed"] >= i:
                player_a_compare_to_par = getattr(score_instance,"player_a_s{0}".format(i)) - playerSI[i-1] - eval("cq.hole" + str(i) + "par")
                player_b_compare_to_par = getattr(score_instance,"player_b_s{0}".format(i)) - alt_playerSI[i-1] - eval("cq.hole" + str(i) + "par")
                if player_a_compare_to_par < player_b_compare_to_par:
                    outcome = 1
                elif player_b_compare_to_par < player_a_compare_to_par:
                    outcome = -1
                else:
                    outcome = 0
                # print("Player A")
                # print(outcome)
            if no_of_players == 2 and p_letter == 'b' and round_meta["holes_completed"] >= i:
                player_b_compare_to_par = getattr(score_instance,"player_b_s{0}".format(i)) - playerSI[i-1] - eval("cq.hole" + str(i) + "par")
                player_a_compare_to_par = getattr(score_instance,"player_a_s{0}".format(i)) - alt_playerSI[i-1] - eval("cq.hole" + str(i) + "par")
                if player_b_compare_to_par < player_a_compare_to_par:
                    outcome = 1
                elif player_a_compare_to_par < player_b_compare_to_par:
                    outcome = -1
                else:
                    outcome = 0

            # hole_obj structure
            # hole_no, par, SI, Strokes, Gross (or *), Net, Compare Net to Par, Match Play Outcome, BG Colour set by compare and return function or just on net double bogey check
            # print(colourize)
            if colourize:
                color_adjustment_and_score_adjustment = ('#009688', 0) if round_meta["holes_completed"] < i else set_colour_for_handicap_adjustment(eval("cq.hole" + str(i) + "par"), int(gross_score), int(net_score))
                hole_obj = hole_obj + ((
                    i,
                    eval("cq.hole" + str(i) + "par"),
                    eval("cq.hole" + str(i) + "SI"), playerSI[i-1],
                    make_stars(playerSI[i-1]) if round_meta["holes_completed"] < i else gross_score,
                    '' if round_meta["holes_completed"] < i else net_score,
                    '' if round_meta["holes_completed"] < i else compare_to_par,
                    '' if no_of_players != 2  and round_meta["holes_completed"] < i else outcome,
                    color_adjustment_and_score_adjustment[0],
                    color_adjustment_and_score_adjustment[1],
                    ),
                    )
            else:
                color_adjustment_and_score_adjustment = ('#009688', 0) if round_meta["holes_completed"] < i else set_colour_for_handicap_adjustment(eval("cq.hole" + str(i) + "par"), int(gross_score), int(net_score))
                hole_obj = hole_obj + ((
                i,
                eval("cq.hole" + str(i) + "par"),
                eval("cq.hole" + str(i) + "SI"), playerSI[i-1],
                make_stars(playerSI[i-1]) if round_meta["holes_completed"] < i else gross_score,
                '' if round_meta["holes_completed"] < i else net_score,
                '' if round_meta["holes_completed"] < i else compare_to_par,
                '' if no_of_players != 2  and round_meta["holes_completed"] < i else outcome,
                color_adjustment_and_score_adjustment[0],
                color_adjustment_and_score_adjustment[1],
                ),
                )

        holes_attr.append(hole_obj)
        # print(hole_obj)

        # Get Gross, Net, Stableford, out_nine, in_nine and adjusted_score running totals
        gross, net, stableford, out_nine_gross, out_nine_net, in_nine_gross, in_nine_net, adjusted_score = 0, 0, 0, 0, 0, 0, 0, 0
        player_match_play = 0

        for i in range(1, round_meta["holes_completed"] + 1):
            gross += getattr(score_instance,"player_{0}_s{1}".format(p_letter, i))
            net += getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) - playerSI[i-1]
            adjusted_score += hole_obj[i-1][9]
            adjusted_gross = gross - adjusted_score
            # print(adjusted_score, adjusted_gross)
            if i < 10:
                out_nine_gross = gross
                out_nine_net = net
                out_nine_gross_neg = out_nine_gross
                out_nine_net_neg = out_nine_net
            if i >= 10:
                in_nine_gross = gross - out_nine_gross_neg
                # print(">>>>>",gross, in_nine_gross)
                in_nine_net = net - out_nine_net_neg
            s = (getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) - playerSI[i-1]) - eval("cq.hole" + str(i) + "par")
            stableford += 0 if s >= 2 else stableford_dict[str(s)]
            if p_letter == "a":
                # print(hole_obj[i-1][7])
                player_match_play += hole_obj[i-1][7]
            if p_letter == "b":
                # print(hole_obj[i-1][7])
                player_match_play += hole_obj[i-1][7]


        # Covert Match play totals to text and assign background colour for cell
        if player_match_play == 0:
            player_match_play_text = "AS"
            box_bk_colour = "#008080"
        elif player_match_play < 0:
            player_match_play_text = str(abs(player_match_play)) + " Dn"
            box_bk_colour = "OrangeRed"
        else:
            player_match_play_text = str(player_match_play) + " Up"
            box_bk_colour = "Black"



        running_totals.append((
            (gross, net, stableford, player_match_play_text, box_bk_colour, out_nine_gross, out_nine_net, in_nine_gross, in_nine_net, adjusted_gross)
            )
        )

    # Build the player_dict to pass to the form
    player_dict = {}
    player_details = {}
    for count,player in enumerate(buddy_queryset):
        player_details = {}
        player_details["name"] = str(player.buddy_email)
        player_details["firstname"] = CustomUser.objects.filter(email=player.buddy_email)[0].firstname
        player_details["holes_attr"] = holes_attr[count]
        player_details["running_totals"] = running_totals[count]
        player_dict["player" + str(count + 1)] = player_details


    players_stableford_list = []
    players_stableford_list.append(player_dict["player1"]["running_totals"][2])
    players_stableford_list.append(player_dict["player2"]["running_totals"][2])
    if no_of_players > 2:
        players_stableford_list.append(player_dict["player3"]["running_totals"][2])
    if no_of_players > 3:
        players_stableford_list.append(player_dict["player4"]["running_totals"][2])


    positions = calculate_positions(players_stableford_list)

    stableford_medal_positions = {}
    stableford_medal_positions["a"] = positions[0] 
    stableford_medal_positions["b"] = positions[1]
    if no_of_players > 2:
        stableford_medal_positions["c"] = positions[2]
    if no_of_players > 3:
        stableford_medal_positions["d"] = positions[3]

    # print(player_dict)
    
    # Siri Score info functionaility
    if siri and hole_no > 1:
        print("Siri mode")
        player_name_list = []
        return_details = {}
        return_details["message"] = ""
        if no_of_players == 2:
            player_name_list.append(player_dict['player1']['firstname'])
            player_name_list.append(player_dict['player2']['firstname'])
            if player_dict['player1']['running_totals'][3] == "AS":
                return_details["message"] = f"{player_dict['player1']['firstname']} and {player_dict['player2']['firstname']} are all square through {hole_no - 1} holes. "
            else:
                if "Up" in player_dict['player1']['running_totals'][3]:   # Player 1 is up in the matchplay
                    return_details["message"] = f"{player_dict['player1']['firstname']} is {player_dict['player1']['running_totals'][3]} through {hole_no - 1} holes." 
                else:   # player 2 is up in the matchplay
                    return_details["message"] = f"{player_dict['player2']['firstname']} is {player_dict['player2']['running_totals'][3]} through {hole_no - 1} holes."
        # return_details["message"] = return_details["message"] + f" {player_dict['player1']['firstname']} has {player_dict['player1']['running_totals'][2]} points, {player_dict['player2']['firstname']} has {player_dict['player2']['running_totals'][2]} points."
            holes_left = (18 - hole_no) + 1
            if holes_left <= 4 and score_instance.player_a_score_target:
                strokes_to_target_message = f". With {holes_left} holes to go, {siri_message_for_shots_left(player_dict['player1']['firstname'], hole_no, score_instance.player_a_score_target, player_dict['player1']['running_totals'][0])}. \
                                                                                {siri_message_for_shots_left(player_dict['player2']['firstname'], hole_no, score_instance.player_b_score_target, player_dict['player2']['running_totals'][0])}"
            else: strokes_to_target_message = ""
            return_details["message"] = return_details["message"] + \
                f" As we go to hole number {hole_no}, {player_dict['player1']['firstname']} has played a total of {player_dict['player1']['running_totals'][0]} shots and {player_dict['player2']['firstname']} {player_dict['player2']['running_totals'][0]} shots. " \
                " In Stableford points, " + sort_by_value_and_describe([(player_dict['player1']['firstname'],player_dict['player1']['running_totals'][2]), \
                                                                        (player_dict['player2']['firstname'],player_dict['player2']['running_totals'][2])], 1) + \
                strokes_to_target_message
        if no_of_players == 3:
            player_name_list.append(player_dict['player1']['firstname'])
            player_name_list.append(player_dict['player2']['firstname'])
            player_name_list.append(player_dict['player3']['firstname'])
            holes_left = (18 - hole_no) + 1
            if holes_left <= 4 and score_instance.player_a_score_target:
                strokes_to_target_message = f". With {holes_left} holes to go, {siri_message_for_shots_left(player_dict['player1']['firstname'], hole_no, score_instance.player_a_score_target, player_dict['player1']['running_totals'][0])}. \
                                                                                {siri_message_for_shots_left(player_dict['player2']['firstname'], hole_no, score_instance.player_b_score_target, player_dict['player2']['running_totals'][0])} \
                                                                                {siri_message_for_shots_left(player_dict['player3']['firstname'], hole_no, score_instance.player_c_score_target, player_dict['player3']['running_totals'][0])}"
            else: strokes_to_target_message = ""
            return_details["message"] = return_details["message"] + \
                f" As we go to hole number {hole_no}, {player_dict['player1']['firstname']} has played a total of {player_dict['player1']['running_totals'][0]} shots, {player_dict['player2']['firstname']} {player_dict['player2']['running_totals'][0]} and {player_dict['player3']['firstname']} {player_dict['player3']['running_totals'][0]}. " \
                " In Stableford points, " + sort_by_value_and_describe([(player_dict['player1']['firstname'],player_dict['player1']['running_totals'][2]), \
                                                                        (player_dict['player2']['firstname'],player_dict['player2']['running_totals'][2]), \
                                                                        (player_dict['player3']['firstname'],player_dict['player3']['running_totals'][2])], 1) + \
                strokes_to_target_message
        if no_of_players == 4:
            player_name_list.append(player_dict['player1']['firstname'])
            player_name_list.append(player_dict['player2']['firstname'])
            player_name_list.append(player_dict['player3']['firstname'])
            player_name_list.append(player_dict['player4']['firstname'])
            holes_left = (18 - hole_no) + 1
            if holes_left <= 4 and score_instance.player_a_score_target:
                strokes_to_target_message = f". With {holes_left} holes to go, {siri_message_for_shots_left(player_dict['player1']['firstname'], hole_no, score_instance.player_a_score_target, player_dict['player1']['running_totals'][0])}. \
                                                                                {siri_message_for_shots_left(player_dict['player2']['firstname'], hole_no, score_instance.player_b_score_target, player_dict['player2']['running_totals'][0])} \
                                                                                {siri_message_for_shots_left(player_dict['player3']['firstname'], hole_no, score_instance.player_c_score_target, player_dict['player3']['running_totals'][0])} \
                                                                                {siri_message_for_shots_left(player_dict['player4']['firstname'], hole_no, score_instance.player_d_score_target, player_dict['player4']['running_totals'][0])}"
            else: strokes_to_target_message = ""                
            return_details["message"] = return_details["message"] + \
                f" As we go to hole number {hole_no}, {player_dict['player1']['firstname']} has played a total of {player_dict['player1']['running_totals'][0]} shots, {player_dict['player2']['firstname']} {player_dict['player2']['running_totals'][0]}, {player_dict['player3']['firstname']} {player_dict['player3']['running_totals'][0]} and {player_dict['player4']['firstname']} {player_dict['player4']['running_totals'][0]}. " \
                " In Stableford points, " + sort_by_value_and_describe([(player_dict['player1']['firstname'],player_dict['player1']['running_totals'][2]), \
                                                                        (player_dict['player2']['firstname'],player_dict['player2']['running_totals'][2]), \
                                                                        (player_dict['player3']['firstname'],player_dict['player3']['running_totals'][2]), \
                                                                        (player_dict['player4']['firstname'], player_dict['player4']['running_totals'][2])], 1) + \
                strokes_to_target_message
        if hole_no == 19:
            if makereport:  # Send to ChatGPT for report and email out
                print("make - report")
                return_details["message"] = str(llm_translate(return_details["message"] + f". Your match at {round_meta['course_name']} is over. Hope you enjoyed it!"))
                # return_details["message"] = return_details["message"] + f". Your match at {round_meta['course_name']} is over. Hope you enjoyed it!"
            else:
                print("don't make report")
                return_details["message"] = return_details["message"] + f". Your match at {round_meta['course_name']} is over. Hope you enjoyed it!"
            



    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        if no_of_players == 2:
            form = CardEntryForm(request.POST, player_a="", player_b="")
        if no_of_players == 3:
            form = CardEntryForm(request.POST, player_a="", player_b="", player_c="")
        if no_of_players == 4:
            form = CardEntryForm(request.POST, player_a="", player_b="", player_c="", player_d="")
        # check whether it's valid:
        if form.is_valid():
            # Update scores incrementing the model field name by the hole_no each time
            setattr(score_instance, "player_a_s{0}".format(hole_no), form.cleaned_data['player_A'])
            setattr(score_instance, "player_b_s{0}".format(hole_no), form.cleaned_data['player_B'])
            setattr(score_instance, "player_c_s{0}".format(hole_no), form.cleaned_data['player_C'] if no_of_players > 2 else 0)
            setattr(score_instance, "player_d_s{0}".format(hole_no), form.cleaned_data['player_D'] if no_of_players > 2 else 0)
            hole_no += 1
            score_instance.save()

            # redirect to same page with increment of hole_no 
            return HttpResponseRedirect(f'/golf/trackmatch/{score_id}/{hole_no}/')

    # if a GET (or any other method) create a blank form
    else:
        if no_of_players == 2:
            form = CardEntryForm(
                player_a = f"A) {str(buddy_queryset[0].buddy_email)[:6]}.. ({score_instance.player_a_course_hcp})",
                player_b = f"B) {str(buddy_queryset[1].buddy_email)[:6]}.. ({score_instance.player_b_course_hcp})"
            )
        elif no_of_players == 3:
                form = CardEntryForm(
                player_a = f"A) {str(buddy_queryset[0].buddy_email)[:6]}.. ({score_instance.player_a_course_hcp})",
                player_b = f"B) {str(buddy_queryset[1].buddy_email)[:6]}.. ({score_instance.player_b_course_hcp})",
                player_c = f"C) {str(buddy_queryset[2].buddy_email)[:6]}.. ({score_instance.player_c_course_hcp})"
                )
        else:
            form = CardEntryForm(
                player_a = f"A {str(buddy_queryset[0].buddy_email)[:6]}.. ({score_instance.player_a_course_hcp}) [{player_dict['player1']['running_totals'][0]}/{player_dict['player1']['running_totals'][1]}/{player_dict['player1']['running_totals'][2]}/{player_dict['player1']['running_totals'][3]}]",
                player_b = f"B {str(buddy_queryset[1].buddy_email)[:6]}.. ({score_instance.player_b_course_hcp}) [{player_dict['player2']['running_totals'][0]}/{player_dict['player2']['running_totals'][1]}/{player_dict['player2']['running_totals'][2]}/{player_dict['player2']['running_totals'][3]}]",
                player_c = f"C {str(buddy_queryset[2].buddy_email)[:6]}.. ({score_instance.player_c_course_hcp})",
                player_d = f"D {str(buddy_queryset[3].buddy_email)[:6]}.. ({score_instance.player_d_course_hcp})"
                )

    if siri and hole_no > 1:
        if makereport:
            print("send email with report")
            # print(return_details["message"])
            # print(format_firstnames_for_report(player_name_list))
            # print(request.user.email)
            # print(stop)
            # Prep Email
            subject = "Handi Cappy Golf Report"
            from_email = 'notrelevant@gmail.com'    # This is totally not relevant - uses the email defined in settings
            # print(score_instance.group)
            # buddies_for_email = Buddy.objects.filter(group = score_instance.group).values_list('buddy_email', flat=True)
            buddies_for_email = CustomUser.objects.filter(id__in = Buddy.objects.filter(group = score_instance.group).values_list('buddy_email', flat=True)).values_list('email', flat=True)
            # print(buddies_for_email2)
            # to_email = [x for x in buddies_for_email ]
            if towho == "Group":
                # to_email = ['gordonlindsay@virginmedia.com']
                to_email = [x for x in buddies_for_email ] 
            else:
                to_email = [str(request.user.email)]     
            context = {
                'round_info': f"{round_meta['course_name']}, on {round_meta['round_date'].strftime('%A %d/%b/%Y')} - Players: {format_firstnames_for_report(player_name_list)}",
                'report': return_details["message"],
                'your_scorecard_url': f"https://kenton.eu.pythonanywhere.com/golf/trackmatch/{round_meta['round_id']}/19/colourize/"
            }
            html_message = render_to_string('email/roundsummary_email.html', context)
            plain_message = return_details["message"]
            message = EmailMultiAlternatives(
                subject = subject,
                body = plain_message,
                from_email = from_email,
                to = to_email
            )
            message.attach_alternative(html_message, "text/html")
            message.send()

            return render(request,"email/email_sent.html", {'email_address': to_email})

            # return HttpResponseRedirect(f'/accounts/sendmail/gordonalindsay@gmail.com/')
            #return render(request, 'golf/card_entry.html', {"player_dict": player_dict, "round_meta": round_meta, "stableford_medal_positions": stableford_medal_positions, "form": form})
        else:
            return JsonResponse(return_details)
    else:
        # print(player_dict)
        # Best holes by player and Bandit of the day ( only calculate on completion of round).
        if hole_no > 18:
            golf_terminology = {
                -3: "an Albatross", 
                -2: "an Eagle",
                -1: "a Birdie",
                0: "a Par",
                1: "a Bogey",
                2: "a Double Bogey",
                3: "a Triple Bogey",
                4: "a Quadruple Bogey",
                5: "a Quintuple Bogey",
                6: "a Sextuple Bogey",
                7: "a Septuple Bogey",
                8: "a Octuple Bogey"
            }
            result = find_best_hole(player_dict)
            # print("OVERALL WINNER:")
            winner = result['overall_winner']
            # print(f"{winner['player']} scored {winner['score_vs_par']} vs par on hole {winner['hole']}")
            round_meta["bandit_of_the_day"] = f"{winner['player']} scored {golf_terminology[winner['score_vs_par']]} on hole {winner['hole']}" 
            # print("\nEACH PLAYER'S BEST HOLE:")
            round_meta["player_best_hole"] = []
            for player, best in result['player_best_holes'].items():
                # print(f"{player}: {best['score_vs_par']} vs par on hole {best['hole']} (score: {best['gross_score']}, par: {best['par']})")
                round_meta["player_best_hole"].append(best['hole'])
            # print(round_meta["player_best_hole"])

            # Create a string for the adjusted scores - to be used in the page button <a href=> tag
            round_meta["adjusted_scores_string"] = get_adjusted_scores_string(player_dict)
            # print(round_meta["adjusted_scores_string"])
        return render(request, 'golf/card_entry.html', {"player_dict": player_dict, "round_meta": round_meta, "stableford_medal_positions": stableford_medal_positions, "form": form})

class CardSetupView2(FormView):

    template_name = 'golf/card_entry.html'
    form_class = CardInitialForm
    success_url = '/thanks/'

    def get_queryset(self, **kwargs):
       qs = super().get_queryset(**kwargs)
       print(qs)
       return qs.filter(group = self.kwargs.get("group"))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = GolfGroup.objects.filter(id = self.kwargs.get("group") )
        # print(context['group'])
        return context

    def get_form_kwargs(self):
        kwargs = super(CardInitialView, self).get_form_kwargs()
        match_buddies = Buddy.objects.filter(group = self.kwargs.get("group") )
        # print(match_buddies)
        # print(len(match_buddies))
        # for buddy in match_buddies:
            # print(buddy.buddy_email)
        kwargs['player_a'] = str(match_buddies[0])
        kwargs['player_b'] = str(match_buddies[1])
        if (len(match_buddies) == 3):
            kwargs['player_c'] = str(match_buddies[2])
        if (len(match_buddies) == 4):
            kwargs['player_c'] = str(match_buddies[2])
            kwargs['player_d'] = str(match_buddies[3])

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        pass
        return super().form_valid(form)



class CardInitialView(FormView):

    template_name = 'golf/card_initial.html'
    form_class = CardInitialForm
    # success_url = '/thanks/'

    def get_queryset(self, **kwargs):
       qs = super().get_queryset(**kwargs)
       print(qs)
       return qs.filter(group = self.kwargs.get("group"))
    
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['group'] = GolfGroup.objects.filter(id = self.kwargs.get("group") )
    #     print(context['group'])
    #     return context

    def get_form_kwargs(self):
        from datetime import date
        today = date.today()
        kwargs = super(CardInitialView, self).get_form_kwargs()
        # golf_group_obj = GolfGroup.objects.filter(id = self.kwargs.get("group") )
        match_buddies = Buddy.objects.filter(group = self.kwargs.get("group") )
        # print(match_buddies)
        # print(len(match_buddies))
        buddy_hcps = []         # list of player handicaps to pass to data entry page
        for buddy in match_buddies:
            # print(buddy.buddy_email, buddy.buddy_email.id, calculate_handicap_on_date(today, buddy.buddy_email.id)[1] )
            # buddy_hcps.append(buddy.id)
            buddy_hcps.append(calculate_handicap_on_date(today, buddy.buddy_email.id)[1])
        # print("Buddy hcps", buddy_hcps)
        # CustomUser.objects.filter(email=str(match_buddies[0])[0].firstname
        # CustomUser.objects.filter(email=player.buddy_email)[0].firstname
        kwargs['no_of_players'] = len(match_buddies)
        # kwargs['player_a'] = "<p> </p>" + str(match_buddies[0]) + "<br> Course Hcp"
        kwargs['player_a'] = "<p> </p>" + str(CustomUser.objects.filter(email=match_buddies[0])[0].firstname) + " (" + str(buddy_hcps[0]) + ")<br> Course Hcp"
        kwargs['player_b'] = "<p> </p>" +  str(str(CustomUser.objects.filter(email=match_buddies[1])[0].firstname)) +  " (" + str(buddy_hcps[1]) + ")<br> Course Hcp"
        if (len(match_buddies) == 3):
            kwargs['player_c'] = "<p> </p>" +  str(str(CustomUser.objects.filter(email=match_buddies[2])[0].firstname)) +  " (" + str(buddy_hcps[2]) + ")<br> Course Hcp"
        if (len(match_buddies) == 4):
            kwargs['player_c'] = "<p> </p>" +  str(str(CustomUser.objects.filter(email=match_buddies[2])[0].firstname)) +  " (" + str(buddy_hcps[2]) + ")<br> Course Hcp"
            kwargs['player_d'] = "<p> </p>" +  str(str(CustomUser.objects.filter(email=match_buddies[3])[0].firstname)) +  " (" + str(buddy_hcps[3]) + ")<br> Course Hcp"

        
        return kwargs

    def form_valid(self, form):
        match_buddies = Buddy.objects.filter(group = self.kwargs.get("group"))
        no_of_players = len(match_buddies)
        course_obj = Course.objects.get(id = form.cleaned_data['course'])
        print("Form valid")
        score_instance = Score.objects.create(course = course_obj,
                      no_of_players = no_of_players,
                      group = match_buddies[0].group,
                      player_a = match_buddies[0].buddy_email,
                      player_b = match_buddies[1].buddy_email,
                      player_c = match_buddies[2].buddy_email if no_of_players > 2 else match_buddies[0].buddy_email,
                      player_d = match_buddies[3].buddy_email if no_of_players > 3 else match_buddies[0].buddy_email,
                      date = form.cleaned_data["date"],
                      player_a_course_hcp = form.cleaned_data['player_A'],
                      player_b_course_hcp = form.cleaned_data['player_B'],
                      player_c_course_hcp = form.cleaned_data['player_C'],
                      player_d_course_hcp = form.cleaned_data['player_D'],
                      player_a_score_target = set_player_target_round_score(course_obj.id, CustomUser.objects.get(email = match_buddies[0].buddy_email).id),
                      player_b_score_target = set_player_target_round_score(course_obj.id, CustomUser.objects.get(email = match_buddies[1].buddy_email).id),
                      player_c_score_target = set_player_target_round_score(course_obj.id, CustomUser.objects.get(email = match_buddies[2].buddy_email).id) if no_of_players > 2 else 0,
                      player_d_score_target = set_player_target_round_score(course_obj.id, CustomUser.objects.get(email = match_buddies[3].buddy_email).id) if no_of_players > 3 else 0
                      )
        print(score_instance.id)
        # return super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url(score_instance.id))
    
    def get_success_url(self, score_id=None):
        print(score_id)
        return reverse('trackmatch', kwargs={'score_id': score_id, 'hole_no': 1})
    
class ScoreListView(ListView):
    model = Score
    template_name = 'golf/score_list.html'
    ordering = ['-date']
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the groups to template where current user is the group admin and number of members is greater than 1
        list_of_groups_with_min_two_members = []
        groups_user_is_the_admin = GolfGroup.objects.filter(administrator = self.request.user )
        for group in groups_user_is_the_admin:
            if Buddy.objects.filter(group = group).count() > 1:
                list_of_groups_with_min_two_members.append(group)
        # print(list_of_groups_with_min_two_members)
        # print(list(set(groups_user_is_the_admin) & set(list_of_groups_with_min_two_members)))
        context['groups_which_can_start_rounds'] = list(set(groups_user_is_the_admin) & set(list_of_groups_with_min_two_members))
        return context

class ScoreDeleteView(DeleteView):
    model = Score
    success_url = "/golf/list_scores/"
    template_name = "golf/score_confirm_delete.html"
    


    
@login_required
def displaymaxhole(request, score_id):
    # Get the maximum number of holes scored/saved and redirect to that url page
    score_instance = Score.objects.get(id = score_id)

    # Check through the fields to find the first blank against Player A
    hole_id = 19
    for i in range(1, 19):
        if getattr(score_instance,"player_a_s{0}".format(i)) is None:
            hole_id = i
            break

    print(hole_id)
    return HttpResponseRedirect("/golf/trackmatch/{0}/{1}/".format(score_id,hole_id))

@login_required
def courses_played(request, player_id):
    player_obj_id = CustomUser.objects.get(pk = player_id)
    rounds_entered_objs = Round.objects.filter(player = player_obj_id)
    round_buttons = []
    for r in rounds_entered_objs:
        round_buttons.append([r.course.id,r.course.name]) if [r.course.id,r.course.name] not in round_buttons else round_buttons 

    return render(request, 'golf/stats_menu.html', {"round_buttons": round_buttons, "player_id": player_id})

def set_player_target_round_score(course_id, player_id):
    player_obj_id = CustomUser.objects.get(pk = player_id)
    course = Course.objects.get(id = course_id)
     # Get target handicap differential
    last_20_rounds = Round.objects.filter(player = player_obj_id).order_by('-date')[:20]    # Get last 20 rounds ( or less )
    num_of_rounds_played = len(last_20_rounds)                                              # Actual rounds played
    if num_of_rounds_played < 3:
        target_round_score = 0
    else:
        if num_of_rounds_played > 20:
            calculation_factor = 20
        else:
            calculation_factor = DiffAjustment.objects.get(num_of_scores = num_of_rounds_played).calculation_factor       # Get relevant diff_adjustment record

        last_20_rounds_list = [r.handicap_differential for r in last_20_rounds]                 # List the hcp differentials
        # print("round_scores", [r.score for r in last_20_rounds] )
        rounds_that_count = sorted([r.handicap_differential for r in last_20_rounds])[:calculation_factor]  # List of rounds that count
        target_hcp_differential = sorted(rounds_that_count, reverse=True)[0] - 0.5              # Get the highest hcp differential and subtract 0.5 to get target
        # print("last_20_rounds_list", last_20_rounds_list)
        # print("rounds_that_count", rounds_that_count)
        # print("sorted best8", sorted(best_8, reverse=True))
        # print("target_hcp_differential", target_hcp_differential )

        target_round_score = ((course.slope_rating / 113) * target_hcp_differential) + course.course_rating
        # print("target_round_score", target_round_score)
    return target_round_score

def calculate_stableford_score(strokes, indexes, pars, player_hcp):
    stableford_points = 0

    for hole_strokes, hole_index, hole_par in zip(strokes, indexes, pars):
        if player_hcp <= 18 and hole_index <= player_hcp:    # Player gets 1 stroke
            net_score = hole_strokes - 1
        else:
            net_score = hole_strokes
            
        if player_hcp > 18 and player_hcp <=36:
            if hole_index <= player_hcp - 18:
                net_score = hole_strokes - 2
            else:
                net_score = hole_strokes - 1
                
        if player_hcp > 36 and player_hcp <=54:
            if hole_index <= player_hcp - 36:
                net_score = hole_strokes - 3
            else:
                net_score = hole_strokes - 2
                
        # print(hole_strokes, net_score)
        
        if net_score - hole_par == 0:
            stableford_points += 2
        elif net_score - hole_par == 1:
            stableford_points += 1
        elif net_score - hole_par == -1:
            stableford_points += 3
        elif net_score - hole_par == -2:
            stableford_points += 4
        elif net_score - hole_par == -3:
            stableford_points += 4
        else:
            stableford_points += 0

        # print(hole_par, hole_strokes, net_score, stableford_points)
    return stableford_points


# @login_required - removed for Siri access
def get_course_stats(request, course_id, player_id, extraparam = ''):
    # Initialise the stats best/worse hole variables ( to avoid crash when there are stats for the round but not the scorecard )
    cursed_hole = 0
    bandit_hole = 0

    if extraparam[:4] == "Siri":
        siri = True
    else:
        siri = False
    if extraparam[:8] == "Detailed":
        detailed_stats = True
    else:
        detailed_stats = False
    course = Course.objects.get(id = course_id)
    course_name = course.name
    player_obj_id = CustomUser.objects.get(pk = player_id)

    rounds = Round.objects.filter(course = course, player = player_obj_id)
    # print("stats for ",player_obj_id)
    course_stats = Score.objects.filter(course = course_id).order_by('-date')
    round_matrix = []
    score_hcp_matrix = []
    for round_stat in course_stats:
        round_score = []
        if round_stat.player_a == player_obj_id:
            if round_stat.player_a_s1 is not None and round_stat.player_a_s1 != 0:
                for i in range(1,19):
                   if getattr(round_stat,f"player_a_s18") is not None and getattr(round_stat,f"player_a_s18") != 0: round_score.append(getattr(round_stat,f"player_a_s{i}"))
                if getattr(round_stat,f"player_a_s18") is not None and getattr(round_stat,f"player_a_s18") != 0:
                    round_matrix.append(round_score)
                    score_hcp_matrix.append(round_stat.player_a_course_hcp)
            # print(round_stat.id, round_stat, "playera", round_score)        

        if round_stat.player_b == player_obj_id:
            if round_stat.player_b_s1 is not None and round_stat.player_b_s1 != 0:
                for i in range(1,19):
                    if getattr(round_stat,f"player_b_s18") is not None and getattr(round_stat,f"player_b_s18") != 0: round_score.append(getattr(round_stat,f"player_b_s{i}"))
                if getattr(round_stat,f"player_b_s18") is not None and getattr(round_stat,f"player_b_s18") != 0:
                    round_matrix.append(round_score)
                    score_hcp_matrix.append(round_stat.player_b_course_hcp)
            # print(round_stat.id, round_stat, "playerb", round_score)

        if round_stat.player_c == player_obj_id:
            if round_stat.player_c_s1 is not None and round_stat.player_c_s1 != 0:
                for i in range(1,19):
                    if getattr(round_stat,f"player_c_s18") is not None and getattr(round_stat,f"player_c_s18") != 0: round_score.append(getattr(round_stat,f"player_c_s{i}"))
                if getattr(round_stat,f"player_c_s18") is not None and getattr(round_stat,f"player_c_s18") != 0:
                    round_matrix.append(round_score)
                    score_hcp_matrix.append(round_stat.player_c_course_hcp)
            # print(round_stat.id, round_stat, "playerc", round_score)

        if round_stat.player_d == player_obj_id:
            if round_stat.player_d_s1 is not None and round_stat.player_d_s1 != 0:
                for i in range(1,19):
                    if getattr(round_stat,f"player_d_s18") is not None and getattr(round_stat,f"player_d_s18") != 0: round_score.append(getattr(round_stat,f"player_d_s{i}"))
                if getattr(round_stat,f"player_d_s18") is not None and getattr(round_stat,f"player_d_s18") != 0:
                    round_matrix.append(round_score)
                    score_hcp_matrix.append(round_stat.player_d_course_hcp)
            # print(round_stat.id, round_stat, "playerd", round_score)
    # print("round_matrix", round_matrix)
    if len(round_matrix) > 0: most_recent_round = round_matrix[0]     # Most recent round completed is the first entry in matrix list
    # print("most_recent_round", most_recent_round)
    if len(round_matrix) == 0:
        # print(f"No Completed Scorecards for {Course.objects.get(id = course_id)}")
        no_of_completed_scorecards = 'None'
        rotated_stats_scorecard = []
        calculated_round_best_total = 0
        calculated_round_worst_total = 0
    else:
        rotated_round_matrix = [list(row) for row in zip(*round_matrix)]
        # print(" ")
        # print(rotated_round_matrix)
        # print(" ")
        # print(rotated_round_matrix[2])
        # print(" ")
        # print("Total number of scorecards",len(round_matrix))
        no_of_completed_scorecards = len(round_matrix)
        # print(" ")
        # print("Hole3 average",sum(rotated_round_matrix[2])/len(rotated_round_matrix[2]))
        # print(" ")
        # print("Hole3 max",max(rotated_round_matrix[2]))
        # print(" ")
        # print("Hole3 min",min(rotated_round_matrix[2]))
        calculated_round_worst = []
        calculated_round_best = []
        calculated_round_average = []
        for i in range(0,18):
            calculated_round_worst.append(max(rotated_round_matrix[i]))
            calculated_round_best.append(min(rotated_round_matrix[i]))
            calculated_round_average.append(sum(rotated_round_matrix[i])/len(rotated_round_matrix[i]))
        calculated_round_best_total = sum(calculated_round_best)
        calculated_round_worst_total = sum(calculated_round_worst)
        # print("calculated_round_worst_total", sum(calculated_round_worst))
        # print(" ")
        # print("calculated_round_best_total", sum(calculated_round_best))
        # print(" ")
        # print("calculated_round_average total", round(sum(calculated_round_average)))

        # Get Course Par and SI
        course_holes = []
        course_par = []
        course_si = []
        for i in range(1,19):
            course_holes.append(i)
            course_par.append(getattr(course,f"hole{i}par"))
            course_si.append(getattr(course,f"hole{i}SI"))
        # print("course_holes",course_holes )
        # print("course_par", course_par)
        # print("course_si", course_si)
        # print("calculated round average", calculated_round_average)
        # print(round_matrix)

        ## Code for Personal SI

        # Calculate differences between player's average and course par
        differences = [round(avg - par, 1) for avg, par in zip(calculated_round_average, course_par)]

        # Create list of (hole_number, difference) tuples
        indexed_differences = [(i+1, diff) for i, diff in enumerate(differences)]

        # Sort by difficulty (higher difference = more difficult = lower SI)
        # For ties, earlier holes in the original list get lower SI
        sorted_by_difficulty = sorted(indexed_differences, key=lambda x: (-x[1], x[0]))

        # Assign stroke index values (1-18) based on sorted difficulty
        personal_si = [0] * 18
        for i, (hole_num, _) in enumerate(sorted_by_difficulty):
            personal_si[hole_num-1] = i+1  # i+1 gives values 1-18, hole_num-1 adjusts for 0-based indexing

        # print("Differences by hole:", differences)
        # print("Personal Stroke Index:", personal_si)
        # print("Course Stroke Index:", course_si)


        si_differences = [personal_si[i] - course_si[i] for i in range(len(personal_si))]

        ## End of code for Persoanl SI

        # Bandit and Cured hole functionaility

        # Find max difference
        max_diff = max(si_differences)
        max_indices = [i for i, diff in enumerate(si_differences) if diff == max_diff]

        # If tie, get index with lowest csi value
        if len(max_indices) > 1:
            max_index = min(max_indices, key=lambda i: course_si[i])
        else:
            max_index = max_indices[0]

        # Find min difference
        min_diff = min(si_differences)
        min_indices = [i for i, diff in enumerate(si_differences) if diff == min_diff]

        # If tie, get index with highest csi value
        if len(min_indices) > 1:
            min_index = max(min_indices, key=lambda i: course_si[i])
        else:
            min_index = min_indices[0]

        # print(f"Max difference: {max_diff} at index {max_index}")
        # print(f"Min difference: {min_diff} at index {min_index}")
        cursed_hole = min_index + 1
        bandit_hole = max_index + 1

        # End of Bandit and Cured hole functionaility
        


        # Get list of stableford scores
        # stableford_scores = []
        # for count, each_single_round in enumerate(round_matrix):
            # print(each_single_round, course_si, score_hcp_matrix, score_hcp_matrix[count])
            # stableford_scores.append(calculate_stableford_score(each_single_round, course_si, course_par, score_hcp_matrix[count]))
        # print(stableford_scores)
        # print(round(sum(stableford_scores) / len(stableford_scores),2)) 
        
        if extraparam[:8] == "Detailed":
            # Get the Detailed Hole Stats (No. of Eagles, Birdies etc.)
            # Initialize lists for each score type
            eagles = [0] * 18
            birdies = [0] * 18
            pars_count = [0] * 18
            bogeys = [0] * 18
            double_bogeys = [0] * 18
            triple_bogeys = [0] * 18
            disasters = [0] * 18

            # Initialize total counters
            total_eagles = 0
            total_birdies = 0
            total_pars = 0
            total_bogeys = 0
            total_double_bogeys = 0
            total_triple_bogeys = 0
            total_disasters = 0

            for hole_idx in range(18):
                hole_par = course_par[hole_idx]
                
                # For each hole, get the 5 rounds/players
                for round_idx in range(len(rotated_round_matrix[hole_idx])):
                    score = rotated_round_matrix[hole_idx][round_idx]
                    diff = score - hole_par
                    
                    if diff == -2:
                        eagles[hole_idx] += 1
                        total_eagles += 1
                    elif diff == -1:
                        birdies[hole_idx] += 1
                        total_birdies += 1
                    elif diff == 0:
                        pars_count[hole_idx] += 1
                        total_pars += 1
                    elif diff == 1:
                        bogeys[hole_idx] += 1
                        total_bogeys += 1
                    elif diff == 2:
                        double_bogeys[hole_idx] += 1
                        total_double_bogeys += 1
                    elif diff == 3:
                        triple_bogeys[hole_idx] += 1
                        total_triple_bogeys += 1
                    elif diff > 3:  # Worse than triple bogey = disaster
                        disasters[hole_idx] += 1
                        total_disasters += 1


            # print("Eagles:", eagles, total_eagles)
            # print("Birdies:", birdies, total_birdies)
            # print("Pars:", pars_count, total_pars)
            # print("bogeys:", bogeys, total_bogeys)
            # print("doubles:", double_bogeys, total_double_bogeys)
            # print("triples:", triple_bogeys, total_triple_bogeys)
            # print("disasters:", disasters, total_disasters)

            hole_score_type_total_list = [total_eagles, total_birdies, total_pars, total_bogeys, total_double_bogeys, total_triple_bogeys, total_disasters]

            detailed_hole_breakdown = [course_holes, course_par, course_si, eagles, birdies, pars_count, bogeys, double_bogeys, triple_bogeys, disasters]
            rotated_detailed_hole_breakdown = [list(row) for row in zip(*detailed_hole_breakdown)]

        else:
            # Build the data for the high level stats scorecard
            stats_scorecard = [course_holes, course_par, course_si, calculated_round_best, calculated_round_worst, calculated_round_average, most_recent_round, personal_si]
            # print("stats_scorecard", stats_scorecard)
            rotated_stats_scorecard = [list(row) for row in zip(*stats_scorecard)]
            # print(rotated_stats_scorecard)
            # print("rotated_stats_scorecard", rotated_stats_scorecard )
    if siri:
        print("Siri mode")
        if len(extraparam) == 5:                    # Hole 1-9
            current_hole_no = int(extraparam[-1:])
        else:                                       # Hole 10-18
            current_hole_no = int(extraparam[-2:])
        return_details = {}
        return_details["message"] = ""
        return_details["message"] = return_details["message"] + f"Your best cumulative score at {course_name} is {calculated_round_best_total} and your worst is {calculated_round_worst_total}. "
        return_details["message"] = return_details["message"] + f"Hole {current_hole_no} Your best at hole {current_hole_no} is {min(rotated_round_matrix[current_hole_no - 1])}"
        return JsonResponse(return_details)
    elif detailed_stats:
        return render(request, 'golf/stats_detail2.html', {"course": course,
                                                    "no_of_rounds": rounds.count(),
                                                    "best_round": rounds.aggregate(min_value=Min('score'))['min_value'],
                                                    "calculated_round_best_total": calculated_round_best_total,
                                                    "worst_round": rounds.aggregate(max_value=Max('score'))['max_value'],
                                                    "calculated_round_worst_total": calculated_round_worst_total,
                                                    "average_round": round(rounds.aggregate(average_value=Avg('score'))['average_value'],2),
                                                    "no_of_completed_scorecards": no_of_completed_scorecards,
                                                    "hole_score_type_total_list": hole_score_type_total_list,
                                                    "rotated_detailed_hole_breakdown": rotated_detailed_hole_breakdown,
                                                    "course_id": course_id,
                                                    "player_id": player_id })

    else:
        return render(request, 'golf/stats_detail.html', {"course": course,
                                                    "no_of_rounds": rounds.count(),
                                                    "best_round": rounds.aggregate(min_value=Min('score'))['min_value'],
                                                    "calculated_round_best_total": calculated_round_best_total,
                                                    "worst_round": rounds.aggregate(max_value=Max('score'))['max_value'],
                                                    "calculated_round_worst_total": calculated_round_worst_total,
                                                    "average_round": round(rounds.aggregate(average_value=Avg('score'))['average_value'],2),
                                                    "no_of_completed_scorecards": no_of_completed_scorecards,
                                                    "stats_scorecard": rotated_stats_scorecard,
                                                    "course_id": course_id,
                                                    "player_id": player_id,
                                                    "cursed_hole": cursed_hole,
                                                    "bandit_hole": bandit_hole })


# Functions to build Handicap Tracking capability
    
def get_list_of_rounds_with_valid_hcp(player_id):
    min_number_of_rounds_required = 3   # Set to 3
    # Get all the rounds for player sorted by date decending
    all_round_objs = Round.objects.filter(player = player_id).order_by('-date')
    oldest_round_to_include = int(all_round_objs.count()) - min_number_of_rounds_required
    # print(oldest_round_to_include)
    rounds_list_to_include = []
    for index, round_obj in enumerate(all_round_objs):
        # print(index, round_obj.id, round_obj.date, "yes" if oldest_round_to_include >= index else "no")
        if oldest_round_to_include >= index: rounds_list_to_include.append(round_obj.date)
    # print("rounds to include", rounds_list_to_include)
    return rounds_list_to_include

def calculate_handicap_on_date(round_date, player_id):
    round_obj = Round.objects.filter(player = player_id, date__lte = round_date ).order_by('-date')[0:20] # Most recent 20 rounds
    num_score_differentials = len(round_obj)
    if(num_score_differentials >= 3 and num_score_differentials <= 20):
        diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = num_score_differentials )[0]
    elif(num_score_differentials > 20):
        diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = 20 )[0]
    else:       # Less than 3 rounds so return 0 and exit
        return (round_date, 0)
    round_obj_bylowest = sorted(round_obj, key=lambda o: o.handicap_differential)[:diffadjustment_obj.calculation_factor]
    # round_obj_bylowest = sorted(round_obj, key=lambda o: o.handicap_differential)[:8]  
    # print(round_obj_bylowest)
    # lowest_round_id_list = [ o.id for o in round_obj_bylowest ]
    calculated_handicap = round(sum([i.handicap_differential for i in round_obj_bylowest]) / len(round_obj_bylowest) + diffadjustment_obj.adjustment,1)
    # calculated_handicap = round(sum([i.handicap_differential for i in round_obj_bylowest]) / len(round_obj_bylowest),1)
    return (round_date, calculated_handicap)

def build_handicap_list_over_time(rounds, player_id):
    handicap_list_over_time = []
    for round in rounds:
        handicap_list_over_time.append(calculate_handicap_on_date(round, player_id))
    return handicap_list_over_time

def average_per_month(data):
    monthly_averages = defaultdict(list)
    
    # Group data by month
    for date, value in data:
        month_key = (date.year, date.month)
        monthly_averages[month_key].append(value)
    
    # Calculate averages for each month
    result = {}
    previous_avg = None
    current_year, current_month = datetime.datetime.now().year, datetime.datetime.now().month
    for year in range(min(monthly_averages.keys())[0], current_year + 1):
        end_month = 12 if year < current_year else current_month
        for month in range(1, end_month + 1):
            month_key = (year, month)
            values = monthly_averages.get(month_key, [])
            if values:
                avg_value = sum(values) / len(values)
                result[datetime.date(year, month, 1)] = avg_value
                previous_avg = avg_value
            elif previous_avg is not None:
                result[datetime.date(year, month, 1)] = previous_avg
                
    return result

class UserListView(ListView):
    model = CustomUser
    # ordering = ['-date']
    paginate_by = 10

class UserUpdateView(UpdateView):
    model = CustomUser
    form_class = UserForm
    success_url = "/golf/list_users/"
    template_name = "accounts/user_form.html"

# Functions to do automatic posting of adjusted_scores from a Scorecard to the Round table
def create_rounds_view(request, score_id):
    try:
        # Get scores from query params: ?scores=82,79,95
        scores_param = request.GET.get('scores', '')
        score_list = [int(score) for score in scores_param.split(',') if score]
        rounds = create_round_records(score_id, *score_list)
        # Update scores_posted to True
        Score.objects.filter(id=score_id).update(scores_posted=True)
        return render(request, 'golf/scores_posted_success.html')
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def create_round_records(score_id, *adjusted_scores):
    # Convert to list and integers
    adjusted_scores = [int(score) for score in adjusted_scores]
    
    # Get the Score record
    score = Score.objects.get(id=score_id)
    
    # Get course data for calculations
    course = score.course
    par = course.par
    course_rating = course.course_rating
    slope_rating = course.slope_rating
    
    # Get players based on no_of_players
    players = []
    for i in range(score.no_of_players):
        if i == 0 and score.player_a:
            players.append(score.player_a)
        elif i == 1 and score.player_b:
            players.append(score.player_b)
        elif i == 2 and score.player_c:
            players.append(score.player_c)
        elif i == 3 and score.player_d:
            players.append(score.player_d)
    
    # Create Round records
    rounds_created = []
    for i, player in enumerate(players):
        # Check if player is REGULAR type - ignore the "SINGLE" useforsingleround@one.com user record
        if player.player_type == 'REGULAR':
            # Calculate net_score
            net_score_value = adjusted_scores[i] - par
            net_score = "+" + str(net_score_value) if net_score_value > 0 else str(net_score_value)
            
            # Calculate handicap_differential
            handicap_diff = round((adjusted_scores[i] - course_rating) * 113 / slope_rating, 1)
            
            # Create Round record
            round_record = Round.objects.create(
                player=player,
                date=score.date,
                course=score.course,
                score=adjusted_scores[i],
                net_score=net_score,
                handicap_differential=handicap_diff
            )
            rounds_created.append(round_record)

            # print("player", player)
            # print("date", score.date)
            # print("course", course)
            # print("score", adjusted_scores[i])
            # print("net", net_score)
            # print("handicap_diff",handicap_diff) 
    
    return rounds_created


def card_individual(request, score_id, player_id=None):
    # Get the score record
    score = get_object_or_404(Score, id=score_id)
    course = score.course
    
    # Build hole par and SI data
    hole_pars = [getattr(course, f'hole{i}par') for i in range(1, 19)]
    hole_sis = [getattr(course, f'hole{i}SI') for i in range(1, 19)]
    
    # Build all players info (no scores) based on no_of_players
    all_players = []
    for i, player in enumerate(['a', 'b', 'c', 'd']):
        if i < score.no_of_players:  # Only include based on no_of_players
            player_obj = getattr(score, f'player_{player}')
            if player_obj:
                all_players.append({
                    'firstname': player_obj.firstname,
                    'id': player_obj.id,
                    'player_letter': player
                })
    
    # Build all player scores and totals
    all_player_scores = []
    all_player_score_totals = []
    
    for i, player in enumerate(['a', 'b', 'c', 'd']):
        if i < score.no_of_players:
            player_obj = getattr(score, f'player_{player}')
            if player_obj:
                scores = [getattr(score, f'player_{player}_s{i}') for i in range(1, 19)]
                
                # Create tuples with score and highlight class
                score_tuples = []
                for hole_idx, player_score in enumerate(scores):
                    if player_score is not None and player_score != 0:
                        hole_par = getattr(course, f'hole{hole_idx + 1}par')
                        if player_score < hole_par:
                            highlight_class = "highlight-circle"
                        elif player_score > hole_par:
                            highlight_class = "highlight-square"
                        else:
                            highlight_class = "highlight-none"
                        score_tuples.append((player_score, highlight_class))
                    else:
                        score_tuples.append(("", "highlight-none"))
                
                all_player_scores.append(score_tuples)
                
                # Calculate totals for this player
                valid_scores = [s for s in scores if s is not None]
                front_nine = [s for s in scores[:9] if s is not None]
                back_nine = [s for s in scores[9:] if s is not None]
                
                all_player_score_totals.append({
                    'front_nine': sum(front_nine),
                    'back_nine': sum(back_nine),
                    'total': sum(valid_scores)
                })
                
                # Calculate over/under par string
                total_score = sum(valid_scores)
                par_difference = total_score - course.par
                if par_difference > 0:
                    over_under_par = f"+{par_difference}"
                elif par_difference < 0:
                    over_under_par = str(par_difference)  # Already has minus sign
                else:
                    over_under_par = "Level"
                
                all_player_score_totals[-1]['over_under_par'] = over_under_par
    
    # Set legacy variables for backward compatibility
    player_scores = [t[0] for t in all_player_scores[0]] if all_player_scores else []
    player_score_totals = all_player_score_totals[0] if all_player_score_totals else {}
    
    holes_data = {
        'pars': hole_pars,
        'sis': hole_sis
    }
    
    # Calculate totals for each player
    player_totals = {}
    for player in ['a', 'b', 'c', 'd']:
        player_obj = getattr(score, f'player_{player}')
        if player_obj:  # Only calculate if player exists
            total_score = sum(
                getattr(score, f'player_{player}_s{hole}') or 0 
                for hole in range(1, 19)
            )
            player_totals[f'player_{player}'] = {
                'name': player_obj.get_full_name() or player_obj.username,
                'handicap': getattr(score, f'player_{player}_course_hcp'),
                'total_score': total_score,
                'target': getattr(score, f'player_{player}_score_target')
            }
    
    context = {
        'score': score,
        'score_id': score.id,
        'course': course,
        'holes_data': holes_data,
        'player_scores': player_scores,
        'player_score_totals': player_score_totals,
        'all_player_scores': all_player_scores,
        'all_player_score_totals': all_player_score_totals,
        'all_players': all_players,
        'number_of_players': score.no_of_players,
        'player_totals': player_totals,
        'front_nine_par': sum(getattr(course, f'hole{i}par') for i in range(1, 10)),
        'back_nine_par': sum(getattr(course, f'hole{i}par') for i in range(10, 19)),
        'total_par': course.par
    }

    # print(score)
    # print(course)
    # print(holes_data)
    # print(player_scores)
    # print(player_score_totals)
    # print(all_player_scores)
    # print(all_player_score_totals)

    # print(all_players)
    # print(player_totals)
    
    return render(request, 'golf/card_individual.html', context)



