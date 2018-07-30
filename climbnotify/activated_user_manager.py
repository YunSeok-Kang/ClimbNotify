import django
import os
import time

from .models import ActivatedUsers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClimbNotifyBot.settings')
django.setup()

def getCurrentTime():
    return time.strftime('%m%d%H%M')

def addUser(user_id, phase):
    currentTime = getCurrentTime()
    if ActivatedUsers.objects.get(user_id=user_id):
        updatePhase(user_id, phase)
        return

    activated_user = ActivatedUsers(user_id=user_id, first_logged_time=currentTime, updated_logged_time=currentTime, phase=phase)
    activated_user.save()

def updatePhase(user_id, phase):
    currentTime = getCurrentTime()
    user = ActivatedUsers.objects.get(user_id=user_id)
    user.phase = phase
    user.updated_logged_time = currentTime
    user.save()

# 일정 주기마다 업데이트 하면서 만료된 데이터 날려버리자. 만료 시간은 임의로 우선 20분. first - updated 해서 차 확인하면 됨.