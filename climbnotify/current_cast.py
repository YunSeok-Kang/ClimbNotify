import django
import os
import time
import datetime
import requests
from bs4 import BeautifulSoup

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClimbNotifyBot.settings')
django.setup()

from climbnotify.models import MapPositionData
from climbnotify.models import Mountains

from climbnotify.models import ClimbingRecord

def get_basedate():
    return time.strftime("%Y%m%d")

# basetime은 현재 시간대를 기준으로 1시간을 제해서 계산한다. (예보 delay 40분 발생때문.)
# 후에는 1시간 제하지 않은 시간으로 먼저 요청을 보내고, 요청이 이상할 경우 1시간을 제하는 방식으로 가자.
def get_basetime_for_current():
    return str(datetime.datetime.now().hour - 1) + "00"
    #return time.strftime('%H') + "00"

def get_basetime_for_cast():
    now = datetime.datetime.now()
    hour = datetime.datetime.now().hour

    if now.minute < 46: # 45분 기준이 원칙. 그러나 오차 생각해서 46분
            hour -= 1

    return str(hour) + "30"

def get_basetime_for_today_cast():
    base_times = ['0200', '0500', '0800', '1100', '1400', '1700', '2000', '2300']

    now_time = datetime.datetime.now()
    current_hour = now_time.hour
    current_min = now_time.minute

    idx = 0 # 선택된 basetime보다 1보다 큰 값이 저장됨.
    base_time_int = 2 # 얘도 마찬가지. 얘는 3만큼 큰 값이 저장됨.
    while base_time_int < 24:
        if current_hour < base_time_int:
            break

        base_time_int += 3
        idx += 1

    # 최종 선택된 값
    final_idx = idx - 1

    if current_min < 11: # 10분이 원칙. 오차 생각해서 11분. 이 조건에 걸리면 3시간 전 예보 보냄.
        final_idx -= 1

    selected_time = base_times[final_idx]

    selected_date = ""
    if final_idx < 0: # idx의 값이 음수이면, 그 전 날짜를 반환해줘야 함.
        yesterday_date = datetime.datetime.now() - datetime.timedelta(days=1)
        selected_date = yesterday_date.strftime('%Y%m%d')
    else:
        selected_date = datetime.datetime.now().strftime('%Y%m%d')

    return selected_date + "," + selected_time




def get_url_params_to_str(params):
    param_str = ""
    keys = params.keys()
    for key in keys:
        param_str += "&" + key + "=" + params[key]

    return param_str[1:]

def get_avg_list(list):
    total = 0
    for i in list:
        total += i;

    return total / len(list)

weather_list = ['맑으', '구름이 조금 있으', '구름이 많으', '흐리']
rain_type_list = ['비 없음', '비', '진눈깨비', '눈']

