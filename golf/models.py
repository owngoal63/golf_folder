# golf/models.py
from django.db import models
from accounts.models import CustomUser

class Course(models.Model):
    name = models.CharField(max_length=255, default=' ')
    tee_name= models.CharField(max_length=255, default=' ')
    par = models.IntegerField()
    course_rating = models.FloatField()
    slope_rating = models.FloatField()

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
