from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import CourseSerializer, ScoreSerializer
from golf.models import Course, Score

from accounts.models import CustomUser

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

#============================================================================

@api_view(['GET'])
def getScores(request):
    courses = Score.objects.all()
    serializer = ScoreSerializer(courses, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getScore(request,pk):
    score = Score.objects.get(id = pk)
    serializer = ScoreSerializer(score, many=False)
    return Response(serializer.data)

@api_view(['POST', 'GET'])
def updateScore(request, pk, hole, a_score, b_score, c_score = 0, d_score = 0):

    hole_scores = {}
    # Workaround applied below to fix Siri problem of not hearing the number 6
    if a_score == 99: a_score = 6
    if b_score == 99: b_score = 6
    if c_score == 99: c_score = 6
    if d_score == 99: d_score = 6
    hole_scores["player_a_s" + str(hole)] = a_score
    hole_scores["player_b_s" + str(hole)] = b_score
    hole_scores["player_c_s" + str(hole)] = c_score
    hole_scores["player_d_s" + str(hole)] = d_score
    score = Score.objects.get(id = pk)
    serializer = ScoreSerializer(score, data = hole_scores, partial = True)
    if serializer.is_valid():
        serializer.save()
    return_details = {}
    if score.no_of_players == 2:
        return_details["message"] = f"Hole {str(hole)} updated with {CustomUser.objects.filter(email=score.player_a.email)[0].firstname}'s score of {str(a_score)} and {CustomUser.objects.filter(email=score.player_b.email)[0].firstname}'s score of {str(b_score)}."
    if score.no_of_players == 3:
        return_details["message"] = f"Hole {str(hole)} updated with {CustomUser.objects.filter(email=score.player_a.email)[0].firstname}'s score of {str(a_score)}, {CustomUser.objects.filter(email=score.player_b.email)[0].firstname}'s score of {str(b_score)} and {CustomUser.objects.filter(email=score.player_c.email)[0].firstname}'s score of {str(c_score)}." 
    if score.no_of_players == 4:
        return_details["message"] = f"Hole {str(hole)} updated with {CustomUser.objects.filter(email=score.player_a.email)[0].firstname}'s score of {(a_score)}, {CustomUser.objects.filter(email=score.player_b.email)[0].firstname}'s score of {(b_score)}, {CustomUser.objects.filter(email=score.player_c.email)[0].firstname}'s score of {str(c_score)} and {CustomUser.objects.filter(email=score.player_d.email)[0].firstname}'s score of {str(d_score)}."
    
    return Response(return_details)

@api_view(['GET'])
def getCurrentHole(request,pk):
    score = Score.objects.get(id = pk)

     # Check through the fields to find the first blank against Player A
    hole_id = 19
    current_hole_id = hole_id    # Default value if loop below does not find None value i.e. Round is finished and Hole is 19th 
    for i in range(1, 19):
        if getattr(score,"player_a_s{0}".format(i)) is None:
            current_hole_id = i
            break
    return_details = {}
    if current_hole_id > 18:
        return_details["message"] = f"You have completed the round at {score.course.name}."
    else:    
        return_details["message"] = f"Okay. Let's get the scores for hole number {str(current_hole_id)} at {score.course.name}."
    return_details["current_hole_number"] = current_hole_id
    return_details["no_of_players"] = score.no_of_players
    return_details["course"] = score.course.name
    return_details["course_id"] = score.course.id
    return_details["player_a_name"] = CustomUser.objects.filter(email=score.player_a.email)[0].firstname
    return_details["player_a_id"] = CustomUser.objects.filter(email=score.player_a.email)[0].id
    return_details["player_a_course_hcp"] = score.player_a_course_hcp
    return_details["player_b_name"] = CustomUser.objects.filter(email=score.player_b.email)[0].firstname
    return_details["player_b_id"] = CustomUser.objects.filter(email=score.player_b.email)[0].id
    return_details["player_b_course_hcp"] = score.player_b_course_hcp
    if score.no_of_players > 2:
        return_details["player_c_name"] = CustomUser.objects.filter(email=score.player_c.email)[0].firstname
        return_details["player_c_id"] = CustomUser.objects.filter(email=score.player_c.email)[0].id
        return_details["player_c_course_hcp"] = score.player_c_course_hcp
    if score.no_of_players > 3:
        return_details["player_d_name"] = CustomUser.objects.filter(email=score.player_d.email)[0].firstname
        return_details["player_d_id"] = CustomUser.objects.filter(email=score.player_d.email)[0].id
        return_details["player_d_course_hcp"] = score.player_d_course_hcp

    return Response(return_details)

