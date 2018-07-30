from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import HttpResponse
import json
import time
import datetime

from climbnotify.models import Mountains
from climbnotify.models import User
from climbnotify.models import ClimbingRecord
from .Modules import user_manager
from .models import ActivatedUsers
from . import current_cast

from . import activated_user_manager

# Create your views here.
class Singleton:
    __instance = None

    @classmethod
    def __getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls.__getInstance
        return cls.__instance

class ActivatedUserManager(Singleton):

    def get_current_time(self):
        return time.strftime('%m%d%H%M')

    def add_user(self, user_id, phase):
        currentTime = self.get_current_time()
        if ActivatedUsers.objects.get(user_id=user_id):
            self.update_phase(user_id, phase)
            return

        activated_user = ActivatedUsers(user_id=user_id, first_logged_time=currentTime, updated_logged_time=currentTime,
                                        phase=phase)
        activated_user.save()

    def update_phase(self, user_id, phase):
        currentTime = self.get_current_time()
        user = ActivatedUsers.objects.get(user_id=user_id)
        user.phase = phase
        user.updated_logged_time = currentTime
        user.save()

user_ages_list = ["10대", "20대", "30대", "40대", "50대", "60대 이상"]
user_sex_list = ["남", "여", "기타"]

def keyboard(request):
    return JsonResponse({
        'type': 'buttons',
        'buttons': ['등산알리미 실행하기']
    })

