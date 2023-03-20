# golf/views.py
from django.db.models import Avg, Min, Max, Count
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.urls import reverse
from django.http import HttpResponseRedirect
from random import randrange

from .forms import CourseForm, RoundForm, GolfGroupForm, BuddyForm, CardInitialForm, CardEntryForm
from .models import *

from django.shortcuts import render
# from django.db.models import Sum
from django.http import JsonResponse
# from django.db.models import F, Func, Value, CharField
# from django.db.models.functions import Concat

from django.contrib.auth.decorators import login_required
import json

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
    def get_queryset(self, **kwargs):
        qs = super().get_queryset(**kwargs)
        # Filter rounds for user (default) or for player if id passed as parameter (for buddy groups)
        player_id = self.request.user if len(self.request.GET.keys()) == 0 else self.request.GET.get('p')
        player_qs = qs.filter(player=player_id)
        return player_qs

    # Calculate net_score from round and course join and pass as context to template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Filter rounds for user (default) or for player if id passed as parameter (for buddy groups)
        player_id = self.request.user if len(self.request.GET.keys()) == 0 else self.request.GET.get('p')
        # round_obj = self.object
        round_obj = Round.objects.filter(player = player_id ).order_by('-date')[0:20] # Most recent 20 rounds
        context['object'] = round_obj
        # Determine if weighting factor needs to be applied
        num_score_differentials = len(Round.objects.filter(player = player_id ))
        context['total_number_of_rounds'] = num_score_differentials
        if(num_score_differentials >= 3 and num_score_differentials <= 20):
            diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = num_score_differentials )[0]
        elif(num_score_differentials > 20):
            diffadjustment_obj = DiffAjustment.objects.filter(num_of_scores = 20 )[0]
        # List that is passed to template with ID's of rounds which make up the handicap
        lowest_round_id_list = []
        context['player'] = round_obj[0].player if num_score_differentials > 0 else ''

        if(num_score_differentials < 3):
            context['message'] = 'Minimum of 3 rounds is required to calculate handicap'

        elif(num_score_differentials == 3 or num_score_differentials == 4 or num_score_differentials == 5):
            round_obj_bylowest = Round.objects.filter(player = player_id ).order_by('handicap_differential')[:1]
            for r in round_obj_bylowest:
                lowest_round_id_list.append(r.id)
            context['calculated_handicap'] = round(round_obj_bylowest[0].handicap_differential + diffadjustment_obj.adjustment,1)
            context['number_of_lowest_rounds'] = "1"
            context['lowest_round_id_list'] = lowest_round_id_list

        elif(num_score_differentials == 6 ):
            round_obj_bylowest = Round.objects.filter(player = player_id ).order_by('handicap_differential')[:diffadjustment_obj.calculation_factor]
            for r in round_obj_bylowest:
                lowest_round_id_list.append(r.id)
            calculated_handicap = round_obj_bylowest.aggregate(Avg('handicap_differential'))
            context['calculated_handicap'] = round(calculated_handicap.get('handicap_differential__avg') + diffadjustment_obj.adjustment,1)
            context['number_of_lowest_rounds'] = str(diffadjustment_obj.calculation_factor)
            context['lowest_round_id_list'] = lowest_round_id_list

        elif(num_score_differentials > 20):
            lowest_handicap_diff_list = []
            round_obj_bylowest = Round.objects.filter(player = player_id ).order_by('handicap_differential')
            stop_loop_at = 8
            count = 0
            for r in round_obj_bylowest:
                print(count)
                if r in round_obj:
                    lowest_round_id_list.append(r.id)
                    lowest_handicap_diff_list.append(r.handicap_differential)
                    count = count + 1
                if count == stop_loop_at:
                    break
            print(lowest_round_id_list)
            print(lowest_handicap_diff_list)
            calculated_handicap = sum(lowest_handicap_diff_list) / len(lowest_handicap_diff_list)
            context['calculated_handicap'] = round(calculated_handicap,1)
            context['number_of_lowest_rounds'] = "8"
            context['lowest_round_id_list'] = lowest_round_id_list
            context['total_number_of_rounds'] = 20

        else:   # Greater than 6, less than 20
            round_obj_bylowest = Round.objects.filter(player = player_id ).order_by('handicap_differential')[:diffadjustment_obj.calculation_factor]
            for r in round_obj_bylowest:
                lowest_round_id_list.append(r.id)
            calculated_handicap = round_obj_bylowest.aggregate(Avg('handicap_differential'))
            context['calculated_handicap'] = round(calculated_handicap.get('handicap_differential__avg'),1)
            context['number_of_lowest_rounds'] = str(diffadjustment_obj.calculation_factor)
            context['lowest_round_id_list'] = lowest_round_id_list

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
    ordering = ['buddy_email']
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

