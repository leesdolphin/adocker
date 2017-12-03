import datetime as dt


def as_aware_datetime(utc_timestamp):
    return dt. datetime.fromtimestamp(utc_timestamp, dt.timezone.utc)
