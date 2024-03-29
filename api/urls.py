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
    path('score/<int:pk>/', getScore),
    path('updatescore/<int:pk>/<int:hole>/<int:a_score>/<int:b_score>/<int:c_score>/<int:d_score>/', updateScore),
    path('getcurrenthole/<int:pk>/', getCurrentHole),

    path('getcurrenthandicap/<int:player_id>/', getCurrentHandicap),
    path('gethistoricalhcp/<int:player_id>/', getHistoricalHcp),
    path('getscoredetails/<int:round_id>/', getScoreDetails),


]