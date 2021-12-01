from modules import run
from datetime import datetime
from time import sleep
import json

if __name__ == "__main__":
    print('please ignore this warning ↑')
    print("this scripts will run in background to check and run the script for new day (at 00:05)")
    try:
        with open('./config.json') as j:
            re = json.load(j)
    except FileNotFoundError:
        re = {
            "buff": True,
            "wb": False,
            "lov": False,
            "dragon": True,
            "friendship": True,
            "inn": True,
            "shop": True,
            "stockage": True,
            "tower": True,
            "lil": False,
            "devices": [],
            "ldconsole": "",
            "time": "00:05"
        }
        with open('./config.json', 'a') as j:
            json.dump(re, j, indent=4)
    while True:
        now = datetime.now().strftime("%H:%M")
        print('checking at '+str(now))
        if str(now) != re['time']:
            sleep(60)
            continue
        run()