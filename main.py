from modules import run
from datetime import datetime
from time import sleep
import json

from sys import stdout
from msvcrt import kbhit, getwche
from time import monotonic

class TimeoutOccurred(Exception):
    pass

def echo(string):
    stdout.write(string)
    stdout.flush()

def inputimeout(prompt='', timeout=30.0):
    echo(prompt)
    begin = monotonic()
    end = begin + timeout
    line = ''
    while monotonic() < end:
        if kbhit():
            c = getwche()
            if c in ('\r', '\n'):
                echo('\r' + '\n')
                return line
            if c == '\003':
                raise KeyboardInterrupt
            if c == '\b':
                line = line[:-1]
                cover = ' ' * len(prompt + line + ' ')
                echo(''.join(['\r', cover, '\r', prompt, line]))
            else:
                line += c
        sleep(0.05)
    echo('\r' + '\n')
    raise TimeoutOccurred


def config():
    buff, wb, lov, dragon, friendship, inn, shop, stockage, tower = (None,)*9
    print('\ndo you want this script to')

    def con(text):
        do = None
        while True:
            do = input(text+'? (Y/N) (leave blank to use previous setting) > ')
            if do.lower().startswith('y'):
                do = True
                break
            elif do.lower().startswith('n'):
                do = False
                break
            elif do == '':
                do = ''
                break
            else:
                print('invalid answer, please try again')
        return do

    buff = con('use exp and gold buff before doing dailies')
    wb = con('auto wb')
    lov = con('auto lov')
    dragon = con('fight dragon')
    friendship = con('exchange friendship token')
    inn = con("do stuff in hero's inn")
    shop = con("buy random stuff in May's shop")
    stockage = con('farm random stuff in stockage')
    tower = con('fight low floor in tower of challenge')

    while True:
        auto_launch = input('\ndo you want this script to auto launch your emulators? (Y/N) > ')
        if auto_launch.lower().startswith('y'):
            ldconsole = input("\nok, please enter/paste the path to LDPlayer\n(right click on LDPlayer folder address and 'copy address as text') (leave blank to use previous setting) > ")
            devices = input('\nok, now enter list of index of your emulators\n(numbers on first column in LDMultiPlayer) (seperate numbers with space) (leave blank to use previous setting) > ')
            break
        elif auto_launch.lower().startswith('n'):
            print('ok')
            break
        else:
            print('invalid answer, please try again')

    fail = False
    with open('./config.json') as r:
        re = json.load(r)

    if buff != '':
        re['buff'] = buff
    if wb != '':
        re['wb'] = wb
    if lov != '':
        re['lov'] = lov
    if dragon != '':
        re['dragon'] = dragon
    if friendship != '':
        re['friendship'] = friendship
    if inn != '':
        re['inn'] = inn
    if shop != '':
        re['shop'] = shop
    if stockage != '':
        re['stockage'] = stockage
    if tower != '':
        re['tower'] = tower

    if ldconsole != '':
        re['ldconsole'] = ldconsole.replace('/', '//')+'\\ldconsole'

    if devices != '':
        devices_ = []
        for num in devices.split():
            if num.isnumeric():
                devices_.append(int(num))
            else:
                fail = True
                print('invalid index in emulators config (index must be an interger), please try again')
                break
        re['devices'] = devices_

    if fail == True:
        return
    
    with open('./config.json', 'w') as w:
        json.dump(re, w, indent=4)


if __name__ == "__main__":
    print('please ignore this warning ↑')
    try:
        print('* press 1 to run this script once')
        print('* press 2 to run this script in background to check and run when new day (at 00:05)')
        print('* press 3 to start config this script')
        auto_daily = inputimeout('> ', timeout=30)
        if auto_daily.isnumeric() == False:
            input('invalid answer, press any key to exit...')
        else:
            try:
                open('./config.json').close()
            except FileNotFoundError:
                print('config not found, creating new one with default settings')
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
                    "ldconsole": ""
                }
                with open('./config.json', 'a') as j:
                    json.dump(re, j, indent=4)
            if int(auto_daily) == 1:
                print('ok, running script for once')
                run()
            elif int(auto_daily) == 2:
                print("ok, this scripts will run in background to check and run the script when new day (at 00:05) (please don't close this window)")
                while True:
                    now = datetime.now().strftime("%H:%M")
                    print('checking at '+str(now))
                    if str(now) != '00:05':
                        sleep(60)
                        continue
                    run()
            elif int(auto_daily) == 3:
                print("ok, starting configuration")
                config()
                input('config complete, press any key to exit...')
            else:
                input('invalid answer, press any key to exit...')
    except TimeoutOccurred:
        print('timeout, running script for once with previous config')
        run()