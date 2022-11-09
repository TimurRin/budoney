from datetime import datetime, timedelta


def get_date_transaction_code(date: datetime) -> str:
    return date.strftime("%Y_%m")


def get_today_transaction_code() -> str:
    return datetime.today().strftime("%Y_%m")


def get_today_text() -> str:
    return datetime.today().strftime("%Y-%m-%d")


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
