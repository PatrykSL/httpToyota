import requests
import json

url_base = 'http://terminal-serwer/agv/transports'

data = {
            'eventType': 'StateUpdateddd',
            'eventData': {
                'id': '1234567890',
                'state': {
                    'code': 'Test'
                }
            }
        }

req_response = requests.post(f'{url_base}', verify=False, data=json.dumps(data))

print(req_response.text)
