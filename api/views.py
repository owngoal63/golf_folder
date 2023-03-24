from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import CourseSerializer
from golf.models import Course


@api_view(['GET'])
def django_function(request):
    pass


@api_view(['GET'])
def getCourses(request):
    courses = Course.objects.all()
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getCourse(request,pk):
    course = Course.objects.get(id = pk)
    serializer = CourseSerializer(course, many=False)
    return Response(serializer.data)

@api_view(['POST'])
def createCourse(request):
    data = request.data

    course = Course.objects.create(
        name = data['name'],
        tee_name = data['tee_name'],
        par = data["par"],
        course_rating = data["course_rating"],
        slope_rating = data['slope_rating']
    )
    serializer = CourseSerializer(course, many=False)
    return Response(serializer.data)

@api_view(['PUT'])
def updateCourse(request, pk):
    course = Course.objects.get(id = pk)
    serializer = CourseSerializer(course, data = request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)

@api_view(['DELETE'])
def deleteCourse(request, pk):
    course = Course.objects.get(id = pk)
    course.delete()
    return Response('Course was deleted')

