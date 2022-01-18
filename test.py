import datetime
import math
import pytz
from datetime import date
from


def utc_to_local(utc_dt):
    local_tz = pytz.timezone('Asia/Yekaterinburg')
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


d0 = date(2020, 2, 23)
d1 = datetime.datetime.now()
delta = d1.date() - d0
week = math.ceil(delta.days / 7)
week = 1 if week % 2 == 0 else 2
print(week)

print(datetime.datetime.today().weekday() + 1)

lesson_end = datetime.datetime.strptime('11.30', '%H.%M').time()
now = utc_to_local(datetime.datetime.now()). time()
print(lesson_end)
print(now)


