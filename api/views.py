from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import CourseSerializer, ScoreSerializer
from golf.models import Course, Score, GolfGroup, Buddy
from golf.views import calculate_handicap_on_date, get_list_of_rounds_with_valid_hcp, build_handicap_list_over_time, average_per_month

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
    scores = Score.objects.order_by('-date').all()[:20]
    # print(scores)
    serializer = ScoreSerializer(scores, many=True)
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

@api_view(['GET'])
def getCurrentHandicap(request,player_id):

    from datetime import date

    today = date.today()

    hcp = calculate_handicap_on_date(today, player_id)

    return_details = {}
    return_details["hcp"] = f"Your handicap is {str(hcp[1])}"

    return Response(return_details)

@api_view(['GET'])
def getHistoricalHcp(request, player_id):

    labels = []
    data = []

    # player_id = request.user
    r = get_list_of_rounds_with_valid_hcp(player_id)
    # print(r)
    hcp_history_list = build_handicap_list_over_time(r, player_id)
    worst_hcp = max(hcp_history_list, key=lambda item: item[1])[1]
    best_hcp = min(hcp_history_list, key=lambda item: item[1])[1]
    # hcp_history_list.reverse()      # Sort oldest to most recent
    # print(hcp_history_list)
    monthly_averages = average_per_month(hcp_history_list)
    monthly_averages_list = [(k,v) for k,v in sorted(monthly_averages.items())]
    print(monthly_averages)
    print(monthly_averages_list)
    # for hcp_on_date in monthly_averages_list:
    #     labels.append(hcp_on_date[0])
    #     data.append(hcp_on_date[1])

    return_details = {}
    return_details["hcp_monthly_averages"] = monthly_averages_list
    return_details["worst_hcp"] = worst_hcp
    return_details["best_hcp"] = best_hcp

    return Response(return_details)


@api_view(['GET'])
def getScoreDetails(request, round_id):
    score = Score.objects.get(id = round_id)
    no_of_players = score.no_of_players
    course_name = Course.objects.get(id = score.course.id).name
    course = Course.objects.get(id = score.course.id)
    group_name = GolfGroup.objects.get(id = score.group.id).group_name
    player_list = []
    player_letters = ["a", "b", "c", "d"]
    current_hole_recorded = 0       # Default condition (completed round) for match no started and last hole completed ( recorded )

    for player in range(0, no_of_players):
        player_details_dict = {}
        player_details_dict["id"] = CustomUser.objects.get(email = getattr(score,"player_{0}".format(player_letters[player]))).id
        player_details_dict["firstname"] = CustomUser.objects.get(email = getattr(score,"player_{0}".format(player_letters[player]))).firstname
        player_course_hcp = getattr(score,"player_{0}_course_hcp".format(player_letters[player]))
        player_details_dict["course_hcp"] = player_course_hcp
        player_details_dict["target_score"] = getattr(score,"player_{0}_score_target".format(player_letters[player]))
        gross_score = 0
        net_score = 0
        gross_score_holes_list = []
        net_score_holes_list = []
        course_par_holes_list = []
        course_si_holes_list = []

        for i in range(1, 19):  # Loop through course details to get par and SI
            course_par_holes_list.append(getattr(course,"hole{0}par".format(i)))
            course_si_hole = getattr(course,"hole{0}SI".format(i))
            course_si_holes_list.append(course_si_hole)

        for i in range(1, 19):  # Loop through 18 score fields, add up the gross score and calculate net score
            course_si_hole = getattr(course,"hole{0}SI".format(i))
            if getattr(score,"player_{0}_s{1}".format(player_letters[player],i)) is not None:   # This hole's strokes have been recorded
                gross_score_hole = getattr(score,"player_{0}_s{1}".format(player_letters[player], i))
                gross_score = gross_score + gross_score_hole
                gross_score_holes_list.append(gross_score_hole)
                net_score_hole = gross_score_hole - ( player_course_hcp // 18 + 1 ) if course_si_holes_list[i-1] <= ( player_course_hcp % 18 ) else gross_score_hole - ( player_course_hcp // 18 )
                net_score = net_score + net_score_hole
                net_score_holes_list.append(net_score_hole)
                current_hole_recorded = i    # Take note of last hole played
            else:                                               # This hole's strokes have not been recorded - get handicap strokes for player at this hole  
                base_strokes = player_course_hcp // 18
                remaining_strokes = player_course_hcp % 18
                extra_stroke = 1 if course_si_hole <= remaining_strokes else 0
                total_strokes = base_strokes + extra_stroke
                if total_strokes == 0:
                    gross_score_holes_list.append('')
                    net_score_holes_list.append('')
                else:
                    gross_score_holes_list.append('*' * total_strokes)
                    net_score_holes_list.append('')

        player_details_dict["gross_score"] = gross_score
        player_details_dict["net_score"] = net_score
        player_details_dict["gross_score_holes_list"] = gross_score_holes_list
        player_details_dict["net_score_holes_list"] = net_score_holes_list
        player_details_dict["course_par_holes_list"] = course_par_holes_list
        player_details_dict["course_si_holes_list"] = course_si_holes_list
        player_list.append(player_details_dict)

    return_details = {}
    return_details["score_id"] = score.id
    return_details["date"] = score.date
    return_details["group_name"] = group_name
    return_details["no_of_players"] = score.no_of_players
    return_details["course_name"] = course_name
    return_details["current_hole_recorded"] = current_hole_recorded
    return_details["player_details_list"] = player_list

    return Response(return_details)


@api_view(['GET'])
def getScorecardHeaders(request):
    scores = Score.objects.order_by('-id').all()[:30]
    # print(scores)
    serializer = ScoreSerializer(scores, many=True)
    return Response(serializer.data)




