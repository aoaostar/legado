import time


def date_format(timestamp: int = time.time()):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
