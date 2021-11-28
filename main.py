from threading import Thread
from random import choice
from time import sleep as slp
from datetime import datetime
from os import mkdir, getcwd, system, path
import logging, json

from sys import stdout, stdin
from msvcrt import kbhit, getwche
from time import monotonic

from ppadb.client import Client
from PIL import Image
from numpy import array
from imagehash import average_hash
from pytesseract import pytesseract
from pytesseract import image_to_string
from langdetect import detect, DetectorFactory
from fuzzywuzzy.process import extractOne
from difflib import SequenceMatcher
from cv2 import bilateralFilter

logger = logging.getLogger()
logger.setLevel(logging.INFO)
pytesseract.tesseract_cmd = ('./tesseract/tesseract.exe')


def update_cache(device):
    try:
        device.shell('screencap -p /sdcard/screencap.png')
        device.pull('/sdcard/screencap.png', './cache/screencap-'+str(device.serial)+'.png')
        im = Image.open('./cache/screencap-'+str(device.serial)+'.png')
    except:
        device.shell('screencap -p /screencap.png')
        device.pull('/screencap.png', './cache/screencap-'+str(device.serial)+'.png')
        im = Image.open('./cache/screencap-'+str(device.serial)+'.png')
    return im


def check_login_rewards(device, once=False):
    # get device resolution
    im = update_cache(device)
    size_ = f"{im.size[0]}x{im.size[1]}"
    with open('./sets.json', encoding='utf-8') as j:
        data = json.load(j)[size_]

    count = 0
    while True:
        im = update_cache(device)

        # pass community page
        im1 = Image.open('./base/login/community.png')
        im2 = crop(im, data['login']['community']['dms'])
        community = check_similar(im1, im2, 10)
        if community == 'similar':
            make_sure_loaded('./base/login/sale.png', device, data['login']['sale']['dms'], data['login']['community']['shell'])

        # pass sale page
        im1 = Image.open('./base/login/sale.png')
        im2 = crop(im, data['login']['sale']['dms'])
        sale = check_similar(im1, im2, 10)
        if sale == 'similar':
            make_sure_loaded('./base/login/attendance.png', device, data['login']['attendance']['dms'], data['login']['sale']['shell'])

        # claim login attendance
        im1 = Image.open('./base/login/attendance.png')
        im2 = crop(im, data['login']['attendance']['dms'])
        attendance = check_similar(im1, im2, 10)
        if attendance == 'similar':
            make_sure_loaded('./base/login/event.png', device, data['login']['event']['dms'], data['login']['attendance']['shell'], second_shell=data['login']['attendance']['second_shell'])
            logger.info(device.serial+': claimed login attendance')

        # pass event page
        im1 = Image.open('./base/login/event.png')
        im2 = crop(im, data['login']['event']['dms'])
        event = check_similar(im1, im2, 10)
        if event == 'similar':
            make_sure_loaded('./base/login/guild_attendance.png', device, data['login']['guild_attendance']['dms'], data['login']['event']['shell'])

        # claim guild attendance
        im1 = Image.open('./base/login/guild_attendance.png')
        im2 = crop(im, data['login']['guild_attendance']['dms'])
        guild_attendance = check_similar(im1, im2, 10)
        if guild_attendance == 'similar':
            for day in data['login']['guild_attendance']['days']:
                device.shell(day)
            device.shell(data['login']['guild_attendance']['row_reward'])
            make_sure_loaded('./base/login/mission_button.png', device, data['login']['mission_button'], data['login']['guild_attendance']['exit'])
            logger.info(device.serial+': claimed guild attendance')

        # claim login accumualated
        im1 = Image.open('./base/login/accumualated.png')
        im2 = crop(im, data['login']['accumualated']['dms'])
        accumualated = check_similar(im1, im2, 10)
        if accumualated == 'similar':
            make_sure_loaded('./base/login/guild_attendance.png', device, data['login']['guild_attendance']['dms'], data['login']['accumualated']['shell'], second_shell=data['login']['accumualated']['second_shell'])
            logger.info(device.serial+': claimed login accumualated')

        # return to main page
        im1 = Image.open('./base/login/mission_button.png')
        im2 = crop(im, data['login']['mission_button'])
        mb = check_similar(im1, im2, 20)
        if mb == 'similar':
            break

        if once == True:
            count+=1
            if count == 7:
                break


def make_sure_loaded(original_img, device, dimensions=None, shell_=None, loop=None, sleep_duration=None, \
        shell_first=False, cutoff=6, second_img=None, third_img=None, oposite=False, second_shell=None, clr=False):
    count = 0
    while True:
        if clr == True:
            check_login_rewards(device, True)
        # do adb shell first if passed
        if shell_ is not None:
            if shell_first is True:
                device.shell(shell_)
        if second_shell is not None:
            if shell_first is True:
                slp(3)
                device.shell(second_shell)
        # update cache
        im = update_cache(device)
        if dimensions is not None:
            cache = crop(im, dimensions)
        else:
            cache = im
        # get data for comparing image
        original = average_hash(Image.open(original_img))
        cache = average_hash(cache)
        # compare
        if original - cache < cutoff:
            if oposite == True:
                pass
            else:
                break
        else:
            if second_img is not None:
                second = average_hash(Image.open(second_img))
                if second - cache < cutoff:
                    break
                else:
                    if third_img is not None:
                        third = average_hash(Image.open(third_img))
                        if third - cache < cutoff:
                            break
            if oposite == True:
                break
            pass
        # adb shell if passed
        if shell_ is not None:
            if shell_first is False:
                device.shell(shell_)
        if second_shell is not None:
            if shell_first is False:
                slp(3)
                device.shell(second_shell)
        # break loop if given arg
        if loop is not None:
            if count == loop:
                return 'loop'
            count+=1
        if sleep_duration is not None:
            slp(sleep_duration)

