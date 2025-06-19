from datetime import datetime, timedelta
import requests
import random

BASE_URL = "http://localhost:8445"

SCHOOLS = ["Школа №1"]
CLASSES = ["7А", "8Б", "9В"]
DISCIPLINES = ["Математика", "Русский язык", "Физика", "Биология", "Информатика", "Пропуск по уважительной причине", "Пропуск без уважительной причины", "Пропуск по болезни"]

# Grade pools by performance level
GRADE_PROFILES = {
    "high": [5]*60 + [4]*30 + [3]*10,
    "mid":  [4]*40 + [3]*40 + [2]*20,
    "low":  [3]*30 + [2]*50 + [1]*20,
}

def create_school(name):
    res = requests.post(f"{BASE_URL}/school", params={"facility_name": name})
    if res.status_code == 409:
        res = requests.get(f"{BASE_URL}/school", params={"facility_name": name})
    return res.json()["uuid"]

def create_class(class_name, year, school_uuid):
    res = requests.post(f"{BASE_URL}/class", params={
        "class_name": class_name,
        "start_year": year,
        "school_uuid": school_uuid
    })
    if res.status_code == 409:
        res = requests.get(f"{BASE_URL}/class", params={"uuid": school_uuid})
    return res.json()["uuid"]

def create_user(chat_id, name, role="student"):
    res = requests.post(f"{BASE_URL}/user", params={
        "chat_id": chat_id,
        "name": name,
        "role": role
    })
    if res.status_code == 409:
        res = requests.get(f"{BASE_URL}/user", params={"chat_id": chat_id})
    return res.json()["uuid"]

def join_class(user_uuid, class_uuid):
    requests.post(f"{BASE_URL}/class/student_join", params={
        "user_uuid": user_uuid,
        "class_uuid": class_uuid
    })

def random_datetime_within_year():
    now = datetime.utcnow()
    delta = timedelta(days=random.randint(0, 365), seconds=random.randint(0, 86400))
    return (now - delta).isoformat()

def add_mark(user_uuid, class_uuid, grade_profile):
    for _ in range(random.randint(200, 300)):
        created_at = random_datetime_within_year()
        discipline = random.choice(DISCIPLINES)

        if discipline in [
            "Пропуск по уважительной причине",
            "Пропуск без уважительной причины",
            "Пропуск по болезни"
        ]:
            mark = random.randint(0, 7)  # для пропусков — от 0 до 7 дней
        else:
            mark = random.choice(GRADE_PROFILES[grade_profile])

        requests.post(f"{BASE_URL}/mark", json={
            "user_uuid": user_uuid,
            "class_uuid": class_uuid,
            "discipline": discipline,
            "mark": mark,
            "created_at": created_at
        })


def main():
    school_uuid = create_school(SCHOOLS[0])
    class_uuids = [create_class(name, 2023, school_uuid) for name in CLASSES]

    user_types = (
        ["high"] * 20 +
        ["mid"] * 60 +
        ["low"] * 20
    )
    random.shuffle(user_types)

    for i in range(100):
        chat_id = 10000 + i
        name = f"Ученик{i}"
        user_uuid = create_user(chat_id, name)
        class_uuid = random.choice(class_uuids)
        join_class(user_uuid, class_uuid)
        add_mark(user_uuid, class_uuid, user_types[i])

if __name__ == "__main__":
    main()