@csrf_exempt
def answer(request):

    json_str = ((request.body).decode('utf-8'))
    received_json_data = json.loads(json_str)
    datacontent = received_json_data['content']

    registered_user = False

    if datacontent == '등산알리미 실행하기':
        user_id = received_json_data['user_key']

        # user_id 데이터 베이스 조회.
        queryset = User.objects.all()
        queryset = queryset.filter(id=user_id)

        if not queryset:
            return JsonResponse({
                'message': {
                    'text': '첫 방문이시네요! 간단한 정보 입력을 부탁드리겠습니다. \n\n데이터는 익명으로 수집되며, 추후 제작될 등산로 추천 등의 서비스 구축에 이용될 예정입니다. \n\n1.나이가 어떻게 되시나요?'
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons": user_ages_list
                }
            })
        # 있으면 산 등록 페이지로.
        else:
            registered_user = True
    if not registered_user:
        if datacontent in user_ages_list:
            user_id = received_json_data['user_key']
            user_manager.AddUser(user_id).age = datacontent

            return JsonResponse({
                'message': {
                    'text': '나이 등록 완료. \n\n성별을 입력해주세요.'
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons": user_sex_list
                }
            })
        elif datacontent in user_sex_list:
            user_id = received_json_data['user_key']
            userData = user_manager.FindUser(user_id)
            if userData:
                user = User(id=userData.id, age=userData.age, sex=userData.sex)
                user.save()

                user_manager.DeleteUser(user_id)
                return JsonResponse({
                    'message': {
                        'text': '성별 등록 완료. 축하드려요! 이제부터 서비스를 사용하실 수 있습니다.'
                    },
                    "keyboard": {
                        "type": "buttons",
                        "buttons": [
                            "시작하기"
                        ]
                    }
                })
            else:
                return JsonResponse({
                    'message': {
                        'text': '등록 과정에서 예상치 못한 문제 발생!'
                    }
                })


    # 여기서부터는 무조건 user_id 조회가 가능.
    user_id = received_json_data['user_key']
    if not user_id:
        print("예상치 못한 오류 발생. 문제 확인 바랍니다.")

    activated_data = ActivatedUsers.objects.all()
    activated_data = activated_data.filter(user_id=user_id)
    if not activated_data:  # 활성화 데이터가 없으면 등록.
        currentTime = time.strftime('%m%d%H%M')
        activated_user = ActivatedUsers(user_id=user_id, first_logged_time=currentTime,
                                        updated_logged_time=currentTime,
                                        mountain_info = "",
                                        climbing_date = "",
                                        phase=11)
        activated_user.save()

        return JsonResponse({
            "message": {
                'text': '등산하실 산을 입력하여주세요!'
            },
            "keyboard": {
                "type": "text"
            }
        })

    activated_data = ActivatedUsers.objects.get(user_id=user_id)

    # activated_data가 있으면 아래 절차 시행
    user_phase = activated_data.phase
    if user_phase == 10: # activated_data가 없으면 만들고 11로 지정하지만, 등록된 일정을 취소할 시 11로 돌리니 문제 발생
                        # 쿼리셋이 없다고 읽혀서 검색결과 없음을 뱉어냄. 궁극적으로는 취소할 시 활성화 데이터를 날려야 한다.
        activated_data.phase = 11
        activated_data.save()

        return JsonResponse({
            "message": {
                'text': '등산하실 산을 입력하여주세요!'
            },
            "keyboard": {
                "type": "text"
            }
        })
    elif user_phase == 11:
        # 글자 수가 2글자 이하이면 경고메시지 출력하는 기능 제작하기.
        queryset = Mountains.objects.all()
        queryset = queryset.filter(name__contains=datacontent)

        if queryset:
            mountains_list = []
            for model_instance in queryset:
                mountains_list.append(
                    model_instance.name + ", " + model_instance.location[:-1] + ", " + str(model_instance.code))
            mountains_list.append('다시 입력하기')

            activated_data.phase = 12
            activated_data.save()

            return JsonResponse({
                "message": {
                    'text': "아래의 결과에서 등산을 원하시는 산을 골라주세요."
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons": mountains_list
                }
            })
        else:
            return JsonResponse({
                "message": {
                    'text': "검색하신 결과가 없습니다. 다시 한 번 입력해주세요!"
                },
                "keyboard": {
                    "type": "text"
                }
            })
    elif user_phase == 12:
        if datacontent == '다시 입력하기':
            activated_data.phase = 11
            activated_data.save()

            return JsonResponse({
                "message": {
                    'text': '재입력을 선택하셨습니다. 등산하실 산을 입력하여주세요!'
                },
                "keyboard": {
                    "type": "text"
                }
            })
        else:
            activated_data.phase = 13
            activated_data.mountain_info = datacontent
            activated_data.save()

            return JsonResponse({
                "message": {
                    'text': '등산 일시를 선택하세요.'
                },
                "keyboard":{
                    "type":"buttons",
                    "buttons":['오늘', '내일']
                }
            })

    elif user_phase == 13:
        # 산 데이터 처리를 어떻게 할 것인지 고민해봐야.
        mountain_data = activated_data.mountain_info.split(',')

        climbing_date = time.strftime('%y%m%d')
        if datacontent == '내일':
            tomorrow_date = datetime.datetime.now() + datetime.timedelta(days=1)
            climbing_date = tomorrow_date.strftime('%y%m%d')

        climbing_data = ClimbingRecord(user_id=user_id, date=climbing_date, code=mountain_data[2][1:])
        climbing_data.save()

        activated_data.phase = 2
        activated_data.save()

        return JsonResponse({
            "message": {
                'text': "등산일정 등록이 완료되었습니다. 아래의 '등산정보 확인하기' 버튼을 눌러 등산 정보를 확인하실 수 있습니다."
            },
            "keyboard": {
                "type": "buttons",
                "buttons": ['등산정보 확인하기']
            }
        })

        # 선택된 산을 바탕으로 유저 데이터 등록하기.
    elif user_phase == 2:
        msg = ""
        if datacontent == '등산정보 확인하기':
            climbing_data = ClimbingRecord.objects.get(user_id=user_id)
            mountain_data = Mountains.objects.get(code=climbing_data.code)
            locations_arr = mountain_data.location.split()
            locations_str = ""
            for location in locations_arr:
                locations_str += " " + location

            msg += locations_str[1:] + "에 있는 " + mountain_data.name + "을 등산할 예정이십니다."
            if climbing_data.date == time.strftime("%y%m%d"):
                msg = "오늘 " + msg
                msg += "\n\n" + current_cast.get_mountain_current_cast(mountain_data)
                msg += "\n\n" + current_cast.get_mountain_cast()
                msg += "\n\n" + current_cast.forest_fire_cast(mountain_data)

            else:
                msg = "내일 " + msg
                current_cast.get_mountain_current_cast(mountain_data)
                msg += "\n\n" + current_cast.get_today_cast()

            print(user_id)
        elif datacontent == '지도 확인하기':
            climbing_data = ClimbingRecord.objects.get(user_id=user_id)
            mountain_data = Mountains.objects.get(code=climbing_data.code)

            url = "http://map.daum.net/link/search/"
            url += mountain_data.name
            msg = "지도 정보를 확인합니다. " + mountain_data.name + "을 지도에서 확인하기: " + url
            return JsonResponse({
                "message": {
                    'text': msg + "\n\n'등산정보 확인하기': 산의 기상 정보, 산불예보 등을 확인합니다.\n'지도 확인하기': 등산하실 산의 지도 정보를 확인합니다.\n'취소하기': 등산 일정을 취소합니다."
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons": ['등산정보 확인하기', '지도 확인하기', '취소하기']
                }
            })
        elif datacontent == '취소하기':
            activated_data.phase = 10
            activated_data.save()

            climbing_data = ClimbingRecord.objects.get(user_id=user_id)
            climbing_data.delete()

            return JsonResponse({
                "message": {
                    'text': "등산 일정을 취소하셨습니다. 등산하실 산을 다시 입력해주세요."
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons":['네']
                }
            })

        return JsonResponse({
            "message": {
                'text': msg + "\n\n'등산정보 확인하기': 산의 기상 정보, 산불예보 등을 확인합니다.\n'지도 확인하기': 등산하실 산의 지도 정보를 확인합니다.\n'취소하기': 등산 일정을 취소합니다."
            },
            "keyboard": {
                "type": "buttons",
                "buttons": ['등산정보 확인하기', '지도 확인하기', '취소하기']
            }
        })

    '''
    # 위 과정까지는 '첫 사용' 유저를 위한 기능.
    # 여기서부터 본격적인 기능 사용.
    if datacontent == '시작하기' or registered_user:
        user_id = received_json_data['user_key']
        activated_data = ActivatedUsers.objects.get(user_id=user_id)
        if not activated_data: # 활성화 데이터가 이미 있으면
            currentTime = time.strftime('%m%d%H%M')
            activated_user = ActivatedUsers(user_id=user_id, first_logged_time=currentTime,
                                            updated_logged_time=currentTime,
                                            phase=11)
            activated_user.save()

            return JsonResponse({
                "message": {
                    'text': '등산하실 산을 입력하여주세요!'
                },
                "keyboard": {
                    "type": "text"
                }
            })

        user_id = received_json_data['user_key']
        activated_data = ActivatedUsers.objects.get(user_id=user_id)
        if not activated_data:
            print('오류 발생: 등록되지 않은 유저 key.')

        user_phase = activated_data.phase
        if user_phase == 11:
            # 글자 수가 2글자 이하이면 경고메시지 출력하는 기능 제작하기.

            print('산 이름 입력중')
            queryset = Mountains.objects.all()
            queryset = queryset.filter(name__contains=datacontent)

            if queryset:
                mountains_list = []
                for model_instance in queryset:
                    mountains_list.append(model_instance.name + ", " + model_instance.location[:-1] + ", " + str(model_instance.code))
                mountains_list.append('다시 입력하기')

                activated_data.phase = 12
                activated_data.save()

                return JsonResponse({
                    "message": {
                        'text': "아래의 결과에서 등산을 원하시는 산을 골라주세요."
                    },
                    "keyboard": {
                        "type": "buttons",
                        "buttons": mountains_list
                    }
                })
            else:
                return JsonResponse({
                    "message": {
                        'text': "검색하신 결과가 없습니다. 다시 한 번 입력해주세요!"
                    },
                    "keyboard": {
                        "type": "text"
                    }
                })
        elif user_phase == 12:
            if datacontent == '다시 입력하기':
                activated_data.phase = 11
                activated_data.save()

                return JsonResponse({
                    "message": {
                        'text': '재입력을 선택하셨습니다. 등산하실 산을 입력하여주세요!'
                    },
                    "keyboard": {
                        "type": "text"
                    }
                })
            else:
                mountain_data = datacontent.split(',')
                print(mountain_data[0])
                print(mountain_data[1][1:])

                # 우선 오늘날짜로 등록
                climbing_data = ClimbingRecord(user_id=user_id, date=time.strftime('%y%m%d'), code=mountain_data[2][1:])
                climbing_data.save()

                activated_data.phase = 2
                activated_data.save()

                return JsonResponse({
                    "message": {
                        'text': "등산일정 등록이 완료되었습니다. 아래의 '확인하기' 버튼을 눌러 등산 정보를 확인하실 수 있습니다."
                    },
                    "keyboard": {
                        "type": "buttons",
                        "buttons": ['확인하기']
                    }
                })


            # 선택된 산을 바탕으로 유저 데이터 등록하기.
        elif user_phase == 2:
            if datacontent == '확인하기':
                print('확인하기 명령 실행')
            elif datacontent == '취소하기':
                activated_data.phase = 11
                activated_data.save()

            return JsonResponse({
                "message": {
                    'text': "'확인하기': 등산 정보를 확인합니다.\n'취소하기': 등산 일정을 취소합니다."
                },
                "keyboard": {
                    "type": "buttons",
                    "buttons": ['확인하기', '취소하기']
                }
            })
            
    print(user_phase)
'''


    return JsonResponse({
        'message': {
            'text': '예상치 못한 종료!'
        }
    })

def show_map(request):
    return render(request, 'map.html', {})