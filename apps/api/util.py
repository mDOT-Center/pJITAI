from datetime import datetime


def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()

