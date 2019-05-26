

import requests
from datetime import datetime, timezone
import json

class OneSkyAPI:
'''
class for interacting with OneSky USS API.

param token: token string given for signing API commands

'''
    def __init__(self, token):

        self.token = token
        self.session = self.createSession()

    def createSession(self):
        '''create requests session with the appropriate token and headers'''

        session = requests.Session()
        session.headers.update({'Authorization': 'Bearer {}'.format(self.token),
                                'Content-type': 'application/json'})
        return session

    def currentTime(self):
        '''just returns time in proper format'''

        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def createPointFlight(self, name, lon, lat, alt):
        '''
        creates point flight with OneSky and returns a gufi

        param name: name of uav
        param lon: longitude
        param lat: latitude
        param alt: altitude

        returns: global unique flight identifier 
        '''

        url = 'https://utm.onesky.xyz/api/flights/point'
        data = '''{
            "name": "''' + str(name) + '''",
            "description": "This is a description.",
            "aircraftType": "MULTI_ROTOR",
            "altitudeReference": "WGS84",
            "longitude": ''' + str(lon) + ''',
            "latitude": ''' + str(lat) + ''',
            "altitude": ''' + str(alt) + ''',
            "radius": 500,
            "maxHeight": 120,
            "startTime": "''' + datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") + '''",
            "stopTime": "2019-12-03T10:16:40Z"
                    }'''

        response = self.session.post(url, data=data, stream=True)
        if response.status_code != 201:
            print("Something's wrong")
            print(response.status_code)
        else:
            return response.content.decode('utf-8').split('/')[-1]

    def createFlightPlanSimple(self, data):
        '''creates simple flight plan. never been used'''

        url = "https://utm.onesky.xyz/api/flights/pathSimple"
        response = self.session.post(url, data=data)
        if response.status_code != 201:
            print("Something's wrong")
        else:
            return response.content.decode('utf-8').split('/')[-1]

    def updateTelemetry(self, GUFI, lon, lat, alt):
        '''
        method for updating live telemetry to onesky
        '''

        url = 'https://utm.onesky.xyz/api/flights/log/telemetry/' + GUFI
        data = '''{
          "eventType": "TELEMETRY",
          "timestamp": "''' + self.currentTime()+'''",
          "referenceLocation":
          {
             "longitude":''' + str(lon) + ''',
             "latitude":''' + str(lat) + ''',
             "altitude":'''+ str(alt) + '''
          },
          "altitudeReference": "AGL",
          "data": "any extra data"
        }'''

        response = self.session.post(url, data=data, stream=True)


    def listFlights(self):
        '''lists all active flights'''
        url = 'https://utm.onesky.xyz/api/flights/'
        response = self.session.get(url, stream=True)
        return json.loads(response.content.decode('utf-8'))

    def deleteFlight(self, GUFI):
        '''deletes flights'''
        url='https://utm.onesky.xyz/api/flights/' + GUFI
        response = self.session.delete(url,  stream=True)
        return response

if __name__=="__main__":


    '''
    running this module directly will delete all flights associated with the token
    '''
    with open("mwalton.token", "r") as toke:
        token = toke.read()

        utm = OneSkyAPI(token)
        flights = utm.listFlights()

        gufis = [g["id"] for g in flights]

        for g in gufis:
            utm.deleteFlight(g)
