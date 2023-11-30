# golf/models.py
from django.db import models
from accounts.models import CustomUser
from datetime import date

class Course(models.Model):
    name = models.CharField(max_length=255, default=' ')
    tee_name= models.CharField(max_length=255, default=' ')
    par = models.IntegerField()
    course_rating = models.FloatField()
    slope_rating = models.FloatField()
    hole1par = models.IntegerField(blank=True, default = 0)
    hole2par = models.IntegerField(blank=True, default = 0)
    hole3par = models.IntegerField(blank=True, default = 0)
    hole4par = models.IntegerField(blank=True, default = 0)
    hole5par = models.IntegerField(blank=True, default = 0)
    hole6par = models.IntegerField(blank=True, default = 0)
    hole7par = models.IntegerField(blank=True, default = 0)
    hole8par = models.IntegerField(blank=True, default = 0)
    hole9par = models.IntegerField(blank=True, default = 0)
    hole10par = models.IntegerField(blank=True, default = 0)
    hole11par = models.IntegerField(blank=True, default = 0)
    hole12par = models.IntegerField(blank=True, default = 0)
    hole13par = models.IntegerField(blank=True, default = 0)
    hole14par = models.IntegerField(blank=True, default = 0)
    hole15par = models.IntegerField(blank=True, default = 0)
    hole16par = models.IntegerField(blank=True, default = 0)
    hole17par = models.IntegerField(blank=True, default = 0)
    hole18par = models.IntegerField(blank=True, default = 0)
    hole1SI = models.IntegerField(blank=True, default = 0)
    hole2SI = models.IntegerField(blank=True, default = 0)
    hole3SI = models.IntegerField(blank=True, default = 0)
    hole4SI = models.IntegerField(blank=True, default = 0)
    hole5SI = models.IntegerField(blank=True, default = 0)
    hole6SI = models.IntegerField(blank=True, default = 0)
    hole7SI = models.IntegerField(blank=True, default = 0)
    hole8SI = models.IntegerField(blank=True, default = 0)
    hole9SI = models.IntegerField(blank=True, default = 0)
    hole10SI = models.IntegerField(blank=True, default = 0)
    hole11SI = models.IntegerField(blank=True, default = 0)
    hole12SI = models.IntegerField(blank=True, default = 0)
    hole13SI = models.IntegerField(blank=True, default = 0)
    hole14SI = models.IntegerField(blank=True, default = 0)
    hole15SI = models.IntegerField(blank=True, default = 0)
    hole16SI = models.IntegerField(blank=True, default = 0)
    hole17SI = models.IntegerField(blank=True, default = 0)
    hole18SI = models.IntegerField(blank=True, default = 0)

    def get_fields(self):
        return[(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]

    def __str__(self):
        return self.name

class Round(models.Model):
    player = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    course = models.ForeignKey(Course, related_name='round', on_delete=models.CASCADE)
    score = models.IntegerField()
    net_score = models.CharField(max_length=5, default=' ')
    handicap_differential = models.FloatField(default=0)

    # def get_fields(self):
    #     return[(field.verbose_name, field.value_from_object(self)) for field in self.__class__._meta.fields]

    def __str__(self):
        # return self.player + " " + self.course
        return '%s %s' % (self.date, self.course)


class DiffAjustment(models.Model):
    num_of_scores = models.IntegerField()
    calculation_type = models.CharField(max_length=20)
    calculation_factor = models.IntegerField()
    adjustment = models.FloatField()

    class Meta:
        ordering = ['num_of_scores']

    def __str__(self):
        return '%s | %s | %s | %s' % (self.num_of_scores, self.calculation_type, self.calculation_factor, self.adjustment)

class GolfGroup(models.Model):
    group_name = models.CharField(max_length=255, default=' ')
    administrator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.group_name

class Buddy(models.Model):
    group = models.ForeignKey(GolfGroup, on_delete=models.CASCADE)
    buddy_email = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        # return self.player + " " + self.course
        return '%s' % (self.buddy_email)
    
class Score(models.Model):
    date = models.DateField(default=date.today)
    course = models.ForeignKey(Course, related_name='course', on_delete=models.CASCADE)
    group = models.ForeignKey(GolfGroup, on_delete=models.CASCADE)
    no_of_players = models.IntegerField()
    player_a = models.ForeignKey(CustomUser, related_name='player_a', on_delete=models.CASCADE, null=True, blank=True)
    player_b = models.ForeignKey(CustomUser, related_name='player_b', on_delete=models.CASCADE, null=True, blank=True)
    player_c = models.ForeignKey(CustomUser, related_name='player_c', on_delete=models.CASCADE, null=True, blank=True)
    player_d = models.ForeignKey(CustomUser, related_name='player_d', on_delete=models.CASCADE, null=True, blank=True)
    player_a_course_hcp = models.IntegerField(null=True, blank=True)
    player_b_course_hcp = models.IntegerField(null=True, blank=True)
    player_c_course_hcp = models.IntegerField(null=True, blank=True)
    player_d_course_hcp = models.IntegerField(null=True, blank=True)
    player_a_s1 = models.IntegerField(null=True, blank=True)
    player_a_s2 = models.IntegerField(null=True, blank=True)
    player_a_s3 = models.IntegerField(null=True, blank=True)
    player_a_s4 = models.IntegerField(null=True, blank=True)
    player_a_s5 = models.IntegerField(null=True, blank=True)
    player_a_s6 = models.IntegerField(null=True, blank=True)
    player_a_s7 = models.IntegerField(null=True, blank=True)
    player_a_s8 = models.IntegerField(null=True, blank=True)
    player_a_s9 = models.IntegerField(null=True, blank=True)
    player_a_s10 = models.IntegerField(null=True, blank=True)
    player_a_s11 = models.IntegerField(null=True, blank=True)
    player_a_s12 = models.IntegerField(null=True, blank=True)
    player_a_s13 = models.IntegerField(null=True, blank=True)
    player_a_s14 = models.IntegerField(null=True, blank=True)
    player_a_s15 = models.IntegerField(null=True, blank=True)
    player_a_s16 = models.IntegerField(null=True, blank=True)
    player_a_s17 = models.IntegerField(null=True, blank=True)
    player_a_s18 = models.IntegerField(null=True, blank=True)
    player_b_s1 = models.IntegerField(null=True, blank=True)
    player_b_s2 = models.IntegerField(null=True, blank=True)
    player_b_s3 = models.IntegerField(null=True, blank=True)
    player_b_s4 = models.IntegerField(null=True, blank=True)
    player_b_s5 = models.IntegerField(null=True, blank=True)
    player_b_s6 = models.IntegerField(null=True, blank=True)
    player_b_s7 = models.IntegerField(null=True, blank=True)
    player_b_s8 = models.IntegerField(null=True, blank=True)
    player_b_s9 = models.IntegerField(null=True, blank=True)
    player_b_s10 = models.IntegerField(null=True, blank=True)
    player_b_s11 = models.IntegerField(null=True, blank=True)
    player_b_s12 = models.IntegerField(null=True, blank=True)
    player_b_s13 = models.IntegerField(null=True, blank=True)
    player_b_s14 = models.IntegerField(null=True, blank=True)
    player_b_s15 = models.IntegerField(null=True, blank=True)
    player_b_s16 = models.IntegerField(null=True, blank=True)
    player_b_s17 = models.IntegerField(null=True, blank=True)
    player_b_s18 = models.IntegerField(null=True, blank=True)
    player_c_s1 = models.IntegerField(null=True, blank=True)
    player_c_s2 = models.IntegerField(null=True, blank=True)
    player_c_s3 = models.IntegerField(null=True, blank=True)
    player_c_s4 = models.IntegerField(null=True, blank=True)
    player_c_s5 = models.IntegerField(null=True, blank=True)
    player_c_s6 = models.IntegerField(null=True, blank=True)
    player_c_s7 = models.IntegerField(null=True, blank=True)
    player_c_s8 = models.IntegerField(null=True, blank=True)
    player_c_s9 = models.IntegerField(null=True, blank=True)
    player_c_s10 = models.IntegerField(null=True, blank=True)
    player_c_s11 = models.IntegerField(null=True, blank=True)
    player_c_s12 = models.IntegerField(null=True, blank=True)
    player_c_s13 = models.IntegerField(null=True, blank=True)
    player_c_s14 = models.IntegerField(null=True, blank=True)
    player_c_s15 = models.IntegerField(null=True, blank=True)
    player_c_s16 = models.IntegerField(null=True, blank=True)
    player_c_s17 = models.IntegerField(null=True, blank=True)
    player_c_s18 = models.IntegerField(null=True, blank=True)
    player_d_s1 = models.IntegerField(null=True, blank=True)
    player_d_s2 = models.IntegerField(null=True, blank=True)
    player_d_s3 = models.IntegerField(null=True, blank=True)
    player_d_s4 = models.IntegerField(null=True, blank=True)
    player_d_s5 = models.IntegerField(null=True, blank=True)
    player_d_s6 = models.IntegerField(null=True, blank=True)
    player_d_s7 = models.IntegerField(null=True, blank=True)
    player_d_s8 = models.IntegerField(null=True, blank=True)
    player_d_s9 = models.IntegerField(null=True, blank=True)
    player_d_s10 = models.IntegerField(null=True, blank=True)
    player_d_s11 = models.IntegerField(null=True, blank=True)
    player_d_s12 = models.IntegerField(null=True, blank=True)
    player_d_s13 = models.IntegerField(null=True, blank=True)
    player_d_s14 = models.IntegerField(null=True, blank=True)
    player_d_s15 = models.IntegerField(null=True, blank=True)
    player_d_s16 = models.IntegerField(null=True, blank=True)
    player_d_s17 = models.IntegerField(null=True, blank=True)
    player_d_s18 = models.IntegerField(null=True, blank=True)
    player_a_score_target = models.IntegerField(null=True, blank=True)
    player_b_score_target = models.IntegerField(null=True, blank=True)
    player_c_score_target = models.IntegerField(null=True, blank=True)
    player_d_score_target = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return '%s %s %s' % (self.date, self.course, self.group)



