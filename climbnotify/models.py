from django.db import models

# Create your models here.
class Mountains(models.Model):
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=128)
    code = models.IntegerField(primary_key=True)

    def __str__(self):
        return self.name

class User(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    sex = models.CharField(max_length=16)
    age = models.CharField(max_length=16)

    def __str__(self):
        return self.id

class ClimbingRecord(models.Model):
    user_id = models.CharField(max_length=64)
    date = models.CharField(max_length=8)
    code = models.IntegerField()

    def __str__(self):
        return self.date + " " + str(self.code)

class ActivatedUsers(models.Model):
    user_id = models.CharField(max_length=64)
    first_logged_time = models.CharField(max_length=8)
    updated_logged_time = models.CharField(max_length=8)
    phase = models.IntegerField()
    mountain_info = models.CharField(max_length=64, default=-1) # 유저가 등록하는 동안 등산할 산의 데이터가 여기 기록됨.
    climbing_date = models.CharField(max_length=8, default="")

    def __str__(self):
        return self.user_id + " " + str(self.phase)

class MapPositionData(models.Model):
    district_code = models.IntegerField(default=-1, primary_key=True)
    phase_one = models.CharField(max_length=32)
    phase_two = models.CharField(max_length=32, null=True)
    phase_three = models.CharField(max_length=32, null=True)
    posX = models.IntegerField()
    posY = models.IntegerField()

    def __str__(self):
        name = self.phase_one
        if self.phase_two:
            name += self.phase_two
        if self.phase_three:
            name += self.phase_three
        return name