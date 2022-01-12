import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone, utc

def get_offset(*, lat:float, lng:float, date_time:datetime.datetime):
    """Location's time zone offset from UTC in hours.


    Args:
        lat (float): Latitude coordinate
        lng (float): Longitude coordinate
        date_time (datetime.datetime): Datetime object to localize

    Returns:
        float: Time zone offset
    """
    tf = TimezoneFinder()
    tz_target = timezone(tf.certain_timezone_at(lng=lng, lat=lat))
    # ATTENTION: tz_target could be None! handle error case
    s2_target = tz_target.localize(date_time)
    s2_utc = utc.localize(date_time)
    return (s2_utc - s2_target).total_seconds() / 3600