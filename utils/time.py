from datetime import datetime, timezone, timedelta


def get_current_time(timezone_offset: timezone):
    return datetime.now(timezone_offset).strftime("%Y-%m-%d %H:%M:%S")


def get_current_time_in_taipei():
    taipei_tz = timezone(timedelta(hours=8))
    return get_current_time(taipei_tz)