def crop(img, dimesions):
    # size of the image in pixels (size of original image)
    width, height = img.size
    # cropped image
    im = img.crop((dimesions[0], dimesions[1], width-dimesions[2], height-dimesions[3]))
    return im


def check_similar(img1, img2, cutoff):
    # get data for comparing image
    image1 = average_hash(img1)
    image2 = average_hash(img2)
    # compare
    if image1 - image2 < cutoff:
        return "similar"
    else:
        return "not"
        

def filter(pil_image):
    open_cv_image = array(pil_image.convert('RGB')) 
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return bilateralFilter(open_cv_image, 9, 75, 75)


class Missions:
    def __init__(self):
        self.dragon_ = False
        self.friendship_ = False
        self.inn_ = False
        self.lov_ = False
        self.shop_ = False
        self.stockage_ = False
        self.tower_ = False
        self.wb_ = False
        self.lil_ = False

    def execute(self, device):
        # get device resolution
        im = update_cache(device)
        size_ = f"{im.size[0]}x{im.size[1]}"
        logger.info(device.serial+': size '+size_+' detected')
        with open('./sets.json', encoding='utf-8') as j:
            data = json.load(j)[size_]

        def claim():
            # claim rewards
            count = 0
            while True:
                if count == 9:
                    break
                device.shell(data['claim'][0])
                device.shell(data['claim'][1])
                count+=1

        # open daily mission board
        make_sure_loaded('./base/other/daily.png', device, data['daily']['dms'], data['daily']['shell'], clr=True)

        with open('./config.json') as m:
            config = json.load(m)
        if config['buff'] == True:
            # claim exp and gold buff in etc
            make_sure_loaded('./base/other/etc.png', device, data['buff']['1']['dms'], data['buff']['1']['shell'], second_img='./base/other/etc_2.png', third_img='./base/other/etc_3.png')
            # claim exp buff
            make_sure_loaded('./base/other/use_hot_time.png', device, data['buff']['2']['dms'], data['buff']['2']['shell'], cutoff=10, sleep_duration=1, loop=5)
            make_sure_loaded('./base/other/etc.png', device, data['buff']['1']['dms'], data['buff']['2']['second_shell'], second_img='./base/other/etc_2.png', third_img='./base/other/etc_3.png')
            slp(5)
            # claim gold buff 
            make_sure_loaded('./base/other/use_hot_time.png', device, data['buff']['3']['dms'], data['buff']['3']['shell'], cutoff=10, sleep_duration=1, loop=5)
            make_sure_loaded('./base/other/etc.png', device, data['buff']['1']['dms'], data['buff']['3']['second_shell'], second_img='./base/other/etc_2.png', third_img='./base/other/etc_3.png')

            # click back to mission board
            # open daily mission board
            make_sure_loaded('./base/other/daily.png', device, data['daily']['dms'], data['daily']['second_shell'], shell_first=True)

        claim()
        logger.info(device.serial+': opened and claimed rewards (and exp/gold buff) on daily mission board for the first time')

        # get game language
        im = update_cache(device)
        first_misison = crop(im, data['first mission'])
        image = filter(first_misison)
        text_lang = image_to_string(image).splitlines()[0].lower()
        lang = detect(text_lang)
        if lang == 'en' or lang == 'da' or lang == 'fr':
            lang = 'eng'
        elif lang == 'ja':
            lang = 'jpn'
        elif lang == 'vi':
            lang = 'vie'
        else:

            with open('./languages.json', encoding='utf-8') as j:
                langs = json.load(j)
            lang = None
            langs_ = []
            _langs_ = {}
            for lang__ in langs:
                for _lang_ in langs[lang__]:
                    langs_.append(_lang_)
                    _langs_[_lang_] = lang__
            text_lang = image_to_string(image, lang__).splitlines()[0].lower()
            lang_ = extractOne(text_lang, langs_)
            if lang_[1] > 80:
                lang = _langs_[lang_[0]]

            if lang is None:
                print(device.serial+': language not supported, script eneded')
                return

        # check for undone missions
        not_done = []
        not_done_ = []
        count = 0
        while True:
            im = update_cache(device)
            # get 4 visible missions on mission board
            visible_missions = [crop(im, data['first mission']), crop(im, data['second mission']), \
                crop(im, data['third mission']), crop(im, data['fourth mission'])]
            try:
                if not_done_ == not_done:
                    if count == 20:
                        print(device.serial+': all avalible missions has been completed, script ended')
                        break
                    count+=1
            except:
                pass
            not_done_ = not_done
            count_ = 0
            for mission in visible_missions:
                pil_image = mission
                text = image_to_string(pil_image, lang).splitlines()[0].lower()
                if text == ' ':
                    img = filter(pil_image)
                    text = image_to_string(img, lang).splitlines()[0].lower()
                re = self.do_mission(text, device, data['shortcut'][str(count_)], data, size_, lang)
                if re == 'not':
                    if text not in not_done:
                        not_done.append(text)
                else:
                    make_sure_loaded('./base/other/daily.png', device, data['daily']['dms'], data['daily']['shell'])
                    claim()
                    logger.info(device.serial+': opened and claimed rewards on daily mission board')
                    break
                count_+=1


    def do_mission(self, mission, device, pos, data, res, lang):
        with open('./languages.json', encoding='utf-8') as j:
            lang_data = json.load(j)[lang]
        lst = []
        for name in lang_data:
            lst.append(name)
        ext = extractOne(mission, lst)
        re = lang_data[ext[0]]
        with open('./config.json') as m:
            config = json.load(m)
        if re == 'dragon':
            if config['dragon'] == False:
                return 'not'
            if self.dragon_ == True:
                return 'not'
            return self.dragon(device, pos, data, lang)
        elif re == 'friendship':
            if config['friendship'] == False:
                return 'not'
            if self.friendship_ == True:
                return 'not'
            return self.friendship(device, pos, data)
        elif re == 'inn':
            if config['inn'] == False:
                return 'not'
            if self.inn_ == True:
                return 'not'
            return self.inn(device, pos, data)
        elif re == 'lov':
            if config['lov'] == False:
                return 'not'
            if self.lov_ == True:
                return 'not'
            return self.lov(device, pos, data)
        elif re == 'shop':
            if config['shop'] == False:
                return 'not'
            if self.shop_ == True:
                return 'not'
            return self.shop(device, pos, data)
        elif re == 'stockage':
            if config['stockage'] == False:
                return 'not'
            if self.stockage_ == True:
                return 'not'
            return self.stockage(device, pos, data)
        elif re == 'tower':
            if config['tower'] == False:
                return 'not'
            if self.tower_ == True:
                return 'not'
            return self.tower(device, pos, data, lang)
        elif re == 'wb':
            if config['wb'] == False:
                return 'not'
            if self.wb_ == True:
                return 'not'
            return self.wb(device, pos, data)
        elif re == 'lil':
            if config['lil'] == False:
                return 'not'
            if self.lil_ == True:
                return 'not'
            return self.lil(device, pos, data, res)
        elif re == 'dungeons':
            return 'not'
        elif re == 'stamina':
            return 'not'
        elif re == 'login':
            return 'not'


    def dragon(self, device, position, data, lang):
        print(device.serial+': hunting dragon...')
        logger.info(device.serial+': hunting dragon')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/dragon/raid_list.png', device, data['dragon']['1']['dms'], data['dragon']['1']['shell']+position, cutoff=20, loop=20, sleep_duration=5)
        if shortcut == 'loop':
            self.dragon_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click create red dragon raid
        make_sure_loaded('./base/dragon/red_dra.png', device, data['dragon']['2']['dms'], data['dragon']['2']['shell'])
        logger.info(device.serial+': clicked create dragon raid')

        with open('./languages.json', encoding='utf-8') as j:
            self.dragon_text = json.load(j)[lang]['dragon']
        # change hard level to t6 stage 1
        while True:
            im = update_cache(device)
            pil_image = crop(im, data['dragon']['3']['dms'])
            img = filter(pil_image)
            text = image_to_string(img, lang)
            text_ = text.splitlines()[0].lower().replace(' ', '')
            if SequenceMatcher(None, self.dragon_text, text_).ratio() > 0.9:
                device.shell(data['dragon']['3']['shell'])
                break
            else:
                device.shell(data['dragon']['4']['shell'])
        logger.info(device.serial+': changed to dragon t6 stage 1')

        # click single raid
        make_sure_loaded('./base/dragon/single_raid.png', device, data['dragon']['5']['dms'], data['dragon']['5']['shell'], shell_first=True)
        logger.info(device.serial+': clicked single raid')

        # click enter raid
        make_sure_loaded('./base/dragon/party.png', device, data['dragon']['6']['dms'], data['dragon']['6']['shell'], sleep_duration=0.5, cutoff=15)
        logger.info(device.serial+': clicked enter raid')

        # check avalible party
        # slot 1
        make_sure_loaded('./base/dragon/party_4.png', device, data['dragon']['7']['dms'], data['dragon']['7']['shell'], oposite=True, sleep_duration=0.5)
        # slot 2
        make_sure_loaded('./base/dragon/party_3.png', device, data['dragon']['8']['dms'], data['dragon']['8']['shell'], oposite=True, sleep_duration=0.5)
        # slot 3
        make_sure_loaded('./base/dragon/party_2.png', device, data['dragon']['9']['dms'], data['dragon']['9']['shell'], oposite=True, sleep_duration=0.5)
        # slot 4
        make_sure_loaded('./base/dragon/party_1.png', device, data['dragon']['10']['dms'], data['dragon']['10']['shell'], oposite=True, sleep_duration=0.5)
        # slot 5
        make_sure_loaded('./base/dragon/party_6.png', device, data['dragon']['11']['dms'], data['dragon']['11']['shell'], oposite=True, sleep_duration=0.5)
        # slot 6
        make_sure_loaded('./base/dragon/party_5.png', device, data['dragon']['12']['dms'], data['dragon']['12']['shell'], oposite=True, sleep_duration=0.5)
        logger.info(device.serial+': checked all avalible slots')

        # click start battle
        make_sure_loaded('./base/dragon/battle.png', device, data['dragon']['13']['dms'], data['dragon']['13']['shell'], cutoff=30)
        logger.info(device.serial+': clicked start battle')

        # wait until finish
        make_sure_loaded('./base/dragon/end.png', device, data['dragon']['14']['dms'], sleep_duration=15, cutoff=10)
        logger.info(device.serial+': battle completed')

        # click exit battle
        make_sure_loaded('./base/dragon/party.png', device, data['dragon']['15']['dms'], data['dragon']['15']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': exited battle')

        # click exit
        make_sure_loaded('./base/dragon/my_info.png', device, data['dragon']['16']['dms'], data['dragon']['16']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['dragon']['17']['shell'])
        logger.info(device.serial+': successfully did dragon mission')
        self.dragon_ = True
        return 'success'


    def friendship(self, device, position, data):
        print(device.serial+': exchanging friendship points...')
        logger.info(device.serial+': exchanging friendship points')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/friendship/friends.png', device, data['friendship']['1']['dms'], data['friendship']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.friendship_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click exchange friendship points
        make_sure_loaded('./base/friendship/exchange.png', device, data['friendship']['2']['dms'], data['friendship']['2']['shell'], cutoff=10, shell_first=True, loop=30)
        logger.info(device.serial+': clicked exchange friendship points')

        # click exit
        make_sure_loaded('./base/friendship/my_info.png', device, data['friendship']['3']['dms'], data['friendship']['3']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['friendship']['4']['shell'])
        logger.info(device.serial+': successfully did friendship mission')
        self.friendship_ = True
        return 'success'


    def inn(self, device, position, data):
        print(device.serial+': doing stuffs in inn...')
        logger.info(device.serial+': doing stuffs in inn')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/inn/visit_inn.png', device, data['inn']['1']['dms'], data['inn']['1']['shell']+position, cutoff=20, loop=20, sleep_duration=5)
        if shortcut == 'loop':
            self.inn_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # open inn
        make_sure_loaded('./base/inn/inn.png', device, data['inn']['2']['dms'], data['inn']['2']['shell'], second_img='./base/inn/inn_.png', cutoff=15)
        logger.info(device.serial+': opened inn')

        # give gifts
        def gift():
            slp(2)
            make_sure_loaded('./base/inn/greet.png', device, data['inn']['3']['dms'], data['inn']['3']['shell'], cutoff=10, \
                second_img='./base/inn/greet_.png', third_img='./base/inn/greet__.png', loop=5, shell_first=True)
            make_sure_loaded('./base/inn/start_conversation.png', device, data['inn']['4']['dms'], data['inn']['4']['shell'], cutoff=10, \
                second_img='./base/inn/start_conversation_.png', third_img='./base/inn/start_conversation__.png', loop=5, shell_first=True)
            make_sure_loaded('./base/inn/send_gift.png', device, data['inn']['5']['dms'], data['inn']['5']['shell'], cutoff=10, \
                second_img='./base/inn/send_gift_.png', third_img='./base/inn/send_gift__.png', loop=5, shell_first=True)
        
        # choose hero in inn
        def choose_hero(tap1, tap2):
            make_sure_loaded('./base/inn/inn.png', device, data['inn']['6']['dms'], data['inn']['6']['shell']+str(tap1)+' '+str(tap2),
                shell_first=True, second_img='./base/inn/inn_.png', cutoff=15, second_shell=data['inn']['2']['shell'])

        # give gifts to first hero
        gift()
        logger.info(device.serial+': gave gifts to first hero')
        # give gifts to second hero
        choose_hero(data['inn']['7']['shell'][0], data['inn']['7']['shell'][1])
        gift()
        logger.info(device.serial+': gave gifts to second hero')
        # give gifts to third hero
        choose_hero(data['inn']['8']['shell'][0], data['inn']['8']['shell'][1])
        gift()
        logger.info(device.serial+': gave gifts to third hero')
        # give gifts to fourth hero
        choose_hero(data['inn']['9']['shell'][0], data['inn']['9']['shell'][1])
        gift()
        logger.info(device.serial+': gave gifts to fourth hero')
        # give gifts to fifth hero
        choose_hero(data['inn']['10']['shell'][0], data['inn']['10']['shell'][1])
        gift()
        logger.info(device.serial+': gave gifts to fifth hero')
        # give gifts to sixth hero
        choose_hero(data['inn']['11']['shell'][0], data['inn']['11']['shell'][1])
        gift()
        logger.info(device.serial+': gave gifts to sixth hero')

        # click 'Mini Game'
        count = 0
        while True:
            if count == 6:
                break
            make_sure_loaded('./base/inn/mini_game.png', device, data['inn']['12']['dms'], data['inn']['12']['shell'])
            slp(0.5)
            device.shell(data['inn']['13']['shell'])
            slp(0.5)
            make_sure_loaded('./base/inn/inn.png', device, data['inn']['14']['dms'], data['inn']['14']['shell'], cutoff=20, second_img='./base/inn/inn_.png')
            slp(1)
            count+=1
        logger.info(device.serial+': played minigames')

        # click exit
        make_sure_loaded('./base/inn/visit_inn.png', device, data['inn']['15']['dms'], data['inn']['15']['shell'], cutoff=20, sleep_duration=3)
        make_sure_loaded('./base/inn/my_info.png', device, data['inn']['16']['dms'], data['inn']['16']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['inn']['17']['shell'])
        logger.info(device.serial+': successfully did some stuffs in inn mission')
        self.inn_ = True
        return 'success'


    def lov(self, device, position, data):
        print(device.serial+': suiciding in lov...')
        logger.info(device.serial+': suiciding in lov')
        
        # click mission shortcut
        shortcut = make_sure_loaded('./base/lov/arena.png', device, data['lov']['1']['dms'], data['lov']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.lov_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click select arena
        make_sure_loaded('./base/lov/arenas.png', device, data['lov']['2']['dms'], data['lov']['2']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked select arena')

        # click enter lov
        make_sure_loaded('./base/lov/lov.png', device, data['lov']['3']['dms'], data['lov']['3']['shell'], sleep_duration=1)
        logger.info(device.serial+': clicked enter lov')

        # not sure about this, sometime shortcut brought directly to lov screen but sometime it only brought to arena screen. if it brought to arena screen,
        # comment 3 lines above and uncomment the line below, if oposite keep this.

        # # click mission shortcut
        # make_sure_loaded('./base/lov/lov.png', device, 0, 469, 0, 0, f'input tap {position}')

        # click ready to dual
        make_sure_loaded('./base/lov/party.png', device, data['lov']['4']['dms'], data['lov']['4']['shell'], sleep_duration=0.5, cutoff=20)
        logger.info(device.serial+': clicked ready to dual')

        # check avalible team
        make_sure_loaded('./base/lov/party_.png', device, data['lov']['5']['dms'], data['lov']['5']['shell'], sleep_duration=0.5, oposite=True, cutoff=10)
        logger.info(device.serial+': checked avalible team')

        # click register match
        make_sure_loaded('./base/lov/end.png', device, data['lov']['6']['dms'], data['lov']['6']['shell'], sleep_duration=0.5, cutoff=20, second_shell=data['lov']['6']['second_shell'])
        logger.info(device.serial+': clicked and exited battle')

        # click exit match
        make_sure_loaded('./base/lov/lov.png', device, data['lov']['7']['dms'], data['lov']['7']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': exited match')

        # click exit
        make_sure_loaded('./base/lov/my_info.png', device, data['lov']['8']['dms'], data['lov']['8']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['lov']['9']['shell'])
        logger.info(device.serial+': successfully did lov mission')
        self.lov_ = True
        return 'success'


    def shop(self, device, position, data):
        print(device.serial+': buying stuffs in shop...')
        logger.info(device.serial+': buying stuffs in shop')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/shop/use_shop.png', device, data['shop']['1']['dms'], data['shop']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.shop_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # open shop
        make_sure_loaded('./base/shop/shop.png', device, data['shop']['2']['dms'], data['shop']['2']['shell'])
        logger.info(device.serial+': opened shop')

        # click a random item in shop
        lst = data['shop']['3-0']['shell']
        r = choice(lst)
        device.shell(data['shop']['3-1']['shell']+str(r[0])+' '+str(r[1]))
        logger.info(device.serial+': clicked a random stuff')
        make_sure_loaded('./base/shop/buy.png', device, data['shop']['3-2']['dms'], data['shop']['3-2']['shell']+str(r[0])+' '+str(r[1]), cutoff=1)
        logger.info(device.serial+': clicked a random stuff second time')

        # click buy item
        make_sure_loaded('./base/shop/bought.png', device, data['shop']['4']['dms'], data['shop']['4']['shell'], shell_first=True, cutoff=3)
        logger.info(device.serial+': bought stuff')

        # click exit
        make_sure_loaded('./base/shop/my_info.png', device, data['shop']['5']['dms'], data['shop']['5']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['shop']['6']['shell'])
        logger.info(device.serial+': successfully bought stuffs in shop in inn mission')
        self.shop_ = True
        return 'success'


    def stockage(self, device, position, data):
        print(device.serial+': farming stuffs in stockage...')
        logger.info(device.serial+': farming stuffs in stockage')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/stockage/enter_dungeons.png', device, data['stockage']['1']['dms'], data['stockage']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.stockage_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # open stockage
        make_sure_loaded('./base/stockage/stockage.png', device, data['stockage']['2']['dms'], data['stockage']['2']['shell'], cutoff=9, sleep_duration=0.5)
        logger.info(device.serial+': opened stockage')


        # fragment dungeons
        make_sure_loaded('./base/stockage/fragment_d.png', device, data['stockage']['3']['dms'], data['stockage']['3']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked fragment dungeons')
        # party
        make_sure_loaded('./base/stockage/party.png', device, data['stockage']['4']['dms'], data['stockage']['4']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to party setup')
        # start battle
        make_sure_loaded('./base/stockage/select_battle.png', device, data['stockage']['5']['dms'], data['stockage']['5']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked start battle')
        # auto repeat
        make_sure_loaded('./base/stockage/notice.png', device, data['stockage']['6']['dms'], data['stockage']['6']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked auto repeat')
        # select reward
        make_sure_loaded('./base/stockage/fragment_select_reward.png', device, data['stockage']['7']['dms'], data['stockage']['7']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to select reward')
        # click random reward
        lst = data['stockage']['8-0']['shell']
        r = choice(lst)
        make_sure_loaded('./base/stockage/ok.png', device, data['stockage']['8-1']['dms'], data['stockage']['8-1']['shell']+str(r[0])+' '+str(r[1]), shell_first=True, sleep_duration=0.5)
        logger.info(device.serial+': selected random reward')
        # click ok
        make_sure_loaded('./base/stockage/loading_r.png', device, data['stockage']['9']['dms'], data['stockage']['9']['shell'], loop=15, sleep_duration=0.5, second_shell=data['stockage']['8-1']['shell']+str(r[0])+' '+str(r[1]))
        logger.info(device.serial+': clicked ok to enter battle')
        # wait until finish
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['10']['dms'], sleep_duration=15, cutoff=8)
        slp(5)
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['10']['dms'], sleep_duration=15, cutoff=8)
        logger.info(device.serial+': battle completed')
        # click exit
        make_sure_loaded('./base/stockage/loading.png', device, data['stockage']['11']['dms'], data['stockage']['11']['shell'])
        logger.info(device.serial+': exited from fragment dungeons')


        # skill book dungeon
        make_sure_loaded('./base/stockage/skill_book_d.png', device, data['stockage']['12']['dms'], data['stockage']['12']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked skill book dungeons')
        # party
        make_sure_loaded('./base/stockage/party.png', device, data['stockage']['13']['dms'], data['stockage']['13']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to party setup')
        # start battle
        make_sure_loaded('./base/stockage/select_battle.png', device, data['stockage']['14']['dms'], data['stockage']['14']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked start battle')
        # auto repeat
        make_sure_loaded('./base/stockage/notice.png', device, data['stockage']['15']['dms'], data['stockage']['15']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked auto repeat')
        # select reward
        make_sure_loaded('./base/stockage/exp_select_reward.png', device, data['stockage']['16']['dms'], data['stockage']['16']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to select reward')
        # click random type of book
        lst = data['stockage']['17-0']['shell']
        r = choice(lst)
        device.shell(data['stockage']['17-1']['shell']+str(r[0])+' '+str(r[1]))
        logger.info(device.serial+': selected random book type')
        # click random book
        lst = data['stockage']['18-0']['shell']
        r = choice(lst)
        make_sure_loaded('./base/stockage/ok_.png', device, data['stockage']['18-1']['dms'], data['stockage']['18-1']['shell']+str(r[0])+' '+str(r[1]), shell_first=True, sleep_duration=0.5)
        logger.info(device.serial+': selected random book reward')
        # click ok
        make_sure_loaded('./base/stockage/loading_r.png', device, data['stockage']['19']['dms'], data['stockage']['19']['shell'], loop=15, sleep_duration=0.5, second_shell=data['stockage']['18-1']['shell']+str(r[0])+' '+str(r[1]))
        logger.info(device.serial+': clicked ok to enter battle')
        # wait until finish
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['20']['dms'], sleep_duration=15, cutoff=8)
        slp(5)
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['20']['dms'], sleep_duration=15, cutoff=8)
        logger.info(device.serial+': battle completed')
        # click exit
        make_sure_loaded('./base/stockage/loading.png', device, data['stockage']['21']['dms'], data['stockage']['21']['shell'])
        logger.info(device.serial+': exited from skill book dungeons')


        # exp dungeon
        make_sure_loaded('./base/stockage/exp_d.png', device, data['stockage']['22']['dms'], data['stockage']['22']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked exp dungeons')
        # party
        make_sure_loaded('./base/stockage/party.png', device, data['stockage']['23']['dms'], data['stockage']['23']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to party setup')
        # start battle
        make_sure_loaded('./base/stockage/select_battle.png', device, data['stockage']['24']['dms'], data['stockage']['24']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked start battle')
        # auto repeat
        make_sure_loaded('./base/stockage/notice.png', device, data['stockage']['25']['dms'], data['stockage']['25']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked auto repeat')
        # click ok
        make_sure_loaded('./base/stockage/loading_r.png', device, data['stockage']['26']['dms'], data['stockage']['26']['shell'], loop=10, sleep_duration=0.5)
        logger.info(device.serial+': clicked ok to enter battle')
        # wait until finish
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['27']['dms'], sleep_duration=15, cutoff=8)
        slp(5)
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['27']['dms'], sleep_duration=15, cutoff=8)
        logger.info(device.serial+': battle completed')
        # click exit
        make_sure_loaded('./base/stockage/loading.png', device, data['stockage']['28']['dms'], data['stockage']['28']['shell'])
        logger.info(device.serial+': exited from exp dungeons')


        # gold dungeon
        make_sure_loaded('./base/stockage/gold_d.png', device, data['stockage']['29']['dms'], data['stockage']['29']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked exp dungeons')
        # party
        make_sure_loaded('./base/stockage/party.png', device, data['stockage']['30']['dms'], data['stockage']['30']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked to party setup')
        # start battle
        make_sure_loaded('./base/stockage/select_battle.png', device, data['stockage']['31']['dms'], data['stockage']['31']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked start battle')
        # auto repeat
        make_sure_loaded('./base/stockage/notice.png', device, data['stockage']['32']['dms'], data['stockage']['32']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked auto repeat')
        # click ok
        make_sure_loaded('./base/stockage/loading_r.png', device, data['stockage']['33']['dms'], data['stockage']['33']['shell'], loop=10, sleep_duration=0.5)
        logger.info(device.serial+': clicked ok to enter battle')
        # wait until finish
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['34']['dms'], sleep_duration=15, cutoff=8)
        slp(5)
        make_sure_loaded('./base/stockage/end.png', device, data['stockage']['34']['dms'], sleep_duration=15, cutoff=8)
        logger.info(device.serial+': battle completed')
        # click exit
        make_sure_loaded('./base/stockage/loading.png', device, data['stockage']['35']['dms'], data['stockage']['35']['shell'])
        logger.info(device.serial+': exited from gold dungeons')


        # click exit
        make_sure_loaded('./base/stockage/my_info.png', device, data['stockage']['36']['dms'], data['stockage']['36']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['stockage']['37']['shell'])
        logger.info(device.serial+': successfully did stockage mission')
        self.stockage_ = True
        return 'success'


    def tower(self, device, position, data, lang):
        print(device.serial+': battling in tower...')
        logger.info(device.serial+': battling in tower')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/tower/tower.png', device, data['tower']['1']['dms'], data['tower']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.tower_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click tower of challenge
        make_sure_loaded('./base/tower/toc.png', device, data['tower']['2']['dms'], data['tower']['2']['shell'], sleep_duration=1)
        logger.info(device.serial+': clicked toc')

        # change to floor 1
        with open('./languages.json', encoding='utf-8') as j:
            floor = json.load(j)[lang]['tower']
        while True:
            im = update_cache(device)
            pil_image = crop(im, data['tower']['3']['dms'])
            img = filter(pil_image)
            text = image_to_string(img, lang).splitlines()[0].lower().replace(' ','')
            if SequenceMatcher(None, text, floor).ratio() > 0.9:
                device.shell(data['tower']['5']['shell'])
                break
            else:
                device.shell(data['tower']['4']['shell'])
            slp(1)
        logger.info(device.serial+': changed floor level to 1')

        # click ready for battle
        make_sure_loaded('./base/tower/party.png', device, data['tower']['6']['dms'], data['tower']['6']['shell'])
        logger.info(device.serial+': clicked ready for battle')

        # check avalible team
        # slot 1
        make_sure_loaded('./base/tower/party_4.png', device, data['tower']['7']['dms'], data['tower']['7']['shell'], sleep_duration=0.5, oposite=True)
        # slot 2
        make_sure_loaded('./base/tower/party_3.png', device, data['tower']['8']['dms'], data['tower']['8']['shell'], sleep_duration=0.5, oposite=True)
        # slot 3
        make_sure_loaded('./base/tower/party_2.png', device, data['tower']['9']['dms'], data['tower']['9']['shell'], sleep_duration=0.5, oposite=True)
        # slot 4
        make_sure_loaded('./base/tower/party_1.png', device, data['tower']['10']['dms'], data['tower']['10']['shell'], sleep_duration=0.5, oposite=True)
        logger.info(device.serial+': checked all avalible slots')

        # click start battle to open select battle board
        make_sure_loaded('./base/tower/select_battle.png', device, data['tower']['11']['dms'], data['tower']['11']['shell'], sleep_duration=0.5)
        logger.info(device.serial+': clicked start battle and opened select battle board')

        # click start battle
        make_sure_loaded('./base/tower/end.png', device, data['tower']['12']['dms'], data['tower']['12']['shell'], sleep_duration=0.5, cutoff=10)
        logger.info(device.serial+': clicked start battle')

        # click exit battle
        make_sure_loaded('./base/tower/toc.png', device, data['tower']['2']['dms'], data['tower']['13']['shell'])
        logger.info(device.serial+': exited battle')

        # click exit
        make_sure_loaded('./base/tower/my_info.png', device, data['tower']['14']['dms'], data['tower']['14']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['tower']['15']['shell'])
        logger.info(device.serial+': successfully did toc mission')
        self.tower_ = True
        return 'success'


    def wb(self, device, position, data):
        print(device.serial+': battling world boss...')
        logger.info(device.serial+': battling world boss')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/wb/wb.png', device, data['wb']['1']['dms'], data['wb']['1']['shell']+position, loop=20, cutoff=20, sleep_duration=5)
        if shortcut == 'loop':
            self.wb_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click get ready for battle
        close = make_sure_loaded('./base/wb/party.png', device, data['wb']['2']['dms'], data['wb']['2']['shell'], sleep_duration=2, cutoff=20, loop=20)
        # wb close
        if close == 'loop':
            self.wb_ = True
            # click exit
            make_sure_loaded('./base/wb/my_info.png', device, data['wb']['8']['dms'], data['wb']['8']['shell'], sleep_duration=0.5, clr=True)
            device.shell(data['wb']['9']['shell'])
            return 'success'
        logger.info(device.serial+': loaded from get ready for battle')

        # check avalible team
        make_sure_loaded('./base/wb/a_party.png', device, data['wb']['3']['dms'], data['wb']['3']['shell'], cutoff=20, oposite=True, sleep_duration=0.5)
        logger.info(device.serial+': checked avalible party')

        # click set sub team
        make_sure_loaded('./base/wb/sub_party.png', device, data['wb']['4']['dms'], data['wb']['4']['shell'], sleep_duration=0.5, cutoff=2)
        logger.info(device.serial+': clicked set up sub team')

        # click start battle
        make_sure_loaded('./base/wb/loading.png', device, data['wb']['5']['dms'], data['wb']['5']['shell'], cutoff=10, \
            sleep_duration=0.5, second_shell=data['wb']['5']['second_shell'], loop=10)
        logger.info(device.serial+': clicked start battle')

        # wait until finish
        make_sure_loaded('./base/wb/end.png', device, data['wb']['6']['dms'], sleep_duration=15, cutoff=20)
        logger.info(device.serial+': battle completed')

        # click exit battle
        make_sure_loaded('./base/wb/wb.png', device, data['wb']['7']['dms'], data['wb']['7']['shell'])
        logger.info(device.serial+': exited battle')
        
        # click exit
        make_sure_loaded('./base/wb/my_info.png', device, data['wb']['8']['dms'], data['wb']['8']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['wb']['9']['shell'])
        logger.info(device.serial+': successfully did world boss mission')
        self.wb_ = True
        return 'success'


    def lil(self, device, position, data, res):
        print(device.serial+': feeding lil raider...')
        logger.info(device.serial+': feeding lil raider')

        # click mission shortcut
        shortcut = make_sure_loaded('./base/lil/lil.png', device, data['lil']['1']['dms'], data['lil']['1']['shell']+position, cutoff=20, loop=20, sleep_duration=5)
        if shortcut == 'loop':
            self.lil_ = True
            return 'not'
        logger.info(device.serial+': loaded from mission shortcut')

        # click treats
        make_sure_loaded('./base/lil/treats.png', device, data['lil']['2']['dms'], data['lil']['2']['shell'], cutoff=10, sleep_duration=0.5)
        logger.info(device.serial+': clicked treats')
        # click feed first lil raider
        make_sure_loaded('./base/lil/feeded.png', device, data['lil']['3']['dms'], data['lil']['3']['shell'], second_shell=data['lil']['4']['shell'], shell_first=True, cutoff=20, sleep_duration=0.5)
        logger.info(device.serial+': clicked feed')
        # click exit feeding
        make_sure_loaded('./base/lil/lil.png', device, data['lil']['5']['dms'], data['lil']['5']['shell'], cutoff=10, sleep_duration=0.5)
        logger.info(device.serial+': exit treats')

        # click exit
        make_sure_loaded('./base/lil/my_info.png', device, data['lil']['6']['dms'], data['lil']['6']['shell'], sleep_duration=0.5, clr=True)
        device.shell(data['lil']['7']['shell'])
        logger.info(device.serial+': successfully did lil raider mission')
        self.lil_ = True
        return 'success'


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
        slp(0.05)
    echo('\r' + '\n')
    raise TimeoutOccurred


def load_devices():
    working_dir = getcwd()
    system(working_dir+'\\adb kill-server')
    adb = Client(host="127.0.0.1", port=5037)
    try:
        devices = adb.devices()
    except:
        system(working_dir+'\\adb devices')
        slp(5)
        system(working_dir+'\\adb devices')
        devices = adb.devices()
    return devices, working_dir, adb


def run():
    devices, working_dir, adb = load_devices()
    count=0
    while True:
        if count == 49:
            print('no device was found after 10 retries, script ended')
            break
        if devices == []:
            print('no device was found, retrying...')
            # print('no device was found, launching from config and retrying...')
            # with open('./config.json') as j:
            #     re = json.load(j)
            # for device in re['devices']:
            #     system(working_dir+'\\ldconsole launch --index '+str(device))
            #     print('launched device with index '+str(device))
            system(working_dir+'\\adb devices')
            devices = adb.devices()
        elif str(devices[0].serial).startswith('127'):
            print('no device was found, retrying...')
            devices, working_dir, adb = load_devices()
        else:
            slp(10)
            system(working_dir+'\\adb devices')
            devices = adb.devices()
            print('device(s) detected')
            print('----------------------------------------------------------------\n')
            if path.exists('./cache') == False:
                mkdir('./cache')
            handler = logging.FileHandler("./cache/log.log", "a", "utf-8")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            for device in devices:
                thread = Thread(target=Missions().execute, args=(device,))
                print('executing on device '+device.serial)
                thread.start()
            break
        slp(5)
        count+=9


if __name__ == "__main__":
    print('please ignore this warning ↑')
    try:
        auto_daily = inputimeout('do you want this script to auto run when new day (at 00:05) ? (Y/N) > ', timeout=10)
        if auto_daily.lower().startswith('y'):
            print("ok, this scripts will run in background to check and run the script for new day (at 00:05) (please don't close this window)")
            while True:
                now = datetime.now().strftime("%H:%M")
                print('checking at '+str(now))
                if str(now) != '00:05':
                    slp(60)
                    continue
                run()
        elif auto_daily.lower().startswith('n'):
            print('ok, running script for once')
            run()
        else:
            input('invalid answer, press any key to exit...')
    except TimeoutOccurred:
        print('timeout, running script for once')
        run()