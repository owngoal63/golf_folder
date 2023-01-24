# golf/views.py
from django.db.models import Avg, Min, Max, Count
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.urls import reverse

from .forms import CourseForm, RoundForm, GolfGroupForm, BuddyForm
from .models import Course, Round, DiffAjustment, GolfGroup, Buddy

from django.shortcuts import render
# from django.db.models import Sum
from django.http import JsonResponse
# from django.db.models import F, Func, Value, CharField
# from django.db.models.functions import Concat

from django.contrib.auth.decorators import login_required

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
        num_score_differentials = len(round_obj)
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
            round_obj_bylowest = Round.objects.filter(player = player_id ).order_by('handicap_differential')[:8]
            for r in round_obj_bylowest:
                lowest_round_id_list.append(r.id)
            calculated_handicap = round_obj_bylowest.aggregate(Avg('handicap_differential'))
            context['calculated_handicap'] = round(calculated_handicap.get('handicap_differential__avg'),1)
            context['number_of_lowest_rounds'] = "8"
            context['lowest_round_id_list'] = lowest_round_id_list

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

# ~~~~~~~ Stat views ~~~~~~~

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
def chart_handicap_page(request):
    return render(request, 'golf/chart_handicap_page.html')

@login_required
def chart_handicap_graph(request):
    labels = []
    data = []
    backgroundcolors = []
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
        # print(course[0])
        # print(course[1].get("course__name"))
        course_colours[course[1].get("course__name")] = defaultColors[course[0]]
    print(course_colours)

    _min = queryset.aggregate(min = Min('handicap_differential'))
    _max = queryset.aggregate(max = Max('handicap_differential'))
    _avg = queryset.aggregate(avg = Avg('handicap_differential'))
    average_handicap = _avg.get("avg")
    max_height = max(_min.get("min"), _max.get("max")) - average_handicap
    suggested_min = 0-max_height
    suggested_max = max_height

    # Limit to last x rounds
    queryset = queryset[:20]

    # print(queryset)
    for entry in queryset:
        labels.append(entry['date'])
        data.append(entry['handicap_differential'] - average_handicap)
        # print(course_colours[entry['course__name']])
        backgroundcolors.append(course_colours[entry['course__name']])
    print(backgroundcolors)
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
        's_min': suggested_min,
        's_max': suggested_max,
        'average': str(round(average_handicap,2)),
        'backgroundcolors': backgroundcolors
    })

@login_required
def chart_handicap_page2(request):
    return render(request, 'golf/chart_handicap_page2.html')

@login_required
def chart_handicap_graph2(request):
    labels = []
    data = []
    backgroundcolors = []
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
        # print(course[0])
        # print(course[1].get("course__name"))
        course_colours[course[1].get("course__name")] = defaultColors[course[0]]
    print(course_colours)

    _min = queryset.aggregate(min = Min('handicap_differential'))
    _max = queryset.aggregate(max = Max('handicap_differential'))
    _avg = queryset.aggregate(avg = Avg('handicap_differential'))
    average_handicap = _avg.get("avg")
    max_height = max(_min.get("min"), _max.get("max")) - average_handicap
    suggested_min = 0-max_height
    suggested_max = max_height

    # Limit to last x rounds
    queryset = queryset[:20]

    # print(queryset)
    for entry in queryset:
        labels.append(entry['date'])
        data.append(entry['handicap_differential'] - average_handicap)
        # print(course_colours[entry['course__name']])
        backgroundcolors.append(course_colours[entry['course__name']])
    print(backgroundcolors)
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
        's_min': suggested_min,
        's_max': suggested_max,
        'average': str(round(average_handicap,2)),
        'backgroundcolors': backgroundcolors
    })



