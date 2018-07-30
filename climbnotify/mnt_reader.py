#from .models import Mountains
import csv
import django
import os
import time
import datetime
import requests, json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClimbNotifyBot.settings')
django.setup()

from climbnotify.models import MapPositionData
from climbnotify.models import ClimbingRecord
from climbnotify.models import Mountains


'''
def get_basedate():
    return time.strftime("%Y%m%d")

# basetime은 현재 시간대를 기준으로 1시간을 제해서 계산한다. (예보 delay 40분 발생때문.)
# 후에는 1시간 제하지 않은 시간으로 먼저 요청을 보내고, 요청이 이상할 경우 1시간을 제하는 방식으로 가자.
def get_basetime():
    return str(datetime.datetime.now().hour - 1) + "00"
    #return time.strftime('%H') + "00"

def get_url_params_to_str(params):
    param_str = ""
    keys = params.keys()
    for key in keys:
        param_str += "&" + key + "=" + params[key]

    return param_str[1:]

weather_list = ['맑으', '구름이 조금 있으', '구름이 많으', '흐리']
rain_type_list = ['비 없음', '비', '진눈깨비', '눈']

def get_current_cast(mountain_name, pos_x, pos_y):
    # params로 serviceKey를 날리니 이상하게 변형되는 문제 발생. 인코딩 관련 문제인 것 같긴 한데, 정보를 찾을 시간이 부족하여 우선 야매로 해결.
    params = {
        'serviceKey': "enGPdGoVyvBJUTmlXNaHKUZKs9pm5tv8zmBWgVW%2F9Je7wWq4qRW77y6oEikFMVT9y9qz1EONELmGSUryRfB1wA%3D%3D",
        'base_date': get_basedate(),
        'base_time': get_basetime(),
        'nx': pos_x,
        'ny': pos_y,
        '_type': 'json'}

    res = requests.get(
        "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastGrib?" + get_url_params_to_str(params))
    json_result = res.json()

    weather_type = -1
    rain_type = -1
    rainfall = -1
    temperature = -100
    wind_speed = -1
    wind_vec = -1 # 방위각인듯. 활용가이드 보고 쓸건지 말건지 결정하자.

    # 데이터 수신 파트
    for item in json_result['response']['body']['items']['item']:
        current_item_cat = item['category']
        current_value = item['obsrValue']
        if current_item_cat == 'SKY':
            weather_type = current_value - 1 # 1 ~ 4로 데이터 받아짐. 0 ~ 3의 범위로 좁힘.
        elif current_item_cat == "PTY":
            rain_type = current_value
        elif current_item_cat == "RN1":
            rainfall = current_value
        elif current_item_cat == "T1H":
            temperature = current_value
        elif current_item_cat == "WSD":
            wind_speed = current_value
        elif current_item_cat == "VEC":
            wind_vec = current_value

    # 메시지 만드는 파트
    weather_condition_msg = ""  # 맑음 ~ 흐림
    rain_condition_msg = ""  # 비 형태
    temp_condition_msg = ""  # 온도
    rainfall_msg = ""  # 강우량
    windspeed_msg = ""  # 풍속

    # 하늘 상태(맑음, 구름 등) 메시지
    weather_condition_msg = "현재 " + mountain_name + "은 " + weather_list[weather_type] + "며, "

    # 비 소식 메시지
    if rain_type == 0:  # 비 없음
        rain_condition_msg += "비는 내리지 않고 있습니다."
    elif rain_type == 3:  # 눈
        rain_condition_msg += "눈이 내리고 있습니다."
    else:  # 비 혹은 진눈깨비
        rain_condition_msg += rain_type_list[rain_type] + "가 내리고 있습니다."

    # 강수량 메시지(있을 경우)
    if rainfall > 0:
        rainfall_msg += "앞으로 1시간동안 " + str(rainfall) + "mm의 " + rain_type_list[rain_type] + "이(가) 올 것으로 예상됩니다."

    # 현재 기온 메시지
    temp_condition_msg = "현재 기온은 " + str(temperature) + "도 이고, "

    # 현재 바람 메시지
    if wind_speed > 0:
        windspeed_msg += str(wind_speed) +"m/s의 "
        if wind_speed > 14:
            windspeed_msg += "매우 강한"
        elif wind_speed > 9:
            windspeed_msg += "강한"
        elif wind_speed > 4:
            windspeed_msg += "약간 강한"
        else:
            windspeed_msg += "약한"
        windspeed_msg += " 바람이 불고있습니다."
    else:
        windspeed_msg += "바람은 없습니다."

    final_msg = weather_condition_msg + rain_condition_msg + rainfall_msg + " " + temp_condition_msg + windspeed_msg
    return final_msg



def get_mountain_cast(mountain_data):
    location_str = mountain_data.location.split()
    number_of_phases = len(location_str)

    map_data = MapPositionData.objects.all()
    map_data = map_data.filter(phase_one=location_str[0])
    number_of_phases -= 1

    if number_of_phases > 0:
        map_data = map_data.filter(phase_two=location_str[1])
        number_of_phases -= 1

        if number_of_phases > 0:
            map_data = map_data.filter(phase_two=location_str[2])

    selected_data = map_data[0]

    get_current_cast(mountain_data.name, str(selected_data.posX), str(selected_data.posY))
'''





'''
from climbnotify.models import MapPositionData

instances = []

with open("./Map.csv", 'r', encoding='UTF8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        p1 = row['p1']
        p2 = row['p2']
        if p2 == '':
            p2 = None
        p3 = row['p3']
        if p3 == '':
            p3 = None

        instances.append(MapPositionData(district_code=row['district_code'], phase_one=p1, phase_two=p2, phase_three=p3, posX=row['x'], posY=row['y']))

MapPositionData.objects.bulk_create(instances)
'''
'''
queryset = Mountains.objects.all()
queryset = queryset.filter(name__contains='금')

for model_instance in queryset:
    print(model_instance.name + " " + model_instance.location) # 화면에 출력할 때 DB에 쿼리 (lazy)
'''

