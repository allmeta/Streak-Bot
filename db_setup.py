import sqlite3
from datetime import datetime
from pytz import timezone

conn = sqlite3.connect('streakbot.db')
c = conn.cursor()

# Create table - users
c.execute('''CREATE TABLE users
             ([id] INTEGER PRIMARY KEY,[userid] text,[serverid] text, [joined_today] integer, [current_streak] integer, [total_streak] integer, [highest_streak] integer, [last_joined] date)''')

# Create table - date
c.execute('''CREATE TABLE date
             ([id] INTEGER PRIMARY KEY, [last_date] date)''')

now=datetime.now(timezone('Europe/Oslo'))
c.execute('INSERT INTO date VALUES (0,?)',(f'{now.year}.{now.month}.{now.day}'))

conn.commit()
