import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import pytz


def log(*message):
    print(f'**************** {utc_now()} : {message}')


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def utc_now():
    return datetime.utcnow()


@st.cache_resource
def last_cache_date():
    return utc_now().strftime('%Y-%m-%d')


def local_to_utc(timestamp, source_tz, destin_tz):
    return pytz.timezone(source_tz).localize(timestamp).astimezone(tz=destin_tz)


def convert_datetime_to_string(date_time):
    if not isinstance(date_time, str):
        return date_time.strftime('%Y-%m-%dT%H:%M:%S')
    else:  # if it's already a string, just return as it is
        return date_time


def change_pd_time_zone(datetime_col, source_tz, destin_tz):
    # converting source_tz to destin_tz in a pandas column datetime_col
    if datetime_col.tz is None: # not time zone aware
        datetime_col = datetime_col.tz_localize(source_tz)
    return datetime_col.tz_convert(destin_tz)


def format_firebase_doc_id_string(doc_id):
    return doc_id[:19].replace('T', ' ')


def seconds_until_midnight(dt=None):
    if dt is None:
        dt = utc_now()
    return ((24 - dt.hour - 1) * 60 * 60) + ((60 - dt.minute - 1) * 60) + (60 - dt.second)


def milliseconds_until_midnight(dt=None):
    return 1000 * seconds_until_midnight(dt)


def log_time(times, key):
    now = utc_now()
    if times.get('last'):
        times[key] = (now - times['last']).total_seconds()
    else:
        times[key] = now

    times['last'] = now
    return key, times[key]


def change_index_timezone(df, to_zone=None):
    datetime_col = pd.to_datetime(df.index, format="%Y-%m-%d %H:%M:%S")
    if to_zone is not None:
        datetime_col = change_pd_time_zone(datetime_col, 'UTC', to_zone)
    return datetime_col
