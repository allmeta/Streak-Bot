import sqlite3
conn = sqlite3.connect('streakbot.db')
c = conn.cursor()
e=  """CREATE TABLE USER (
            ID TEXT NOT NULL,
            SERVERID TEXT NOT NULL,
            LASTJOINED TEXT,
            CURRENT INT NOT NULL,
            TOTAL INT NOT NULL,
            HIGHEST INT NOT NULL,
            DAILY BIT NOT NULL,
            PRIMARY KEY (ID, SERVERID)
        );"""

e2=     """ INSERT INTO USER
            SELECT * FROM USERS;"""
e3=     """DROP TABLE USERS;"""
e4=     """ALTER TABLE USER RENAME TO USERS;"""
c.execute(e) # POG??????????????????????????????
c.execute(e2)
c.execute(e3)
c.execute(e4)
conn.commit()
