# golf/urls.py
from django.urls import path
from django.contrib.auth.decorators import login_required

# from .views import CourseAddView, CourseDetailView, CourseListView, CourseDetailView, CourseUpdateView, CourseDeleteView, RoundAddView, RoundListView, RoundDetailView, RoundUpdateView, RoundDeleteView, RoundListHandicapView
from .views import *

urlpatterns = [
    path("add_course/", login_required(CourseAddView.as_view()), name="addcourse"),
    path("list_courses/", login_required(CourseListView.as_view()), name = "courselist" ),
    path("display_course/<int:pk>/", login_required(CourseDetailView.as_view()), name="coursedetail"),
    path("display_course/<int:pk>/update/", login_required(CourseUpdateView.as_view()), name="courseupdate"),
    path("display_course/<int:pk>/delete/", login_required(CourseDeleteView.as_view()), name="coursedelete"),

    path("add_round/", login_required(RoundAddView.as_view()), name="addround"),
    path("list_rounds/", login_required(RoundListView.as_view()), name = "roundlist" ),
    path("display_round/<int:pk>/", login_required(RoundDetailView.as_view()), name="rounddetail"),
    path("display_round/<int:pk>/update/", login_required(RoundUpdateView.as_view()), name="roundupdate"),
    path("display_round/<int:pk>/delete/", login_required(RoundDeleteView.as_view()), name="rounddelete"),

    path("list_round_handicaps/", login_required(RoundListHandicapView.as_view()), name = "roundlisthandicap" ),
    path("show_calculated_handicap/<str:calculated_handicap>/<str:total_number_of_rounds>/<str:number_of_lowest_rounds>", login_required(HandicapDetailView.as_view()), name="handicapview" ),

    path("add_golf_group/", login_required(GolfGroupAddView.as_view()), name="addgolfgroup"),
    path("list_golf_groups/", login_required(GolfGroupListView.as_view()), name = "golfgrouplist" ),
    path("display_golf_group/<int:pk>/", login_required(GolfGroupDetailView.as_view()), name="golfgroupdetail"),
    path("display_golf_group/<int:pk>/update/", login_required(GolfGroupUpdateView.as_view()), name="golfgroupupdate"),
    path("display_golf_group/<int:pk>/delete/", login_required(GolfGroupDeleteView.as_view()), name="golfgroupdelete"),

    path("add_buddy/<int:group>/", login_required(BuddyAddView.as_view()), name="addbuddy"),
    path("list_buddies/<int:group>/", login_required(BuddyListView.as_view()), name = "buddylist" ),
    path("display_buddy/<int:group>/<int:pk>/update/", login_required(BuddyUpdateView.as_view()), name="buddyupdate"),
    path("display_buddy/<int:group>/<int:pk>/delete/", login_required(BuddyDeleteView.as_view()), name="buddydelete"),

    path('chart_rounds_page/', chart_rounds_page, name='chart_rounds_page'),
    path('chart_rounds_graph/', chart_rounds_graph, name='chart_rounds_graph'),
    path('chart_handicap_page/', chart_handicap_page, name='chart_handicap_page'),
    path('chart_handicap_graph/', chart_handicap_graph, name='chart_handicap_graph'),
    # path('chart_handicap_page2/', chart_handicap_page2, name='chart_handicap_page2'),
    # path('chart_handicap_graph2/', chart_handicap_graph2, name='chart_handicap_graph2'),
]