# @login_required
# def chart_handicap_graph(request):
#     labels = []
#     data = []
#     backgroundcolors = []
#     defaultColors = [
#         "#3366CC", "#DC3912", "#FF9900", "#109618", "#990099", "#3B3EAC", "#0099C6",
#         "#DD4477", "#66AA00", "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
#         "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6", "#651067"
#         ]
#     course_colours = dict()

#     # queryset = Round.objects.all().values('date','handicap_differential').filter(player=request.user).order_by('date')
#     queryset = Round.objects.all().values('date', 'course__name','handicap_differential').filter(player=request.user).order_by('date')
#     # print(queryset)
#     queryset_courses = Round.objects.values('course__name').annotate(dcount=Count('course__name')).filter(player=request.user).order_by()
#     # print(queryset_courses)
#     for course in enumerate(queryset_courses):
#         # print(course[0])
#         # print(course[1].get("course__name"))
#         course_colours[course[1].get("course__name")] = defaultColors[course[0]]
#     # print(course_colours)

#     _min = queryset.aggregate(min = Min('handicap_differential'))
#     _max = queryset.aggregate(max = Max('handicap_differential'))
#     _avg = queryset.aggregate(avg = Avg('handicap_differential'))
#     average_handicap = _avg.get("avg")
#     max_height = max(_min.get("min"), _max.get("max")) - average_handicap
#     suggested_min = 0-max_height
#     suggested_max = max_height

#     # Limit to last x rounds
#     # This is now done in chart.js

#     raw_dict = {
#         "x": 0,
#         "y": 0,
#         "course": ""
#     }

#     n=0
#     for entry in queryset:
#         labels.append(entry['date'])
#         me = Object()
#         # me.name = "Onur"
#         # me.age = 35
#         # me.dog = Object()
#         # me.dog.name = "Apollo"
#         me.x = n
#         me.y = int(entry['handicap_differential'] - average_handicap)
#         # me.course = entry['course__name']
#         raw_dict["x"] = n
#         raw_dict["y"] = entry['handicap_differential'] - average_handicap
#         # raw_dict["course"] = entry['course__name']
#         raw_obj = MyObject(raw_dict)
#         # print(me)
#         # print(raw_obj.x)
#         # print(stop)
#         # obj_string = "{ x: " + str(n) + ", y: " + str(entry['handicap_differential'] - average_handicap) + ", course: '" + entry['course__name'] + "'}"
#         # print(raw_obj)
#         data.append(int(entry['handicap_differential'] - average_handicap))
#         # data.append(me)
#         # print(course_colours[entry['course__name']])
#         backgroundcolors.append(course_colours[entry['course__name']])
#         # print(entry['course__name'], entry['date'], backgroundcolors[n])
#         n=n+1
#     print(data)
    
#     return JsonResponse(data={
#         'labels': labels,
#         'data': data,
#         's_min': suggested_min,
#         's_max': suggested_max,
#         'average': str(round(average_handicap,2)),
#         'backgroundcolors': backgroundcolors
#     })

# @login_required
# def chart_handicap_page2(request):
#     return render(request, 'golf/chart_handicap_page2.html')

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
        "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6", "#651067"
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

