from datetime import timedelta


def flow_codes_range(start_date, end_date):
    so = []
    for n in range(int((end_date - start_date).days)):
        d = start_date + timedelta(n)
        df = d.strftime('%Y_%m')    
        if df not in so:
            so.append(df)
            yield df
        
