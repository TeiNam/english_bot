# utils/time_utils.py
from datetime import datetime, timezone, timedelta
from typing import Union

import pytz

KST = pytz.timezone('Asia/Seoul')


def to_utc(dt: Union[str, datetime]) -> datetime:
    """datetime 객체나 문자열을 UTC timezone이 있는 datetime으로 변환합니다."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    return dt


def get_current_utc() -> datetime:
    """현재 시간을 UTC timezone으로 반환합니다."""
    return datetime.now(timezone.utc)


def format_utc(dt: datetime) -> str:
    """datetime 객체를 ISO 8601 형식의 UTC 문자열로 변환합니다."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def get_today_utc() -> datetime:
    """오늘 날짜의 시작 시간을 UTC로 반환합니다."""
    current = get_current_utc()
    return current.replace(hour=0, minute=0, second=0, microsecond=0)


def get_date_range(days: int) -> tuple[datetime, datetime]:
    """특정 일수 범위의 시작과 끝 시간을 반환합니다."""
    end_time = get_current_utc()
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


def to_kst(dt: Union[str, datetime]) -> datetime:
    """datetime 객체나 문자열을 KST timezone이 있는 datetime으로 변환합니다."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(KST)


def get_current_kst() -> datetime:
    """현재 시간을 KST timezone으로 반환합니다."""
    return datetime.now(KST)


def format_kst(dt: datetime) -> str:
    """datetime 객체를 ISO 8601 형식의 KST 문자열로 변환합니다."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST).isoformat()
