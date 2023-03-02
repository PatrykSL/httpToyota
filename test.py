import datetime

import pyodbc

conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=192.168.2.9,49319;'
                      'Database=Stolarz_AGV_Mroczen;'
                      'UID=sa;PWD=Stolarz123@;')
cursor = conn.cursor()
transport_id = '63e0a21e820282bf9f4bc52e'
transport_new_state = 'Pending'
par_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:000')
curs_text = f"UPDATE dbo.Przejazdy SET Przej_T_ONE_status = '{transport_new_state}', Przej_time_stamp = '{par_now}' WHERE Przej_T_ONE_id = '{transport_id}'"
cursor.execute(curs_text)
conn.commit()
