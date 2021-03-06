# -*- coding: utf-8 -*-

import re
import os
from datetime import datetime, timedelta, timezone
from tzlocal import get_localzone

from .exceptions import ArgumentError

# Auxiliary

DATETIME_FORMAT = r'%Y-%m-%d %H:%M:%S %z'


def td2str(td):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours += td.days * 24

    s = ""
    if hours != 0:
        s += "%sh" % hours
    if minutes != 0:
        s += "%s%smin" % (' ' if s else '', minutes)
    if seconds != 0:
        s += "%s%ss" % (' ' if s else '', seconds)
    return s


def dt2str(dt):
    return dt.strftime(DATETIME_FORMAT)


def str2dt(string):
    return datetime.strptime(string, DATETIME_FORMAT)


# The function `now` needs to be mocked when running tests
# In order to have progressing time, we maintain a file with an incrementing
# integer
if os.path.isfile('DIT_TESTING'):

    LOCALZONE = timezone(timedelta(-1, 79200), 'BRST')

    _base_now = datetime(2016, 9, 10, 18, 50, 43, 0, LOCALZONE)

    def now(inc=1):
        with open('DIT_TESTING', 'r') as f:
            i = int(f.read())
        now = _base_now + timedelta(seconds=(i * 40))
        with open('DIT_TESTING', 'w') as f:
            f.write(str(i + inc))
        return now

    def today():
        return now().replace(hour=0,
                             minute=0,
                             second=0,
                             microsecond=0)


else:
    LOCALZONE = get_localzone()

    def now(**kwargs):
        return datetime.now(LOCALZONE)

    def today():
        return now().replace(hour=0,
                             minute=0,
                             second=0,
                             microsecond=0)


def now_str():
    return dt2str(now())


def time_spent_on(logbook):
    time_spent = timedelta()
    for log in logbook:
        if log['out']:
            time_spent += log['out'] - log['in']
        else:
            time_spent += now(inc=0) - log['in']

    return time_spent


def convert_datetimes(data):
    for key in ['created_at', 'updated_at', 'concluded_at']:
        if key in data:
            data[key] = str2dt(data[key])
    logbook = data.get('logbook', [])
    for log in logbook:
        log['in'] = str2dt(log['in'])
        log['out'] = str2dt(log['out']) if log['out'] else None
    return data

# ===========================================
# Filtering


def _cast_values(d, t=int):
    return {k: t(v) if v else 0 for k, v in d.items()}


def interpret_date(string):

    if string in ["now"]:
        return now()
    elif string in ["today", "td"]:
        return today()
    elif string in ["yesterday", "yd"]:
        return today() - timedelta(days=-1)

    # 2018-03-24-15:40
    date_p = r'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})(-(?P<hour>\d{2}):(?P<minute>\d{2}))?$'

    date_m = re.search(date_p, string)
    if date_m:
        return datetime(**_cast_values(date_m.groupdict()), tzinfo=LOCALZONE)

    # 15:40
    time_p = r'^(?P<hours>\d{2}):(?P<minutes>\d{2})$'

    time_m = re.search(time_p, string)
    if time_m:
        return today() + timedelta(**_cast_values(time_m.groupdict()))

    # 2d13h25min
    rel_p = r'^((?P<days>[+-]?\d+)d)?((?P<hours>[+-]?\d+)h)?((?P<minutes>[+-]?\d+)min)?$'

    rel_m = re.search(rel_p, string)
    if string and rel_m:
        return now() + timedelta(**_cast_values(rel_m.groupdict()))

    raise ArgumentError('Unrecognized date/time string: %s' % string)


def apply_filter_where(data, where):
    name = where[0]
    value = where[1]

    properties = data.get('properties', {})

    if name in properties and re.search(value, properties[name]):
        return data
    return {}


def apply_filter_to(data, date):
    if 'created_at' in data and date <= data['created_at']:
        return {}
    logbook = data.get('logbook', [])

    for i in range(len(logbook) + 1):
        if i == len(logbook) or logbook[-i - 1]['out'] <= date:
            break
        elif logbook[-i - 1]['in'] <= date:
            logbook[-i - 1]['out'] = date
            break

    if i > 0:
        data['logbook'] = logbook[:-i]
    return data


def apply_filter_from(data, date):
    if 'concluded_at' in data and date >= data['concluded_at'] or \
            'updated_at' in data and date >= data['updated_at']:
        return {}
    logbook = data.get('logbook', [])

    for i in range(len(logbook) + 1):
        if i == len(logbook) or logbook[i]['in'] >= date:
            break
        elif logbook[i]['out'] >= date:
            logbook[i]['in'] = date
            break
    if i > 0:
        data['logbook'] = logbook[i:]
    return data


def apply_filters(data, filters):

    if data and 'where' in filters:
        data = apply_filter_where(data, filters['where'])

    if data and 'from' in filters:
        data = apply_filter_from(data, filters['from'])

    if data and 'to' in filters:
        data = apply_filter_to(data, filters['to'])

    return data
