from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt


from django.db.models import F, Q

from .serializers import CourseSerializer, ScoreSerializer, ScoreListSerializer, GolfGroupSerializer, BuddySerializer, UserSerializer, ScoreSerializerExtended
from golf.models import Course, Score, GolfGroup, Buddy
from golf.views import calculate_handicap_on_date, get_list_of_rounds_with_valid_hcp, build_handicap_list_over_time, average_per_month, set_player_target_round_score

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
    return_details["hcp_num"] = hcp[1]
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

    stableford_dict = {
        "1": 1,
        "0": 2,
        "-1": 3,
        "-2": 4,
        "-3": 5,
        "-4": 6,
        "-5": 7
    }
    
    score = Score.objects.get(id = round_id)
    no_of_players = score.no_of_players
    course_name = Course.objects.get(id = score.course.id).name
    course = Course.objects.get(id = score.course.id)
    group_name = GolfGroup.objects.get(id = score.group.id).group_name
    admin_id = GolfGroup.objects.get(id = score.group.id).administrator.id
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
        player_details_dict["player_type"] = "Admin" if player == 0 else "Player"
        gross_score = 0
        net_score = 0
        out_gross_score = 0
        in_gross_score = 0
        out_net_score = 0
        in_net_score = 0
        out_par_total = 0
        in_par_total = 0
        stableford_total = 0
        gross_score_holes_list = []
        net_score_holes_list = []
        stableford_score_holes_list = []
        course_par_holes_list = []
        course_si_holes_list = []
        matchplay_holes_list= []

        for i in range(1, 19):  # Loop through course details to get par and SI
            course_par_holes_list.append(getattr(course,"hole{0}par".format(i)))
            course_si_hole = getattr(course,"hole{0}SI".format(i))
            course_si_holes_list.append(course_si_hole)
            if i <= 9: out_par_total = out_par_total + getattr(course,"hole{0}par".format(i))
            if i > 9: in_par_total = in_par_total + getattr(course,"hole{0}par".format(i))

        for i in range(1, 19):  # Loop through 18 score fields, add up the gross score and calculate net score
            course_si_hole = getattr(course,"hole{0}SI".format(i))
            if getattr(score,"player_{0}_s{1}".format(player_letters[player],i)) is not None:   # This hole's strokes have been recorded
                gross_score_hole = getattr(score,"player_{0}_s{1}".format(player_letters[player], i))
                gross_score = gross_score + gross_score_hole
                gross_score_holes_list.append(gross_score_hole)
                net_score_hole = gross_score_hole - ( player_course_hcp // 18 + 1 ) if course_si_holes_list[i-1] <= ( player_course_hcp % 18 ) else gross_score_hole - ( player_course_hcp // 18 )
                net_score = net_score + net_score_hole
                net_score_holes_list.append(net_score_hole)
                if net_score_hole - getattr(course,"hole{0}par".format(i)) <= 1:
                    stableford_score = stableford_dict.get(str(net_score_hole - getattr(course,"hole{0}par".format(i))))
                    stableford_score_holes_list.append(stableford_score)
                    stableford_total = stableford_total + stableford_score
                    # print("Stableford Hole",i, net_score_hole, getattr(course,"hole{0}par".format(i)), stableford_dict.get(str(net_score_hole - getattr(course,"hole{0}par".format(i)))), stableford_total )
                else:
                    stableford_score_holes_list.append(0)
                    # print("Stableford Hole",i, net_score_hole, getattr(course,"hole{0}par".format(i)), 0 )
                current_hole_recorded = i    # Take note of last hole played
                if i <= 9: out_gross_score = out_gross_score + int(gross_score_hole)
                if i > 9: in_gross_score = in_gross_score + int(gross_score_hole)
                if i <= 9: out_net_score = out_net_score + int(net_score_hole)
                if i > 9: in_net_score = in_net_score + int(net_score_hole)
            else:             # This hole's strokes have not been recorded - get handicap strokes for player at this hole  
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

        
        player_details_dict["out_par_total"] = out_par_total
        player_details_dict["in_par_total"] = in_par_total
        player_details_dict["out_gross_score"] = out_gross_score if current_hole_recorded >= 9 else ''
        player_details_dict["in_gross_score"] = in_gross_score if current_hole_recorded == 18 else ''
        player_details_dict["out_net_score"] = out_net_score if current_hole_recorded >= 9 else ''
        player_details_dict["in_net_score"] = in_net_score if current_hole_recorded == 18 else ''
        player_details_dict["gross_score"] = gross_score
        player_details_dict["net_score"] = net_score
        player_details_dict["stableford_total"] = stableford_total
        player_details_dict["gross_score_holes_list"] = gross_score_holes_list
        player_details_dict["net_score_holes_list"] = net_score_holes_list
        player_details_dict["stableford_score_holes_list"] = stableford_score_holes_list
        player_details_dict["course_par_holes_list"] = course_par_holes_list
        player_details_dict["course_si_holes_list"] = course_si_holes_list

        player_list.append(player_details_dict)

    # Add in Matchplay details when its a two player game
    matchplay_holes_list_player1 = []
    matchplay_holes_list_player2 = []
    if score.no_of_players == 2:
        for i in range(0, 18):
            if player_list[0]['net_score_holes_list'][i] == player_list[1]['net_score_holes_list'][i]:  # AS
                print("AS")
                matchplay_holes_list_player1.append(0)
                matchplay_holes_list_player2.append(0)
            if player_list[0]['net_score_holes_list'][i] > player_list[1]['net_score_holes_list'][i]:   # PLayer2's hole
                matchplay_holes_list_player1.append(-1)
                matchplay_holes_list_player2.append(1)
            if player_list[0]['net_score_holes_list'][i] < player_list[1]['net_score_holes_list'][i]:   # PLayer1's hole
                matchplay_holes_list_player1.append(1)
                matchplay_holes_list_player2.append(-1)
        player_list[0]['matchplay_holes_list'] = matchplay_holes_list_player1
        player_list[1]['matchplay_holes_list'] = matchplay_holes_list_player2
    

    return_details = {}
    return_details["score_id"] = score.id
    return_details["name"] = score.name
    return_details["date"] = score.date
    return_details["group_name"] = group_name
    return_details["admin_id"] = admin_id
    return_details["no_of_players"] = score.no_of_players
    return_details["course_name"] = course_name
    return_details["current_hole_recorded"] = current_hole_recorded
    if score.no_of_players == 2:
        return_details["matchplay_status_player1"] = sum(matchplay_holes_list_player1)
        return_details["matchplay_status_player2"] = sum(matchplay_holes_list_player2)
    return_details["player_details_list"] = player_list

    return Response(return_details)


@api_view(['GET'])
def getScorecardHeaders(request):
    scores = Score.objects.order_by('-id').all()[:30]
    # print(scores)
    serializer = ScoreListSerializer(scores, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getGroups(request):
    golfgroups = GolfGroup.objects.order_by('administrator').all()
    serializer = GolfGroupSerializer(golfgroups, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getGroupsByAdmin(request, administrator):
    golfgroups = GolfGroup.objects.order_by('administrator').filter(administrator__id = administrator)
    serializer = GolfGroupSerializer(golfgroups, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getBuddys(request, group_id):
    buddys = Buddy.objects.filter(group_id = group_id).all()
    serializer = BuddySerializer(buddys, many=True)
    return Response(serializer.data)


@api_view(['POST', 'GET'])
def CreateScorecard(request, group_id, course_id, no_of_players, player_a_id, player_a_course_hcp, player_b_id, player_b_course_hcp, player_c_id = 0, player_c_course_hcp = 0, player_d_id = 0, player_d_course_hcp = 0, name = "No Name" ):

    course_obj = Course.objects.get(id = course_id)
    group_obj = GolfGroup.objects.get(id = group_id)
    match_buddies = Buddy.objects.filter(group = group_id)

    request.data["no_of_players"] = no_of_players       # Had to add this due to weird bug that was erronously generating a serializer error
    
    Scorecard = Score.objects.create(
        course = course_obj,
        group = group_obj,
        no_of_players = int(no_of_players),
        player_a = match_buddies[0].buddy_email,
        player_a_course_hcp = int(player_a_course_hcp),
        player_b = match_buddies[1].buddy_email,
        player_b_course_hcp = int(player_b_course_hcp),
        player_c = match_buddies[2].buddy_email if no_of_players > 2 else match_buddies[0].buddy_email,
        player_c_course_hcp = int(player_c_course_hcp),
        player_d = match_buddies[3].buddy_email if no_of_players > 3 else match_buddies[0].buddy_email,
        player_d_course_hcp = int(player_d_course_hcp),
        player_a_score_target = set_player_target_round_score(course_id, player_a_id),
        player_b_score_target = set_player_target_round_score(course_id, player_b_id),
        player_c_score_target = set_player_target_round_score(course_id, player_c_id) if no_of_players > 2 else 0,
        player_d_score_target = set_player_target_round_score(course_id, player_d_id) if no_of_players > 3 else 0,
        name = name
    )
    serializer = ScoreSerializer(Scorecard, data = request.data)
    if serializer.is_valid():
        instance = serializer.save()
        return Response({
            "id": instance.id,
            "message": "Record created successfully",
            "data": serializer.data},
            status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def getUsers(request):
    users = CustomUser.objects.filter(is_superuser = False).all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getUser(request, user_id):
    user = CustomUser.objects.filter(id = user_id).all()
    serializer = UserSerializer(user, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getScorecardHeadersExtended(request):
    player_id = request.query_params.get('player_id', None)  # Get player_id from query parameters
    if player_id:
        player_id = int(player_id)
        # Filter the Score records based upon no_of_players and where any of the player_a, player_b, player_c, or player_d matches the provided ID
        scores = Score.objects.filter(
            Q(no_of_players=2) & (Q(player_a__id=player_id) | Q(player_b__id=player_id)) |
            Q(no_of_players=3) & (Q(player_a__id=player_id) | Q(player_b__id=player_id) | Q(player_c__id=player_id)) |
            Q(no_of_players=4) & (Q(player_a__id=player_id) | Q(player_b__id=player_id) | Q(player_c__id=player_id) | Q(player_d__id=player_id))
        ).order_by('-id')[:30]  # Order by id descending and limit to 30 records
    else:
        # If no player_id is provided, return all records
        scores = Score.objects.all().order_by('-id')[:30]  # Order by id descending and limit to 30 records
    serializer = ScoreSerializerExtended(scores, many=True)
    return Response(serializer.data)

@csrf_exempt  # Disable CSRF for this view
@api_view(['POST'])
def createGolfGroup(request, group_name, administrator_id):
    # Validate the administrator exists
    try:
        administrator = CustomUser.objects.get(id=administrator_id)
    except CustomUser.DoesNotExist:
        return Response({"error": "Administrator with ID does not exist"}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # Create a new GolfGroup
    golf_group = GolfGroup(group_name=group_name, administrator=administrator)
    golf_group.save()

    # Serialize and return the newly created GolfGroup
    serializer = GolfGroupSerializer(golf_group)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@csrf_exempt  # Disable CSRF for this view
@api_view(['POST'])
def createBuddy(request, user_id, golfgroup_id):
    # Validate the user exists
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({"error": "User with ID does not exist"}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Validate the golfgroup exists
    try:
        golfgroup = GolfGroup.objects.get(id=golfgroup_id)
    except GolfGroup.DoesNotExist:
        return Response({"error": "GolfGroup with ID does not exist"}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # Create a new GolfGroup
    buddy = Buddy(group=golfgroup, buddy_email=user)
    buddy.save()

    # Serialize and return the newly created GolfGroup
    serializer = BuddySerializer(buddy)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
