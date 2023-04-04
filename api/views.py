from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import CourseSerializer, ScoreSerializer
from golf.models import Course, Score


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

    player_name= {}
    player_name["golfuser2@domain.com"] = "Usain"
    player_name["gordonalindsay@gmail.com"] = "Lindsay"
    player_name["gordonlindsay@virginmedia.com"] = "Gordon"
    player_name["golfuser@domain.com"] = "Goffy"
    player_name["tester@mail.com"] = "Lester"
    player_name["dmcdmcd@me.com"] = "David"
    player_name["chrisbalderstone@yahoo.com"] = "Chris"

    # print(pk, hole, a_score, b_score)
    hole_scores = {}
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
        return_details["message"] = f"Hole {str(hole)} updated with {player_name.get(score.player_a.email)}'s score of {str(a_score)} and {player_name.get(score.player_b.email)}'s score of {str(b_score)}."
    if score.no_of_players == 3:
        return_details["message"] = f"Hole {str(hole)} updated with {player_name.get(score.player_a.email)}'s score of {str(a_score)}, {player_name.get(score.player_b.email)}'s score of {str(b_score)} and {player_name.get(score.player_c.email)}'s score of {str(c_score)}." 
    if score.no_of_players == 4:
        return_details["message"] = f"Hole {str(hole)} updated with {player_name.get(score.player_a.email)}'s score of {(a_score)}, {player_name.get(score.player_b.email)}'s score of {(b_score)}, {player_name.get(score.player_c.email)}'s score of {str(c_score)} and {player_name.get(score.player_d.email)}'s score of {str(d_score)}."
    
    return Response(return_details)

@api_view(['GET'])
def getCurrentHole(request,pk):
    score = Score.objects.get(id = pk)

    player_name= {}
    player_name["golfuser2@domain.com"] = "Usain"
    player_name["gordonalindsay@gmail.com"] = "Lindsay"
    player_name["gordonlindsay@virginmedia.com"] = "Gordon"
    player_name["golfuser@domain.com"] = "Goffy"
    player_name["tester@mail.com"] = "Lester"
    player_name["dmcdmcd@me.com"] = "David"
    player_name["chrisbalderstone@yahoo.com"] = "Chris"

     # Check through the fields to find the first blank against Player A
    hole_id = 19
    for i in range(1, 19):
        if getattr(score,"player_a_s{0}".format(i)) is None:
            current_hole_id = i
            break
    return_details = {}
    return_details["message"] = f"Okay. Let's get the scores for hole number {str(current_hole_id)} at {score.course.name}."
    return_details["current_hole_number"] = current_hole_id
    return_details["no_of_players"] = score.no_of_players
    return_details["course"] = score.course.name
    return_details["player_a_name"] = player_name.get(score.player_a.email)
    return_details["player_b_name"] = player_name.get(score.player_b.email)
    if score.no_of_players > 2:
        return_details["player_c_name"] = player_name.get(score.player_c.email)
    if score.no_of_players > 3:
        return_details["player_d_name"] = player_name.get(score.player_d.email)

    return Response(return_details)

