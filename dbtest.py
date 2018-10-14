import sqlite3
conn = sqlite3.connect('streakbot.db')
c = conn.cursor()
c.execute("UPDATE USERS SET CURRENT = 0, DAILY = 0, TOTAL = 0, HIGHEST = 0")
conn.commit()
