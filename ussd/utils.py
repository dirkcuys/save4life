from datetime import datetime
from django.utils.timezone import utc

def utcnow():
    return datetime.utcnow().replace(tzinfo=utc)


