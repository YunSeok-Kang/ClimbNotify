
# 한 번에 등록하는 사용자가 많지 않을 것으로 추정되어 우선은 선형적으로 모두 검색함.

adding_users = []

class UserData:
    id = ''
    age = '00대'
    sex = '기타'

def AddUser(user_id):
    new_data = UserData()
    new_data.id = user_id

    adding_users.append(new_data)
    return new_data

def FindUser(user_id):
    for user in adding_users:
        if user.id == user_id:
            return user

    return None

def DeleteUser(user_id):
    for user in adding_users:
        if user.id == user_id:
            adding_users.remove(user)