@login_required
def trackmatch(request, score_id, hole_no):
    # Get Functional Parameters and Initaliase variables  
    score_instance = Score.objects.get(id = score_id)
    no_of_players = score_instance.no_of_players
    player_hcps = []
    player_hcps.append(score_instance.player_a_course_hcp)
    player_hcps.append(score_instance.player_b_course_hcp)
    player_hcps.append(score_instance.player_c_course_hcp)
    player_hcps.append(score_instance.player_d_course_hcp)
    holes_attr=[]
    holes_attr2 = []
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

    cq = Course.objects.all().get(id = 1)
    # cq = Course.objects.all().get(id = score_instance.course.id)      !!!!!!!!!!!!!! Remember to put this in and remove above line !!!!!!!!!!!!!!
    buddy_queryset = Buddy.objects.all().filter(group = score_instance.group)

    # Set Round Meta Parameters for passing to form
    round_meta = {}
    round_meta["round_id"] = score_instance.id
    round_meta["buddy_group"] = score_instance.group
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
    round_meta["outpar"] = cq.hole1par + cq.hole2par + cq.hole3par + cq.hole4par + cq.hole5par + cq.hole6par + cq.hole7par + cq.hole8par + cq.hole9par
    round_meta["inpar"] = cq.hole10par + cq.hole11par + cq.hole12par + cq.hole13par + cq.hole14par + cq.hole15par + cq.hole16par + cq.hole17par + cq.hole18par
    round_meta["totalpar"] = round_meta["outpar"] + round_meta["inpar"]

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
        if count == 0 and no_of_players == 2:   # Get the SI for the 2nd player                             !!!!!!!!!!!!! Change the 4 to a 2
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
        if count == 1 and no_of_players == 2:   # Get the SI for the 1st player                             !!!!!!!!!!!!! Change the 4 to a 2
            if player_hcps[0] <= 18:
                for holeSI in holesSI:
                    alt_playerSI.append(1) if holeSI <= player_hcps[0] else alt_playerSI.append(0)
            if player_hcps[0] > 18 and player_hcps[1] <=36:
                for holeSI in holesSI:
                    alt_playerSI.append(2) if holeSI <= player_hcps[0] - 18 else alt_playerSI.append(1)
            if player_hcps[0] > 36 and player_hcps[1] <=54:
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

            hole_obj = hole_obj + ((
                i,
                eval("cq.hole" + str(i) + "par"),
                eval("cq.hole" + str(i) + "SI"), playerSI[i-1],
                make_stars(playerSI[i-1]) if round_meta["holes_completed"] < i else gross_score,
                '' if round_meta["holes_completed"] < i else net_score,
                '' if round_meta["holes_completed"] < i else compare_to_par,
                '' if no_of_players != 2  and round_meta["holes_completed"] < i else outcome,
                
                ),
                )

        holes_attr.append(hole_obj)
        print(hole_obj)

        # Get Gross, Net, Stableford, out_nine and in_nine running totals
        gross, net, stableford, out_nine_gross, out_nine_net, in_nine_gross, in_nine_net = 0, 0, 0, 0, 0, 0, 0
        player_match_play = 0

        for i in range(1, round_meta["holes_completed"] + 1):
            gross += getattr(score_instance,"player_{0}_s{1}".format(p_letter, i))
            net += getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) - playerSI[i-1]
            if i < 10:
                out_nine_gross = gross
                out_nine_net = net
                out_nine_gross_neg = out_nine_gross
                out_nine_net_neg = out_nine_net
            if i >= 10:
                in_nine_gross = gross - out_nine_gross_neg
                print(">>>>>",gross, in_nine_gross)
                in_nine_net = net - out_nine_net_neg
            s = (getattr(score_instance,"player_{0}_s{1}".format(p_letter, i)) - playerSI[i-1]) - eval("cq.hole" + str(i) + "par")
            stableford += 0 if s >= 2 else stableford_dict[str(s)]
            if p_letter == "a":
                print(hole_obj[i-1][7])
                player_match_play += hole_obj[i-1][7]
            if p_letter == "b":
                print(hole_obj[i-1][7])
                player_match_play += hole_obj[i-1][7]


        # Covert Match play totals to text and assign background colour for cell
        if player_match_play == 0:
            player_match_play_text = "AS"
            box_bk_colour = "#008080"
        elif player_match_play < 0:
            player_match_play_text = str(abs(player_match_play)) + "D"
            box_bk_colour = "OrangeRed"
        else:
            player_match_play_text = str(player_match_play) + "U"
            box_bk_colour = "Black"



        running_totals.append((
            (gross, net, stableford, player_match_play_text, box_bk_colour, out_nine_gross, out_nine_net, in_nine_gross, in_nine_net)
            )
        )

    # Build the player_dict to pass to the form
    player_dict = {}
    player_details = {}
    for count,player in enumerate(buddy_queryset):
        player_details = {}
        player_details["name"] = str(player.buddy_email)
        player_details["holes_attr"] = holes_attr[count]
        player_details["running_totals"] = running_totals[count]
        player_dict["player" + str(count + 1)] = player_details

    # print(player_dict["player1"]["running_totals"][2])    
    # print(player_dict["player2"]["running_totals"][2])
    # print(player_dict["player3"]["running_totals"][2])
    # print(player_dict["player4"]["running_totals"][2])

    players_stableford_list = []
    players_stableford_list.append(player_dict["player1"]["running_totals"][2])
    players_stableford_list.append(player_dict["player2"]["running_totals"][2])
    if no_of_players > 2:
        players_stableford_list.append(player_dict["player3"]["running_totals"][2])
    if no_of_players > 3:
        players_stableford_list.append(player_dict["player4"]["running_totals"][2])
    
    print(players_stableford_list)

    positions = calculate_positions(players_stableford_list)
    print(positions)

    stableford_medal_positions = {}
    stableford_medal_positions["a"] = positions[0] 
    stableford_medal_positions["b"] = positions[1]
    if no_of_players > 2:
        stableford_medal_positions["c"] = positions[2]
    if no_of_players > 3:
        stableford_medal_positions["d"] = positions[3]


    print(stableford_medal_positions)

    # for count, player in enumerate(players_sorted):
    #     players_stableford_colours[players_sorted[count]] = mp_colors.get(str(players_sorted.index(player)))

    # # player_dict["player1"]["running_totals"].append(players_stableford_colours["a"])

    # print(players_stableford)
    # print(players_stableford_colours)

    print(player_dict)

    if request.method == 'POST':
        print("here")
        # create a form instance and populate it with data from the request:
        if no_of_players == 2:
            form = CardEntryForm(request.POST, player_a="", player_b="")
        if no_of_players == 3:
            form = CardEntryForm(request.POST, player_a="", player_b="", player_c="")
        if no_of_players == 4:
            form = CardEntryForm(request.POST, player_a="", player_b="", player_c="", player_d="")
        # check whether it's valid:
        if form.is_valid():
            print("here2")
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
        kwargs = super(CardInitialView, self).get_form_kwargs()
        # golf_group_obj = GolfGroup.objects.filter(id = self.kwargs.get("group") )
        match_buddies = Buddy.objects.filter(group = self.kwargs.get("group") )
        # print(match_buddies)
        # print(len(match_buddies))
        # for buddy in match_buddies:
        #     print(buddy.buddy_email)
        kwargs['no_of_players'] = len(match_buddies)
        kwargs['player_a'] = str(match_buddies[0])
        kwargs['player_b'] = str(match_buddies[1])
        if (len(match_buddies) == 3):
            kwargs['player_c'] = str(match_buddies[2])
        if (len(match_buddies) == 4):
            kwargs['player_c'] = str(match_buddies[2])
            kwargs['player_d'] = str(match_buddies[3])

        
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
                      player_a_course_hcp = form.cleaned_data['player_A'],
                      player_b_course_hcp = form.cleaned_data['player_B'],
                      player_c_course_hcp = form.cleaned_data['player_C'],
                      player_d_course_hcp = form.cleaned_data['player_D']
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
    


