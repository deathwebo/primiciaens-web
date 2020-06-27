import time

def ellapsed_time(ellapsed_datetime):
    seconds = time.time() - ellapsed_datetime.timestamp()
    days = seconds // 86400
    if days >= 1:
        return 'Hace {} días'.format(int(days))
    h = seconds // 3600
    if h >= 1:
        return 'Hace {} horas'.format(int(h))
    m = seconds % 3600 // 60
    return 'Hace {} minutos'.format(int(m))

