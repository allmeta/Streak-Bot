import sqlite3
from datetime import datetime


def getTodayStr():
    i = datetime.now()
    return "%s/%s/%s" % (i.day, i.month, i.year)


conn = sqlite3.connect('streakbot.db')
c = conn.cursor()

# c.execute("SELECT DATE FROM TODAY")
i = datetime.now()
print(f"Time until execute: {24 - i.hour - i.minute/60}")
