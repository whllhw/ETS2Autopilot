# coding:utf-8
import requests

TELEMETRY_URL = 'http://127.0.0.1:25555/api/ets2/telemetry'


def get_steering_throttle_speed() -> (float, float, float):
    resp = requests.get(TELEMETRY_URL)
    json_resp = resp.json()
    truck_prop = json_resp['truck']
    return _convert_steering(truck_prop['gameSteer']), \
           _convert_throttle(truck_prop['gameThrottle']), \
           truck_prop['speed']


def _convert_steering(steering):
    return steering * 180


def _convert_throttle(throttle):
    return throttle * 100


if __name__ == '__main__':
    import time

    while True:
        time.sleep(1 / 25)
        print(get_steering_throttle_speed())
