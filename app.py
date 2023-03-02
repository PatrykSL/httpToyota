import datetime
import sys

from flask import Flask, request, jsonify
import requests
import json
import logging
import pyodbc
import urllib3

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__, static_folder='static/', static_url_path='')

url_base = 'https://192.168.2.46'

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',
                    filename=r'\\terminal-serwer\AGVMro\log\serwer_terminal.log',
                    level=logging.INFO)


def get_new_token() -> 'access token':
    client_id = 'stolarz'
    client_secret = "OGI2NmVhYWMtNjZhMC00ZTU5LTgzZTEtMjg3YTk0ZDgyMmQ2"
    access_token_url = f"{url_base}/api/Auth/connect/token"
    payload = {'grant_type': 'client_credentials', 'scope': 'public.transport public.inventory public.notification'}

    token_response = requests.post(access_token_url, data=payload, verify=False, allow_redirects=False, auth=(client_id, client_secret))

    if token_response.status_code != 200:
        logging.error(token_response.text)
        print("Błąd odpowiedzi na żądanie tokena")
        logging.error("Błąd odpowiedzi na żądanie tokena")
    else:
        token_json = json.loads(token_response.text)
        return token_json['access_token']


def send_get_subscription(sub_id):
    token = get_new_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    req_response = requests.get(f'{url_base}/api/v1/subscriptions/{sub_id}', headers=headers, verify=False)
    return req_response.status_code


def send_create_subscription():
    token = get_new_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    data = {
                'sourceType': 'Transports',
                'endpoint': 'http://192.168.2.9/agv/transports',
                'authentication': {
                    'credentials': 'testcred'
                }
            }
    req_response = requests.post(f'{url_base}/api/v1/subscriptions', headers=headers, verify=False, data=json.dumps(data))
    print(req_response.text)
    if req_response.status_code == 201:
        print('okkkk')
        return req_response.json().get('id')
    else:
        print('errrr')
        return 'Error'


def get_subscription():
    try:
        f = open(r'\\terminal-serwer\AGVMro\log\subscription.log', 'r')
        sub_id = f.read()
        f.close()
        if sub_id == '':
            # logging.info(f'Pusty readline')
            subscription = send_create_subscription()
            if subscription != 'Error':
                # logging.info(f'{subscription}')
                f = open(r'\\terminal-serwer\AGVMro\log\subscription.log', 'w')
                f.write(f'{subscription}')
                f.close()
            else:
                logging.info(f'Error')
        else:
            if send_get_subscription(sub_id) != 200:
                # logging.info(f'{send_get_subscription(sub_id)}')
                subscription = send_create_subscription()
                if subscription != 'Error':
                    # logging.info(f'{subscription}')
                    f = open(r'\\terminal-serwer\AGVMro\log\subscription.log', 'w')
                    f.write(f'{subscription}')
                    f.close()
    except Exception as e:
        logging.info(f'{e}')


@app.route('/transports', methods=['GET', 'POST'])
def get_transport_notification():
    try:
        event_type = request.get_json()['eventType']
        transport_id = request.get_json()['eventData']['id']
        reason = request.get_json()['eventData']['state']['reason']
        logging.info(f'ID: {transport_id}, etype: {event_type}')
        if event_type == 'StateUpdated':
            logging.info(f'{request.get_json()}')
            transport_new_state = request.get_json()['eventData']['state']['code']
            conn = pyodbc.connect('Driver={SQL Server};'
                                  'Server=192.168.2.9,49319;'
                                  'Database=Stolarz_AGV_Mroczen;'
                                  'UID=sa;PWD=Stolarz123@;')
            cursor = conn.cursor()
            if reason is None:
                curs_text = f"UPDATE dbo.Przejazdy SET Przej_T_ONE_status = '{transport_new_state}', " \
                            f"Przej_T_ONE_reason = '', " \
                            f"Przej_time_stamp = '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:000')}' " \
                            f"WHERE Przej_T_ONE_id = '{transport_id}'"
                logging.info(f'None: {curs_text}')
                cursor.execute(curs_text)
                conn.commit()
            else:
                curs_text = f"UPDATE dbo.Przejazdy SET Przej_T_ONE_status = '{transport_new_state}', " \
                            f"Przej_T_ONE_reason = '{reason}', " \
                            f"Przej_T_ONE_reason_date = '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:000')}', " \
                            f"Przej_time_stamp = '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:000')}' " \
                            f"WHERE Przej_T_ONE_id = '{transport_id}'"
                logging.info(f'Not none: {curs_text}')
                cursor.execute(curs_text)
                conn.commit()
            text = str(request.get_json()).replace("'",'')
            curs_text = f"INSERT INTO dbo.LogSerwer (log_serv_opis, log_serv_czas) VALUES ('{text}', " \
                        f"'{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S:000')}')"
            logging.info(f'Time/Log: {curs_text}')
            cursor.execute(curs_text)
            conn.commit()
            logging.info(f'Zaktualizowano status przejazdu: {transport_id} na {transport_new_state}')
        return jsonify(result='ok')
    except Exception as e:
        logging.info(f'BTN: {e}')
        print(f'BTN: {e}')
        return jsonify(result=f'{e}')


scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=get_subscription, trigger="interval", hours=1)
scheduler.start()


#if __name__ == '__main__':
#    app.run('192.168.2.9', port=30054, debug=True)

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)