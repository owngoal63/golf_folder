# api/urls.py
from django.urls import path

from .views import *

urlpatterns = [
    # path("add_course/", CourseAddView.as_view(), name="addcourse"),
    path('courses/', getCourses),
    path('course/create/', createCourse),
    path('course/<int:pk>/update/', updateCourse),
    path('course/<int:pk>/delete/', deleteCourse),
    path('course/<int:pk>/', getCourse),

    # path('score/<int:pk>/update/', updateScore),
    path('getscores/', getScores),
    path('score/<int:pk>/', getScore),
    path('createscorecard/<int:group_id>/<int:course_id>/<int:no_of_players>/<int:player_a_id>/<int:player_a_course_hcp>/<int:player_b_id>/<int:player_b_course_hcp>/<int:player_c_id>/<int:player_c_course_hcp>/<int:player_d_id>/<int:player_d_course_hcp>/<str:name>/', CreateScorecard),
    path('updatescore/<int:pk>/<int:hole>/<int:a_score>/<int:b_score>/<int:c_score>/<int:d_score>/', updateScore),
    path('getcurrenthole/<int:pk>/', getCurrentHole),

    path('getcurrenthandicap/<int:player_id>/', getCurrentHandicap),
    path('gethistoricalhcp/<int:player_id>/', getHistoricalHcp),
    path('getscorecardheaders/', getScorecardHeaders),
    path('getscoredetails/<int:round_id>/', getScoreDetails),
    path('getgroups/', getGroups),
    path('getgroups/<int:administrator>/', getGroupsByAdmin),
    path('getbuddys/<int:group_id>/', getBuddys),
    path('getusers/', getUsers),
    path('getuser/<int:user_id>/', getUser),
    path('getscorecardheadersextended/', getScorecardHeadersExtended),
    path('creategolfgroup/<str:group_name>/<int:administrator_id>/', createGolfGroup),
    path('createbuddy/<int:user_id>/<int:golfgroup_id>/', createBuddy),

]