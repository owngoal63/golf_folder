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

]