def __get_current_cast_msg(mountain_name, pos_x, pos_y):
    # params로 serviceKey를 날리니 이상하게 변형되는 문제 발생. 인코딩 관련 문제인 것 같긴 한데, 정보를 찾을 시간이 부족하여 우선 야매로 해결.
    params = {
        'serviceKey': "enGPdGoVyvBJUTmlXNaHKUZKs9pm5tv8zmBWgVW%2F9Je7wWq4qRW77y6oEikFMVT9y9qz1EONELmGSUryRfB1wA%3D%3D",
        'base_date': get_basedate(),
        'base_time': get_basetime_for_current(),
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

def get_mountain_current_cast(mountain_data):
    location_str = mountain_data.location.split()
    number_of_phases = len(location_str)

    map_data = MapPositionData.objects.all()
    map_data = map_data.filter(phase_one=location_str[0])
    number_of_phases -= 1

    if number_of_phases > 0:
        result = map_data.filter(phase_two=location_str[1])
        if len(result) > 0:
            number_of_phases -= 1
            map_data = result

            if number_of_phases > 0:
                result = map_data.filter(phase_two=location_str[2])
                if len(result) > 0:
                    map_data = result

    global selected_data
    global g_mountain_data
    g_mountain_data = mountain_data
    selected_data = map_data[0]
    return __get_current_cast_msg(mountain_data.name, str(selected_data.posX), str(selected_data.posY))

sky_condition_cast_list = ['맑은', '구름 조금의', '구름 많은', '흐린']
lgt_condition_cast_list = ['없음', '낮은', '보통', '높은']
wsd_condition_cast_list = ['잔잔한', '약간 강한', '강한', '매우 강한']

# get_mountain_current_cast 가 먼저 호출된 다음에 호출되어야 합니다.
# selected_data의 데이터가 채워져야 아래 함수가 실행될 수 있습니다.
# 연산 효율화를 위해 이렇게 작업하였습니다.
# 체계적으로 구조화 시킬 수 있지만, 개발 일정을 맞추기 위해 우선 임시로 진행합니다.
def get_mountain_cast():
    if selected_data == None:
        print('먼저 get_mountain_current_cast를 실행해주세요.')

    params = {
        'serviceKey': "enGPdGoVyvBJUTmlXNaHKUZKs9pm5tv8zmBWgVW%2F9Je7wWq4qRW77y6oEikFMVT9y9qz1EONELmGSUryRfB1wA%3D%3D",
        'base_date': get_basedate(),
        'base_time': get_basetime_for_cast(),
        'nx': str(selected_data.posX),
        'ny': str(selected_data.posY),
        'numOfRows': '50',
        '_type': 'json'}

    params = get_url_params_to_str(params)
    res = requests.get(
        "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastTimeData?" + params)
    json_result = res.json()
    #print(json_result)

    #print(len(json_result['response']['body']['items']['item']))
    time_list = []
    th1_list = []
    rn1_list = []
    sky_list = [] # 1 ~ 4까지의 데이터가 들어감. 사용할 때 주의.
    pty_list = []
    lgt_list = []
    wsd_list = []

    # 측정 시간대 확인 후 time_list에 삽입
    for item in json_result['response']['body']['items']['item']:
        current_time = item['fcstTime']
        if current_time in time_list:
            continue
        else:
            time_list.append(current_time)

    # 순회하기 위한 정보 수집
    items = json_result['response']['body']['items']['item']
    time_length = len(time_list)
    number_of_datas = len(items)

    # 순회 시작. 각각의 list에 데이터가 수집됨.
    for i in range(int(number_of_datas / time_length)):
        current_list = []
        for j in range(time_length):
            item = items[i * time_length + j]
            if j == 0:
                current_cat = item['category']
                if current_cat == 'T1H':
                    current_list = th1_list
                elif current_cat == 'RN1':
                    current_list = rn1_list
                elif current_cat == 'SKY':
                    current_list = sky_list
                elif current_cat == 'PTY':
                    current_list = pty_list
                elif current_cat == 'LGT':
                    current_list = lgt_list
                elif current_cat == 'WSD':
                    current_list = wsd_list

            current_list.append(item['fcstValue'])

    total_msg = ""
    th1_msg = ""
    rn1_msg = ""
    sky_msg = ""
    pty_msg = ""
    lgt_msg = ""
    wsd_msg = ""

    # 기준 시간 설명
    total_msg = str(time_list[0])[:2] + "시부터 " + str(time_list[-1])[:2] + "시까지의 예보입니다.\n"

    # 날씨 예보
    th1_msg += str(time_list[0])[:2] + "시 기준 " + g_mountain_data.name + "의 기온은 " + str(th1_list[0]) \
               + "도로 예상되며, "

    ''' 예보 백업. 간략하게 임시로 수정해봄.
    th1_msg += str(time_list[0]) + "시 기준 " + g_mountain_data.name + "의 기온은 " + str(th1_list[0]) \
               + "도로 예상되며, "  \+ str(time_list[-1]) + "시 기준 "  + str(th1_list[1]) + "도로 "
    if float(th1_list[0]) - th1_list[-1] > 0:
        th1_msg += "하락"
    else:
        th1_msg += "상승"
    th1_msg += "할 예정이고, "
    '''

    # 비/눈 소식
    first_pty = pty_list[0]
    total_pty = first_pty
    pty_msg_once = True
    for i in range(1, len(pty_list)):
        if (pty_list[i]) > 0 and pty_msg_once:
            pty_msg += str(time_list[i])[:2] + "시부터 " + rain_type_list[pty_list[i]] + "소식이 있습니다. "
            pty_msg_once = False

        total_pty += pty_list[i]

    if (total_pty / len(pty_list)) == first_pty: # 평균과 첫째 값이 같으면 같은 상태가 지속된다는 의미.
        pty_msg = str(time_list[0])[:2] + "시부터 계속해서 " + rain_type_list[first_pty]
        if rain_type_list[first_pty] == 3:
            pty_msg += "이"
        else:
            pty_msg += "가"
        pty_msg += " 소식이 있습니다."

    if total_pty == 0:
        pty_msg = "비 소식은 없습니다."

    # 이거 네 개 해야함.
    # 강수량 측정
    if total_pty > 0: # 눈/비 소식이 있는 경우에만 예보.
        avg_rn1 = -1
        for rn1 in rn1_list:
            avg_rn1 += rn1
        avg_rn1 = avg_rn1 / len(rn1_list)

        rn1_msg += "시간당 평균 " + str(round(avg_rn1, 2)) + "mm의 눈/비가 내릴 예정입니다."

    # 하늘 상태
    sky_msg = " 그리고 "
    avg_sky = int(get_avg_list(sky_list) - 1) # 1 ~ 4 사이로 나옴.

    print(sky_list)
    if avg_sky == (sky_list[0] - 1): # 평균 sky 상태와 첫번째 상태가 같다면, 같은 하늘이 지속되고 있는 것.
        sky_msg += sky_condition_cast_list[avg_sky] + ' 날씨가 계속될 전망입니다.'
    else:
        sky_msg += str(time_list[0])[:2] + "시는 " + sky_condition_cast_list[sky_list[0] - 1] + "상태, "
        for i in range(1, len(sky_list)):
            if sky_list[i] != sky_list[0]:
                sky_msg += str(time_list[i])[:2] + "시부터 " + sky_condition_cast_list[sky_list[i] - 1] + "상태가 될 예정입니다."
                break

    lgt_msg = ""
    lgt_total = get_avg_list(lgt_list)
    if lgt_total > 0:
        for i in range(len(lgt_list)):
            if lgt_list[i] > 0:
                lgt_msg += str(time_list[i])[:2] + "시부터" + lgt_condition_cast_list[i] + '확률로 낙뢰가 발생할 수 있습니다. '
                if lgt_list[i] == 3:
                    lgt_msg += "등산 중이시면 활동을 중단하고 하산하십시오. "

    # 바람
    wsd_msg = " 또한 "
    wsd_avg = get_avg_list(wsd_list)
    wsd_msg += "평균 " + str(round(wsd_avg, 2)) + "m/s의 "
    idx = -1
    if wsd_avg > 14:
        idx = 3
    elif wsd_avg > 9:
        idx = 2
    elif wsd_avg > 4:
        idx = 1
    else:
        idx = 0

    wsd_msg += wsd_condition_cast_list[idx] + " 바람이 불 예정입니다. "
    if idx > 1:
        wsd_msg += "등산 활동에 적합하지 않습니다."

    # th1_msg 뺌. 기온이 중요하지 않은 것 같음.
    #total_msg = total_msg + th1_msg + pty_msg + rn1_msg + sky_msg + lgt_msg + wsd_msg
    total_msg = total_msg + pty_msg + rn1_msg + sky_msg + lgt_msg + wsd_msg
    return total_msg

# get_mountain_current_cast 가 먼저 호출된 다음에 호출되어야 합니다.
# selected_data의 데이터가 채워져야 아래 함수가 실행될 수 있습니다.
# 연산 효율화를 위해 이렇게 작업하였습니다.
# 체계적으로 구조화 시킬 수 있지만, 개발 일정을 맞추기 위해 우선 임시로 진행합니다.
def get_today_cast():
    if selected_data == None:
        print('먼저 get_mountain_current_cast를 실행해주세요.')

    base_date_time = get_basetime_for_today_cast().split(',')
    params = {
        'serviceKey': "enGPdGoVyvBJUTmlXNaHKUZKs9pm5tv8zmBWgVW%2F9Je7wWq4qRW77y6oEikFMVT9y9qz1EONELmGSUryRfB1wA%3D%3D",
        'base_date': base_date_time[0],
        'base_time': base_date_time[1],
        'nx': str(selected_data.posX),
        'ny': str(selected_data.posY),
        'numOfRows': '250',
        '_type': 'json'}

    params = get_url_params_to_str(params)
    res = requests.get(
        "http://newsky2.kma.go.kr/service/SecndSrtpdFrcstInfoService2/ForecastSpaceData?" + params)
    json_result = res.json()
    print(json_result)

    time_list = []
    number_of_categories = 0
    first_category = json_result['response']['body']['items']['item'][0]['category']
    duplicated_category_count = 0
    for item in json_result['response']['body']['items']['item']:
        if first_category == item['category']: # 카테고리 갯수 파악
            duplicated_category_count += 1
        current_time = item['fcstTime']#int(item['fcstTime'] / 100)
        if isinstance(current_time, int):
            current_time = str(current_time)

        print(item['category'] + " " + current_time + " " + str(item['fcstDate']))

        if duplicated_category_count < 2:
            number_of_categories += 1

        if current_time in time_list:
            continue
        else:
            time_list.append(current_time)

    starting_idx = 0
    for i in range(len(time_list)):
        cur_time = time_list[i]
        if cur_time == '0600': # 06시보다 작은 데이터 다 잘라냄
            starting_idx = i
            break

    time_list = time_list[i:]

    print(time_list)
    print(number_of_categories)

    sky_list = []
    pop_list = []
    tmx = -1000
    tmn = -1000


    # 필요한 데이터를 걸러냄
    for i in range(starting_idx, starting_idx + len(time_list)):
        for j in range(number_of_categories):
            item = json_result['response']['body']['items']['item'][i * number_of_categories + j]
            category = item['category']
            item_value = item['fcstValue']

            if category == 'POP':
                pop_list.append(item_value)
            elif category == 'SKY':
                sky_list.append(item_value - 1)
            elif tmx == -1000 and category == 'TMX':
                tmx = item_value
            elif tmn == -1000 and category == 'TMN':
                tmn = item_value

    print(sky_list)
    print(pop_list)
    print(tmx)
    print(tmn)

    # 예보
    final_msg = ""
    temp_msg = "내일 기온은 "
    sky_msg = ""
    pop_msg = "강수 확률은 "

    # 최고, 최저 기온
    temp_msg += "아침 최저 " + str(tmn) +"도, 낮 최고 " + str(tmx) +"도 입니다."

    # 하늘 상태
    avg_sky = int(get_avg_list(sky_list))  # 1 ~ 4 사이로 나옴.

    if avg_sky == sky_list[0]:  # 평균 sky 상태와 첫번째 상태가 같다면, 같은 하늘이 지속되고 있는 것.
        sky_msg += sky_condition_cast_list[avg_sky] + ' 날씨가 계속될 전망입니다.'
    else:
        sky_msg += str(time_list[0][:2]) + "시는 " + sky_condition_cast_list[sky_list[0]] + "상태, "
        for i in range(1, len(sky_list)):
            if sky_list[i] != sky_list[0]:
                sky_msg += time_list[i][:2] + "시부터 " + sky_condition_cast_list[sky_list[i]] + "상태가 될 예정입니다."
                break

    # 강수확률
    avg_pop = int(get_avg_list(pop_list))

    if avg_pop == pop_list[0]:
        pop_msg += str(avg_pop) + "% 입니다."
    else:
        pop_msg += str(avg_pop) + "% 이나, "
        for i in range(1, len(pop_list)):
            if pop_list[i] != pop_list[0]:
                pop_msg += time_list[i][:2] + "시부터 " + str(pop_list[i]) + "%가 될 예정입니다."
                break

    final_msg = temp_msg + " 그리고 " + sky_msg + " " + pop_msg
    return final_msg

def get_forest_fire_data_from_server(area_code, gubun):
    params = {
        'localArea': str(area_code),
        'gubun': gubun,
        'keyValue': '2712876668951163538199006701325590044760',
        'version': '1.1',
        'excludeForecast': '1'}

    params = get_url_params_to_str(params)
    res = requests.get(
        'http://know.nifos.go.kr/openapi/forestPoint/forestPointListSearch.do?' + params)
    return BeautifulSoup(res.text, "html.parser")

# get_mountain_current_cast 가 먼저 호출된 다음에 호출되어야 합니다.
# selected_data의 데이터가 채워져야 아래 함수가 실행될 수 있습니다.
# 연산 효율화를 위해 이렇게 작업하였습니다.
# 체계적으로 구조화 시킬 수 있지만, 개발 일정을 맞추기 위해 우선 임시로 진행합니다.
def forest_fire_cast(mountain_data):
    if selected_data == None:
        print('먼저 get_mountain_current_cast를 실행해주세요.')

    area_code = 0
    area_phase_one = selected_data.phase_one
    if area_phase_one == '서울특별시':
        area_code = 11
    elif area_phase_one == '부산광역시':
        area_code = 26
    elif area_phase_one == '대구광역시':
        area_code = 27
    elif area_phase_one == '인천광역시':
        area_code = 28
    elif area_phase_one == '광주광역시':
        area_code = 29
    elif area_phase_one == '대전광역시':
        area_code = 30
    elif area_phase_one == '울산광역시':
        area_code = 31
    elif area_phase_one == '세종특별자치시':
        area_code = 36
    elif area_phase_one == '경기도':
        area_code = 41
    elif area_phase_one == '강원도':
        area_code = 42
    elif area_phase_one == '충청북도':
        area_code = 43
    elif area_phase_one == '충청남도':
        area_code = 44
    elif area_phase_one == '전라북도':
        area_code = 45
    elif area_phase_one == '전라남도':
        area_code = 46
    elif area_phase_one == '경상북도':
        area_code = 47
    elif area_phase_one == '경상남도':
        area_code = 48
    elif area_code == '제주특별자치도':
        area_code = 50

    xml_data = get_forest_fire_data_from_server(area_code, 'sigungu')

    selected_item = None
    for item in xml_data.find_all('items'):
        if selected_data.phase_two and selected_data.phase_two == item.sigun.string:
            selected_item = item

    if selected_item == None:
        # 'sido'로 옵션 맞추고 get_forest_fire_data_from_server 다시 호출
        print("selected_item not selected")

    fire_data = float(selected_item.meanavg.string)
    condition_str = ""
    if fire_data < 50:
        condition_str = "관심"
    elif fire_data <= 65:
        condition_str = "주의"
    elif fire_data <= 85:
        condition_str = "경계"
    else:
        condition_str = "심각"

    print(fire_data)

    final_str = "현재 " + mountain_data.name + "의 산불위험지수 등급은 " + condition_str + "단계 입니다. "
    if condition_str == "경계":
        final_str += "산불에 각별히 주의하시길 부탁드립니다."
    elif condition_str == "심각":
        final_str += "산행을 중단하십시오."

    return final_str




if __name__ == "__main__":
    climbing_data = ClimbingRecord.objects.get(user_id='K9Y1fcvFjGdv')
    mountain_data = Mountains.objects.get(code=climbing_data.code)

    get_mountain_current_cast(mountain_data)
    forest_fire_cast()