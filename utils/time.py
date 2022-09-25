from datetime import datetime, timedelta

from config.settings import JST


def get_jst_now():
    return datetime.now(JST).replace(tzinfo=None)


def get_jst_from_utc_isoformat(utc_isoformat: str):
    return datetime.fromisoformat(utc_isoformat) + timedelta(hours=9)
