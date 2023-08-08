from datetime import datetime, timedelta


def get_date_transaction_code(date: datetime) -> str:
    return date.strftime("%Y_%m")


def get_today_transaction_code() -> str:
    return datetime.today().strftime("%Y_%m")


def get_today_text() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def get_relative_date(date, today=None):
    if not today:
        today = datetime.today()
    days_ago = (today - date).days
    if days_ago == 0:
        return "today"
    elif days_ago == 1:
        return "yesterday"
    elif days_ago == -1:
        return "tomorrow"
    elif days_ago < 0:
        return f"in {abs(days_ago)}d"
    else:
        return f"{days_ago}d ago"


def get_relative_timestamp(timestamp, today=None):
    return get_relative_date(datetime.fromtimestamp(timestamp), today=today)


def get_today_month_timestamp():
    today = datetime.today()
    return int(datetime(today.year, today.month, 1).timestamp())


def monthly_codes_range(start_date: datetime, end_date: datetime):
    so = []
    for n in range(int((end_date - start_date).days)):
        d = start_date + timedelta(n)
        df = d.strftime("%Y_%m")
        if df not in so:
            so.append(df)
            yield df


def date_range(start_date: datetime, end_date: datetime):
    so = []
    for n in range(int((end_date - start_date).days) + 1):
        d = start_date + timedelta(n)
        so.append(d)
        yield d
