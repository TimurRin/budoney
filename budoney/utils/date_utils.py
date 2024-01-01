from datetime import datetime, timedelta


def get_relative_date(date, today=None):
    if not today:
        today = get_today_midnight()
    return (today - date).days


def get_relative_timestamp(timestamp, today=None):
    return get_relative_date(datetime.fromtimestamp(timestamp), today=today)


def get_relative_date_text(date: datetime, today=None, limit=None):
    if not today:
        today = get_today_midnight()
    days_ago = (today - date).days
    if days_ago == 0:
        return "today"
    elif days_ago == 1:
        return "yesterday"
    elif days_ago == -1:
        return "tomorrow"
    elif limit and abs(days_ago) > limit:
        return date.strftime("%Y-%m-%d")
    elif days_ago < 0:
        return f"in {abs(days_ago)}d"
    else:
        return f"{days_ago}d ago"


def get_relative_timestamp_text(timestamp, today=None, limit=None):
    return get_relative_date_text(
        datetime.fromtimestamp(timestamp), today=today, limit=limit
    )


def get_today_midnight():
    today = datetime.today()
    return datetime(today.year, today.month, today.day)


def get_today_midnight_timestamp():
    return int(get_today_midnight().timestamp())


def get_current_month_first_day():
    today = datetime.today()
    return datetime(today.year, today.month, 1)


def get_current_month_first_day_timestamp():
    return int(get_current_month_first_day().timestamp())


def get_month_first_day(year, month):
    return datetime(year, month, 1)


def date_range(start_date: datetime, end_date: datetime):
    so = []
    for n in range(int((end_date - start_date).days) + 1):
        d = start_date + timedelta(n)
        so.append(d)
        yield d


def year_month_range(start: tuple[int, int], end: tuple[int, int]):
    so = []
    for year in range(start[0], end[0] + 1):
        if start[0] == year and end[0] == year:
            month_range = range(start[1], end[1] + 1)
        elif start[0] == year:
            month_range = range(start[1], 13)
        else:
            month_range = range(1, end[1] + 1)
        for month in month_range:
            so.append(get_month_first_day(year, month))
    return so
