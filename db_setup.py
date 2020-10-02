import sqlite3

conn = sqlite3.connect('streakbot.db')
c = conn.cursor()

# Create table - users
c.execute('''CREATE TABLE users
             ([id] INTEGER PRIMARY KEY,[userid] text,[serverid] text, [joined_today] integer, [current_streak] integer, [total_streak] integer, [highest_streak] integer, [last_joined] date)''')

# Create table - date
c.execute('''CREATE TABLE date
             ([id] INTEGER PRIMARY KEY, [last_date] date)''')
            
conn.commit()