import datetime
import random
import threading
from datetime import date, timedelta
import time
import re
import logging

logging.basicConfig(filename='error.log',
                    format='[%(asctime)s] => %(message)s',
                    level=logging.ERROR)
import telebot
from telebot import types
import csv
import dbConn as db
import keyboards
import settings
from settings import bot

class Job(threading.Thread):
    def __init__(self,fn,timeout):
        super().__init__()
        self.timeout=timeout
        self.fn=fn
        self.daemon=True
    def run(self):
        time.sleep(self.timeout)
        self.fn()


def cleaner():
    while True:
        print('cleaner run')
        adds = db.executeSql('select * from adds')
        ##очистка заявок где дата отправки больше текущей
        ##если будут бесплатные попытки создания просмотра - обнуление
        ##а также дневные обновления

class User():
    TRANSFER = 'transfer'
    MAIN = 'main'
    CITY_IN = 'city_in'
    CITY_TO = 'city_to'
    DATE_IN = 'date_in'
    DATE_TO = 'date_to'
    DESC = 'desc'
    CONTACT = 'contact'
    RES = 0
    ADD_DELY = 'dely'
    ADD_SEND = 'send'
    SEARCH = '3'
    SEARCH_DELY_CITY_IN = '6'
    SEARCH_SEND_CITY_IN = '7'
    SEARCH_DELY_ALL = '8'
    SEARCH_SEND_ALL = '9'
    EDIT = '4'
    MODER = 'moder'
    REFER = '5'

    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.msg = []
        self._state = None
        self.step = None
        self.add = {}
        self.transfer = []
        self.last_adds = []
        self.jobs=[]
        self.select_transfer=0
    def add_job(self,fn,timeout):
        self.jobs.append(Job(fn,timeout))
        self.jobs[-1].start()
    def search(self,criteria=None):
        match self.state:
            case User.SEARCH_SEND_CITY_IN:
                right_sql = f'''SELECT id from adds left join transfer t on id=t."add" 
                where type="dely" 
                and ((city_in="{self.add["city_in"]}" and date_to="{self.add["date_to"]}") 
                or (t.city ="{self.add["city_in"]}" and t.date ="{self.add["date_to"]}"))'''
                alter_sql =f'''SELECT id from adds left join transfer t on id=t."add" 
                where type="dely" 
                and ((city_in="{self.add["city_in"]}" and date_to between date("{self.add["date_to"]}","-3") and date("{self.add["date_to"]}","+3")) 
                or (t.city ="{self.add["city_in"]}" and t.date between date("{self.add["date_to"]}","-3") and date("{self.add["date_to"]}","+3")))'''
            case User.SEARCH_DELY_CITY_IN:
                right_sql = f'''SELECT id from adds left join transfer t on id=t."add" 
                                where type="send" 
                                and ((city_in="{self.add["city_in"]}" and date_to="{self.add["date_to"]}") 
                                or (t.city ="{self.add["city_in"]}" and t.date ="{self.add["date_to"]}"))'''
                dates = str(tuple([(date.fromisoformat(self.add['date_to']) + timedelta(days=i)).isoformat() for i in
                                   range(-2, 3, 1)]))
                alter_sql = f'''SELECT id from adds left join transfer t on id=t."add" 
                                where type="dely" 
                                and ((city_in="{self.add["city_in"]}" and date_to in "{dates}") 
                                or (t.city ="{self.add["city_in"]}" and t.date in "{dates}"))'''
            case User.SEARCH_SEND_ALL:
                id = db.executeSql(f'select id from adds where uid!={self.id} and type="dely"')
                pass
            case User.SEARCH_DELY_ALL:
                id = db.executeSql(f'select id from adds where uid!={self.id} and type="dely"')
                pass
        right_add=[]
        alter_add=[]
        for id in right_sql:
            right_add.append(Add(id[0]))
        for id in alter_sql:
            alter_add.append(Add(id[0]))
        return right_add or None , alter_add or None

    def set_step(self, step):
        self.clear_msg()
        self.step = step

    def get_state(self):
        return self._state

    def set_state(self, state):
        if self._state !=self.TRANSFER:
            if state not in (self.MODER,self.TRANSFER) :
                self.add = {'id': None, 'uid': None, 'city_in': None, 'city_to': None, 'date_in': None, 'date_to': None,
                            'desc': None, 'contact': None, 'type': None, 'refer': None}
        self._state = state
    state = property(fset=set_state, fget=get_state)

    def clear_msg(self):
        for msg in self.msg:
            try:
                bot.delete_message(self.id, msg)
            except Exception as e:
                print(e)
        self.msg = []

    def validate(self, ntitle=True):
        rules = ('city_in', 'city_to', 'date_in', 'date_to', 'desc', 'contact')
        return True if len([k for k in rules if k in self.add]) == len(rules) else False

    def edit(self, step):
        pass

    def save(self):
        if self.validate():

            save= db.executeSql(
                f'insert into adds(uid,city_in,city_to,date_in,date_to,desc,contact,type,refer) values({self.id},'
                f'"{self.add["city_in"]}",'
                f'"{self.add["city_to"]}",'
                f'"{self.add["date_in"]}",'
                f'"{self.add["date_to"]}",'
                f'"{self.add["desc"]}",'
                f'"{self.add["contact"]}",'
                f'"{self.type}",'
                f'"{self.add["refer"]}") returning id,type',True)[0]
            for transfer in self.transfer:
                db.executeSql(f'insert into transfer(add,city,date) values ({save[0]},"{transfer["city"]}","{transfer["date"]}")')
        return save if save else None

    def add_msg(self, id):
        self.msg.append(id)

    def edit_add(self, text):
        db.executeSql(f'update adds set "{self.step}"="{text}" where id={self.add["id"]}')

    def add_data(self, key, value,transfer=False):
        if transfer:
            if len(self.transfer)==self.select_transfer:
                self.transfer.append({})
            self.transfer[self.select_transfer][key]=value
        else:
            self.add[key] = value



    def get_add(self, id):
        for add in self.last_adds:
            if add.id == id:
                return add

    def my_add(self):
        self.last_adds = []
        self.last_adds = [Add(i[0]) for i in db.executeSql(f'select id from adds where uid={self.id}')]
        return self.last_adds

    def moder(self, msg):
        self.clear_msg()
        self.add[self.step] = msg.text
        Add(args=self.add).print([Add.MODER], msg)


class Add():
    EDIT = 'edit'
    SEEN = 'seen'
    COLLAPSE = 'collapse'
    EXPAND = 'expand'
    MODER = 'moder'
    TRANSFER='transfer'

    def __init__(self, id=None, args=None,transfer=[]):

        if id:
            ad = db.executeSql(f'select * from adds where id={id}')[0]
            self.transfer=[{'city':i[0],'date':i[1]} for i in db.executeSql(f'select * from transfer where add = {ad[0]}')] if db.executeSql(f'select * from transfer where add = {ad[0]}') else[]
            self.id = ad[0]
            self.uid = ad[1]
            self.city_in = ad[2]
            self.city_to = ad[3]
            self.date_in = ad[4]
            self.date_to = ad[5]
            self.desc = ad[6]
            self.contact = ad[7]
            self.type = ad[8]
            self.refer = ad[9]

        else:

            self.id = args['id']
            self.uid = args['uid']
            self.city_in = args['city_in']
            self.city_to = args['city_to']
            self.date_in = args['date_in']
            self.date_to = args['date_to']
            self.desc = args['desc']
            self.contact = args['contact']
            self.type = args['type']
            self.refer = args['refer']

        self.isColl = False
        self.modes = []
        self.transfer = transfer


    def expand(self):
        if self.COLLAPSE in self.modes:
            self.modes.pop(self.modes.index(self.COLLAPSE))
            self.modes.append(self.EXPAND)
            self.isColl = False
        user = db.executeSql('select * from users where UID={}'.format(self.uid), True)[0]
        username = user[3]
        text = 'Заявка с ресурса: {}\n'.format(self.refer) if self.refer not in ['None', None, ''] and checkAdm(
            self.uid) else ''
        text += 'Заявка  №{} {} '.format(self.id, '✈')
        text += 'Хочу отправить \n{} - {} : c {} по {}\n{}\nКонтакты: {}'.format(self.city_in, self.city_to,
                                                                                 month(self.date_in),
                                                                                 month(self.date_to),
                                                                                 self.desc if self.desc not in (
                                                                                     'None', None) else 'нет описания',
                                                                                 self.contact) if self.type.find(
            'send') != -1 else 'Могу доставить \n{} - {} : {}\n{}\nКонтакты: {}'.format(self.city_in, self.city_to,
                                                                                        month(self.date_to),
                                                                                        self.desc if self.desc not in (
                                                                                            'None',
                                                                                            None) else 'нет описания',
                                                                                        self.contact)

        reviews = db.executeSql('select * from reviews where contact="{}"'.format(username))
        reviews += db.executeSql('select * from reviews where contact="{}"'.format(self.contact))
        if len(reviews) > 0:
            help = ''
            for r in reviews: help += '@' + r + ', '
            text += '\ntg:@{} \n Помог пользователям:\n{}'.format(username,
                                                                  help) if username != None else '\ntg:[{}](tg://user?id={})\nПомог пользователям:\n{}'.format(
                user[6], user[0], help)
        else:
            if user[1] != 'admin':
                text += '\ntg:@{}'.format(username) if username not in [None,
                                                                        'None'] else '\ntg:[{}](tg://user?id={})'.format(
                    user[6], user[0])
        return text

    def collapse(self):
        if self.EXPAND in self.modes:
            self.modes.pop(self.modes.index(self.EXPAND))
            self.modes.append(self.COLLAPSE)
            self.isColl = True
        text = 'Заявка с ресурса: {}\n'.format(self.refer) if self.refer not in ['None', None, ''] and checkAdm(
            self.uid) else ''
        text += 'Заявка  №{} {}'.format(self.id, '✈')
        text += ' Хочу отправить \n{} - {} : с {} по {}'.format(self.city_in, self.city_to,
                                                                month(self.date_in),
                                                                month(self.date_to)) if self.type.find(
            'send') != -1 else 'Могу доставить\n{} - {} : {}'.format(
            self.city_in, self.city_to, month(self.date_to))
        return text

    def mode(self, mode):
        keyboard = types.InlineKeyboardMarkup()
        for m in mode:
            match m:
                case self.TRANSFER:
                    keyboard.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit'),
                                 types.InlineKeyboardButton('Удалить', callback_data=f'erase'))
                    keyboard.add(types.InlineKeyboardButton('Добавить', callback_data=f'edit'))

                case self.MODER:
                    keyboard.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit'),
                                 types.InlineKeyboardButton('Опубликовать', callback_data=f'save'))

                case self.EXPAND:
                    self.isColl = False
                    keyboard.add(
                        types.InlineKeyboardButton('Скрыть', callback_data=f'collapse@{self.id}'))
                case self.COLLAPSE:
                    self.isColl = True
                    keyboard.add(
                        types.InlineKeyboardButton('Раскрыть', callback_data=f'expand@{self.id}'))
                case self.EDIT:
                    keyboard.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{self.id}'),
                                 types.InlineKeyboardButton('Удалить', callback_data=f'erase@{self.id}'))
                case self.SEEN:
                    keyboard.add(types.InlineKeyboardButton('Отработано', callback_data=f'seen@{possible}@{self.id}'))

        return keyboard

    def print(self, mode, msg):
        if not self.uid:
            self.uid = msg.chat.id
        self.collapse() if self.COLLAPSE in self.modes or True else ''
        self.modes = mode
        send_message(self.expand() if (self.EXPAND in self.modes) or self.MODER else self.collapse(), msg,
                     self.mode(mode), User.RES)
        for tranfer in self.transfer:
            send_message(f'Пересадка {month(tranfer["date"])} в городе {tranfer["city"]}',msg,self.mode([self.TRANSFER]),User.RES)


active_user = {}


def init(uid):
    if not uid in active_user:
        active_user[uid] = User(uid, db.executeSql('select type from users where UID={}'.format(uid))[0][0])


def log(uid, action, title, state):
    date = list(time.localtime())
    user = db.executeSql('select * from users where UID={}'.format(uid))[0]
    username = user[3] if user[3] not in [None, 'None'] else user[6]
    title = re.sub('[^А-ЯЁа-яё0-9 ]+', '', string=str(title))
    dateLog = '{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4], date[5])
    db.executeSql(
        'insert into log(UID,nickname,action,date,title,state) values({},"{}","{}","{}","{}","{}")'.format(uid,
                                                                                                           username,
                                                                                                           action,
                                                                                                           dateLog,
                                                                                                           title,
                                                                                                           state), True)


def exportLog(msg, state=None):
    if state == None:
        logs = db.executeSql('select * from log')
        if len(logs) > 0:

            with open('log.csv', 'w', newline='') as csvfile:
                fieldnames = ['uid', 'nickname', 'action', 'date', 'title']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for log in logs:
                    try:
                        writer.writerow(
                            {'uid': log[1], 'nickname': log[2], 'action': log[3], 'date': log[4], 'title': log[5]})
                    except:
                        pass

            bot.send_document(msg.chat.id, open('log.csv', 'r', newline=''))
        else:
            send_message('пусто', msg, state='log')


def statistic():
    pass


def entity(text):
    chars = ['.', '_', '-', '(', ')', '+']
    print(text)
    for char in chars:
        text = text.replace(char, f'\\{char}')
    print(text)

    return text


def notify(uid, text, state, clear=False):
    if uid:
        if clear == False:
            try:
                if isinstance(uid, list):
                    for id in uid:
                        if len(db.executeSql(
                                'select * from notify where UID={} and state="{}"'.format(id, state))) != 0:
                            lastMsg = \
                            db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id, state))[
                                0][0]
                            db.executeSql('update notify set lastMsg="{}" where UID={} and state="{}"'.format(
                                '{}@{}'.format(lastMsg, bot.send_message(id, text).id), id, state), True)
                        else:
                            db.executeSql('insert into notify(UID,lastMsg,state) values({},"{}","{}")'.format(id,
                                                                                                              bot.send_message(
                                                                                                                  id,
                                                                                                                  text).id,
                                                                                                              state),
                                          True)

                '''else:
                    if len(db.executeSql('select * from notify where UID={} and state="{}"'.format(uid,state)))!=0:
                        lastMsg=db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(uid ,state))[0][0]
                        db.executeSql('update notify set lastMsg="{}" where UID={} and state="{}"'.format('{}@{}'.format(lastMsg,bot.send_message(uid,text).id), uid,state),True)
                    else:
                        db.executeSql('insert into notify(UID,lastMsg,state) values({},"{}","{}")'.format(uid,bot.send_message(uid,text).id),state, True)'''
            except:
                pass
        else:
            try:
                if isinstance(uid, list):
                    for id in uid:
                        lastMsg = \
                        db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id, state))[0][0]
                        if lastMsg.find('@') != -1:
                            for msg in lastMsg.split('@'):
                                bot.delete_message(id, msg)
                        else:
                            bot.delete_message(id, lastMsg)
                '''else:
                    lastMsg = db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(uid, state))[0][0]
                    if lastMsg.find('@') != -1:
                        for msg in lastMsg.split('@'):
                            bot.delete_message(uid, msg)
                    else:
                        bot.delete_message(uid, lastMsg)'''
            except:
                pass


def filterAdds(message, all=False, type=None, keyboardTitle=None):
    if all == False and type == None:
        adds = db.executeSql('select * from adds where UID={} order by date asc'.format(message.chat.id))
    if all == False and type != None:
        adds = db.executeSql(
            'select * from adds where UID={} and type="{}" order by date asc'.format(message.chat.id, type))
    if all == True and type != None:
        adds = db.executeSql(
            'select * from adds where type="{}" order by date asc'.format(type))
    if all == True and type == None:
        adds = db.executeSql(
            'select * from adds order by date asc')
    if len(adds) > 0:

        return adds

    else:
        send_message('Заявок нет', message, state='sendAdds')
        return None


def calendar(id, msg, mode=None, data=None, year_data=None, msgid=None):
    mdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ymonth = [0, 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентьбрь', 'Октябрь',
              'Ноябрь', 'Декабрь']
    mindate = date.today()
    if mode == None:
        keyar = []

        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[mindate.month] + 1):

            keyar.append(types.InlineKeyboardButton(text=f'{i}' if i >= mindate.day else ' ',
                                                    callback_data=f'{id}calendar${msgid}?{mindate.month}@{i}@{mindate.year}' if mindate.day >= c else ' '))
            if i % 7 == 0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)

        key.add(*(types.InlineKeyboardButton(text='<', callback_data=f'c_back@{mindate.month}@{id}'),
                  types.InlineKeyboardButton(text='>', callback_data=f'c_next@{mindate.month}@{id}@{mindate.year}')))
        send_message(f'{ymonth[mindate.month]}:', msg, key)
    if mode == 'next':
        month = ymonth[data + 1]
        # month=ymonth[1]
        keyar = []
        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[data + 1] + 1):
            # for i in range(1, mdays[1] + 1):

            keyar.append(types.InlineKeyboardButton(text=f'{i}',
                                                    callback_data=f'{id}calendar${msgid}?{data + 1}@{i}@{year_data}'))
            if i % 7 == 0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)

        key.add(*(types.InlineKeyboardButton(text='<', callback_data=f'c_back@{data + 1}@{id}'),
                  types.InlineKeyboardButton(text='>', callback_data=f'c_next@{data + 1}@{id}@{year_data}')))
        # send_message(f'month={month}', msg)

        return month, key
    if mode == 'back':
        month = ymonth[data - 1]
        keyar = []

        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[data - 1] + 1):

            keyar.append(types.InlineKeyboardButton(text=f'{i}',
                                                    callback_data=f'{id}calendar${msgid}?{data - 1}@{i}'))
            if i % 7 == 0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)

        key.add(*(types.InlineKeyboardButton(text='<', callback_data=f'c_back@{data - 1}@{id}'),
                  types.InlineKeyboardButton(text='>', callback_data=f'c_next@{data - 1}@{id}')))
        return month, key


def checkAdm(id):
    if db.executeSql('select type from users where UID={}'.format(id))[0][0] == 'admin':
        return True
    else:
        return False


def month(d):
    ymonth = [0, 'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентьбря', 'Октября',
              'Ноября', 'Декабря']
    if d not in (None, 'None'):
        day = date.fromisoformat(d)

        return '{} {} {}'.format(day.day, ymonth[day.month], str(day.year))
    else:
        return ''


def region(r):
    reg = {'tr': 'Турция', 'kz': 'Казахстан', 'ru': 'Россия', 'az': 'Азербайджан', 'th': 'Таиланд',
           'kg': 'Киргизия', 'id': 'Индонезия', 'qa': 'Катар', 'ae': 'Объединенные Арабские Эмираты',
           'am': 'Армения', 'eg': 'Египет', 'us': 'Соединенные Штаты', 'by': 'Беларусь', 'bg': 'Болгария'}
    return reg[r]


def send_message(text, msg, keyboard=None, state=None, foto=None, reply=False, video=None, help_text=None):
    if state:
        active_user[msg.chat.id].set_step(state)

    block = True if len(db.executeSql('select * from blist where UID={}'.format(msg.chat.id))) > 0 else False
    if not block:
        if reply != False:
            print(reply)

            lastMsg = bot.send_message(chat_id=msg.chat.id, text=text, reply_to_message_id=reply,
                                       allow_sending_without_reply=False)
        else:
            if video is not None:
                # bot.send_video(msg.chat.id,open(f'/root/bot/img/{video}.mp4','rb'))
                active_user[msg.chat.id].msg.append(bot.send_video(msg.chat.id, open(f'img/{video}.mp4', 'rb')).id)
            if foto is not None:
                # fotoMsg=bot.send_photo(msg.chat.id,open('/root/bot/img/'+foto+'.png','rb')
                active_user[msg.chat.id].msg.append(bot.send_photo(msg.chat.id, open('img/' + foto + '.png', 'rb')).id)
            if keyboard != None:

                lastMsg = bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=keyboard)
            else:
                lastMsg = bot.send_message(chat_id=msg.chat.id, text=text)
            active_user[msg.chat.id].msg.append(lastMsg.id)
        return lastMsg
    else:
        bot.send_message(chat_id=msg.chat.id, text='Упс, у вас блокировка')


try:

    @bot.message_handler(commands=['reply'])
    def reply(message):
        pass


    @bot.message_handler(commands=['adm'])
    @bot.message_handler(commands=['auth'])
    def auth(message):
        log = message.text.replace('/auth ', '').split(' ')[0]
        pas = message.text.replace('/auth ', '').split(' ')[0]
        if log and pas:
            if db.executeSql('select type from auth where login="{}" and password="{}"'):
                db.executeSql('delete from auth where login="{}"'.format(log), True)
                db.executeSql('update users set type="admin" where UID={}'.format(message.chat.id), True)


    @bot.message_handler(commands=['log'])
    def getLog(message):

        bot.delete_message(message.chat.id, message.id)
        if checkAdm(message.chat.id):
            exportLog(message)


    @bot.message_handler(commands=['login'])
    def login(message):
        log = message.text.replace('/login ', '').split(' ')[0]
        pas = message.text.replace('/login ', '').split(' ')[0]
        if checkAdm(message.chat.id):
            if log and pas:
                db.executeSql('insert into auth(login, password) values("{}","{}")'.format(log, pas), True)


    @bot.message_handler(commands=['start'])
    def welcome(message):
        help_text = '''Этот бот для экономии времени и комфортной помощи друг другу по собственному желанию и возможностям. Никто никому ничем не обязан – ни Вы, ни Вам. Если Вы сомневаетесь в человеке, перевозимом предмете, условиях или же на стадии общения Вам уже некомфортно – просто откажитесь от взаимодействия и будьте спокойны.
    1) Не переводите денег вперед больше, чем Вы готовы подарить. 
    2) Ценные вещи и товары старайтесь не передавать. Если стоит острая необходимость - передавайте и получайте все лично и в аэропорту.
    3) Запрашивайте, а также сами предоставляйте больше информации о себе и поездке. Проверяйте информацию на подлинность - созванивайтесь, задавайте вопросы, предлагайте общение в др. соцсетях и тд. 
    4) Сообщайте админу @asap_delivery о подозрительных пользователях, а также об откровенных мошенниках - мы просто их блокируем. Навсегда.
'''
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        try:
            bot.delete_message(message.chat.id, message.id)
        except:
            pass
        if message.chat.id in active_user:
            active_user[message.chat.id].clear_msg()
        else:
            init(message.chat.id)

        if not db.executeSql('select UID from users where UID={}'.format(message.chat.id)):
            res = date(date.today().year, date.today().month, date.today().day)
            db.executeSql(
                'insert into users(UID,username,countAdds,countViews,firstName,lastUpdate) values({},"{}",{},{},"{}","{}")'.format(
                    message.chat.id, message.from_user.username, 2, 5,
                    '{} {}'.format(message.from_user.first_name, message.from_user.last_name), res))
            send_message(
                'Привет, {} {} выберите задачу, которую я Вам помогу решить'.format(message.from_user.first_name,
                                                                                    message.from_user.last_name),
                message, keyboards.mainK(message.chat.id, checkAdm(message.chat.id)), 'welcome', foto='welcome')
            log(message.chat.id, 'пользователь зарегистрировался', '', 'register')
            adds = db.executeSql('select * from adds')
            for add in adds:

                if add[6].find(message.from_user.username) != -1:
                    db.executeSql('update adds set UID = {} where idAdds={}'.format(message.chat.id, add[1]), True)

        else:

            send_message('Привет, выберите задачу, которую я Вам помогу решить', message,
                         keyboards.mainK(message.chat.id, checkAdm(message.chat.id)), 'welcome', foto='welcome')


    @bot.message_handler(content_types=['text'])
    def start(message):
        log(message.chat.id, 'переход в', message.text, 'btn')
        init(message.chat.id)
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)
        elif message.text == 'Назад':
            welcome(message)
        elif message.text == 'con':

            pass

        elif message.text.find('Хочу отправить') != -1:
            active_user[message.chat.id].state = User.ADD_SEND
            active_user[message.chat.id].add_data('type', User.ADD_SEND)
            bot.register_next_step_handler(
                send_message('Выберите из списка пункт отправления', message, keyboards.getCity(),
                             User.CITY_IN, foto='carCity1'), quest)
        elif message.text.find('Могу доставить') != -1:
            active_user[message.chat.id].state = User.ADD_DELY
            active_user[message.chat.id].add_data('type', User.ADD_DELY)
            bot.register_next_step_handler(
                send_message('Выберите из списка пункт отправления', message, keyboards.getCity(),
                             User.CITY_IN, foto='carCity1'), quest)

        elif message.text.find('Поиск') != -1:
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Искать тех, кто хочет отправить', 'Искать тех, кто хочет доставить')
            keyboard.add('На главную')
            adds = db.executeSql(
                'select * from adds where type order by date asc')
            bot.register_next_step_handler(
                send_message(
                    f'Актуальных предложений по всем направлениям:{len(adds) + 111}\nПопулярные направления:\n🇮🇩Индонезия, 🇦🇪ОАЭ, 🇷🇺Россия и СНГ, 🇺🇲США, 🇹🇭Таиланд, 🇹🇷Турция',
                    message, keyboard), show_sub_menu_search)


        elif message.text.find('Мои заявки') != -1:

            notify([message.chat.id], '', 'adds', True)
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')

            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)
            mode = [Add.EXPAND, Add.EDIT]
            for add in active_user[message.chat.id].my_add():
                add.print(mode, message)


        elif message.text == 'Все заявки' and checkAdm(message.chat.id):
            back(message, 'welcome')
            notify([message.chat.id], '', 'adds', True)
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('Поиск заявки', 'На главную')
            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, state='adds', foto='MyAdds'),
                                           searchAdds)
            adds = filterAdds(message, True)
            if adds != None:
                printAdds(message, adds, None, True, False, True)

        elif message.text.find('Памятка пользователя') != -1:
            help_text = '''Этот бот создан для экономии времени и комфортной помощи друг другу. Поэтому: 
            - Сомневаетесь в человеке, перевозимом предмете, условиях или уже на стадии общения Вам некомфортно – просто откажитесь от взаимодействия и будьте спокойны,
            - Не переводите денег вперед больше, чем Вы готовы подарить, 
            - Ценные вещи и товары старайтесь передавать и получать лично и в аэропорту,
            - Запрашивайте, а также сами предоставляйте больше информации о себе и о поездке, 
            - Сообщайте админу @asap_delivery о подозрительных пользователях, а также об откровенных мошенниках.'''
            back(message, 'welcome')
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('Поощряется', 'Запрещается')
            addsKeyboard.add('На главную')
            bot.register_next_step_handler(
                bot.send_message(
                    message.chat.id,
                    help_text,
                    reply_markup=addsKeyboard
                ), info_for_user
            )
            # send_message(f'{help_text}', message, addsKeyboard)
            # bot.register_next_step_handler(
            #     send_message('Информация:\n❌ Что-то\n✅ Что-то\n💵 Столько', message, addsKeyboard, 'info',
            #                  foto='infoMain'),
            #     searchAdds)



        elif message.text.find('Отзывы') != -1:
            back(message, 'welcome')
            bot.register_next_step_handler(
                send_message('Можете написать отзыв о боте или похвалить пользователя который вам помог', message,
                             keyboards.feedKeyboard, 'feedBack', foto='feedbackMain'), feedBack)
            fb = db.executeSql('select * from feedback where UID={}'.format(message.chat.id))
            fb += db.executeSql('select * from feedback where UID!={}'.format(message.chat.id))
            if len(fb) > 0:

                send_message('Мои отзывы', message,
                             state='feedBack')
                for i in fb:
                    try:
                        user = db.executeSql('select * from users where UID={}'.format(i[0]))[0]
                    except:
                        print(f'отзывы нет юзера {i[0]}')
                    else:
                        username = user[3]
                        text = '\nот:@{}'.format(username) if username != None else '\nот:[{}](tg://user?id={})'.format(
                            user[6], user[0])
                        send_message('{}'.format(i[1]) + text, message,
                                     state='feedBack')
                        if i[2] != None:
                            send_message('Ответ: {}'.format(i[2]), message,
                                         state='feedBack')





        elif message.text.find('Служба поддержки') != -1:

            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')
            bot.register_next_step_handler(
                send_message('Написать администратору\n@asap_delivery', message, addsKeyboard, state='support'),
                support, 'support')
        elif message.text.find('Стоимость') != -1:
            info_for_price(message)





        else:
            send_message('Используйте кнопки', message, False)


    def quest(message):
        bot.delete_message(message.chat.id, message.id)
        state = active_user[message.chat.id].state
        if message.text in ('На главную', '/start'):
            welcome(message)

        match state:
            case User.EDIT | User.MODER:
                if active_user[message.chat.id].add['id']:
                    id = active_user[message.chat.id].add['id']
                    active_user[message.chat.id].edit_add(message.text)
                    tmp = db.executeSql(f'select {active_user[message.chat.id].step} from adds where id={id}')
                    db.executeSql('delete from possibleAdds where sendAdd={} or delyAdd={}'.format(id, id))
                    typeAdd = db.executeSql('select type from adds where id={}'.format(id))[0][0]
                    settings.Thread(target=settings.worker(60).search, name='search',
                                    args=(id, typeAdd, checkAdm(message.chat.id))).start()
                    keyboard = types.ReplyKeyboardMarkup(True, True)
                    keyboard.add('Мои заявки', 'На главную')
                    text = ''
                    match active_user[message.chat.id].step:
                        case User.CITY_IN:
                            text = 'Город отправления изменен'
                        case User.CITY_TO:
                            text = 'Город доставки изменен'
                        case User.DESC:
                            text = 'Описание изменено'
                        case User.CONTACT:
                            text = 'Контактная информация изменена'
                        case User.REFER:
                            text = 'Ресурс изменен'
                    log(message.chat.id, '{} {}->{}'.format(text, tmp, message.text), '', 'edit')
                    send_message(text, message, keyboard, state=User.RES)
                else:
                    active_user[message.chat.id].moder(message)
            case User.SEARCH_SEND_CITY_IN | User.SEARCH_DELY_CITY_IN | User.SEARCH_DELY_ALL | User.SEARCH_SEND_ALL:
                log(message.chat.id, 'поиск  {}'.format(message.text), '', 'search')

            case _:
                match active_user[message.chat.id].step:
                    case User.CITY_IN:
                        if message.text in keyboards.cities:
                            log(message.chat.id, 'выбор города отправки ' + message.text, '', 'city1')
                            if state==User.TRANSFER:
                                active_user[message.chat.id].add_data('city', message.text,True)
                                send_message(f"Укажите дату пересадки", message, state=User.DATE_IN)
                                calendar(1, message)

                            else:
                                active_user[message.chat.id].add_data('city_in', message.text)

                                bot.register_next_step_handler(
                                    send_message('Выберите из списка пункт назначения', message,
                                                 keyboards.getCity(mask=message.text), User.CITY_TO, foto='carCity2'),
                                    quest)
                        else:
                            pass
                    case User.CITY_TO:

                        if message.text in keyboards.cities:

                            log(message.chat.id, 'выбор города доставки ' + message.text, '', 'city2')

                            active_user[message.chat.id].add_data('city_to', message.text)
                            if state==User.ADD_SEND:
                                send_message(f"Выберите интервал времени (макс. 7 дней)", message, state=User.DATE_IN)
                                calendar(1, message)
                            else:
                                send_message(f"Выберите дату доставки", message, state=User.DATE_TO)
                                calendar(1, message)
                        else:
                            pass
                    case User.TRANSFER:

                        if message.text =='Да':
                            active_user[message.chat.id].state=User.TRANSFER

                            active_user[message.chat.id].select_transfer=len(active_user[message.chat.id].transfer)
                            bot.register_next_step_handler(
                            send_message('Выберите из списка пункт отправления', message, keyboards.getCity(),User.CITY_IN, foto='carCity1'), quest)

                        if message.text =='Нет':
                            active_user[message.chat.id].state =User.ADD_DELY
                            bot.register_next_step_handler(
                                send_message('Укажите контакты для связи', message, state=User.CONTACT,
                                             foto='carAddsInfo'),
                                quest)

                    case User.DESC:


                        log(message.chat.id, 'ввел описание', message.text, 'title')
                        active_user[message.chat.id].add_data('desc', message.text)
                        if state == User.ADD_DELY:
                            key = telebot.types.ReplyKeyboardMarkup(True, True)
                            key.add('Да', 'Нет')
                            bot.register_next_step_handler(
                                send_message('Добавить пересадку?', message, key,state=User.TRANSFER,
                                             foto='carAddsInfo'),
                                quest)
                        else:
                            bot.register_next_step_handler(
                                send_message('Укажите контакты для связи', message, state=User.CONTACT, foto='carAddsInfo'),
                                quest)
                    case User.CONTACT:
                        log(message.chat.id, 'ввел контакт ', message.text, 'contact')
                        active_user[message.chat.id].add_data('contact', message.text)
                        if checkAdm(message.chat.id):
                            keyboard = types.ReplyKeyboardMarkup(True, True)
                            keyboard.add('Пропустить', 'На главную')
                            bot.register_next_step_handler(
                                send_message(
                                    'Укажите ресурс заявки', message, keyboard, User.REFER, foto='carAddsInfo'
                                ), quest)
                        else:
                            Add(args=active_user[message.chat.id].add,transfer=active_user[message.chat.id].transfer).print([Add.MODER], message)

                    case User.REFER:
                        if message.text.find('Пропустить') != -1:
                            active_user[message.chat.id].add_data('refer', 'None')
                        else:
                            active_user[message.chat.id].add_data('refer', message.text)
                            save = active_user[message.chat.id].save()
                            if save:
                                keyboard = types.ReplyKeyboardMarkup(True, True)
                                keyboard.add('Мои заявки', 'На главную')
                                bot.register_next_step_handler(
                                    send_message(
                                        f'Заявка создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                                        message, keyboard,
                                        state=User.RES, foto='carCreateDeal'), res)
                                settings.Thread(target=settings.worker(60).search, name='search',
                                                args=(save[0], save[1], checkAdm(message.chat.id))).start()


    def res(message):
        if message.text in ('На главную', '/start'):
            welcome(message)


    def show_menu_bid_and_home(message):
        log(message.chat.id, 'переход в ' + message.text, '', 'btn')
        back(message, 'creatAdds')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)
        elif message.text.find('Мои заявки') != -1:
            back(message, 'creatDealRefer')
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')

            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)

            adds = filterAdds(message)
            if adds != None:
                printAdds(message, adds, None, True, False, True)
        else:
            send_message('Используйте кнопки', message, state='getDely')


    def show_sub_menu_search(message):

        log(message.chat.id, 'переход в ' + message.text, '', 'btn')

        bot.delete_message(message.chat.id, message.id)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Поиск по дате и маршруту', 'Поиск по дате и городу отправления')
        keyboard.add('На главную')
        if message.text == 'На главную':
            welcome(message)
        if message.text == 'Искать тех, кто хочет отправить':
            active_user[message.chat.id].state = User.ADD_SEND
            bot.register_next_step_handler(
                send_message(
                    'Выберите пункт', message, keyboard, 'creatAdds'), getAdds)
        if message.text == 'Искать тех, кто хочет доставить':
            active_user[message.chat.id].state = User.ADD_DELY
            bot.register_next_step_handler(
                send_message(
                    'Выберите пункт', message, keyboard, 'creatAdds'), getAdds)
        '''
        else:
            send_message('Используйте кнопки', message, state='getDely')
        '''


    def getAdds(message):

        log(message.chat.id, 'переход в ' + message.text, '', 'btn')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)
        elif message.text == 'Поиск по дате и городу отправления':
            active_user[message.chat.id].state = User.SEARCH_SEND_CITY_IN if active_user[
                                                                                 message.chat.id].state == User.ADD_SEND else User.SEARCH_DELY_CITY_IN
            bot.register_next_step_handler(
                send_message('Выберите город', message, keyboards.getCity(), User.CITY_IN),
                chooseCity1)
        elif message.text == 'Поиск по дате и маршруту':
            active_user[message.chat.id].state = User.SEARCH_SEND_ALL if active_user[
                                                                             message.chat.id].state == User.ADD_SEND else User.SEARCH_DELY_ALL
            bot.register_next_step_handler(
                send_message('Выберите город', message, keyboards.getCity(), state=User.CITY_IN),
                chooseCity1)
        else:
            send_message('Используйте кнопки', message, state='getDely')


    def getSend(message, type):
        log(message.chat.id, 'getSend', message.text)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('На главную')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'Поиск':

            bot.register_next_step_handler(
                send_message('Выберите город отправки', message, keyboards.transport, 'getSend'),
                chooseCity1, 'searchSend' + type)
        elif message.text == 'На главную':
            welcome(message)
        else:
            send_message('Используйте кнопки', message, state='getSend')


    def getDely(message, type):
        log(message.chat.id, 'getDely', message.text)
        bot.delete_message(message.chat.id, message.id)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('На главную')
        if message.text == 'Поиск':
            bot.register_next_step_handler(
                send_message('Выберите город', message, keyboards.transport, state='getDely'),
                chooseCity1, 'searchDely' + type)
        if message.text == 'На главную':
            welcome(message)
        else:
            send_message('Используйте кнопки', message, state='getDely')


    def sendMsg(message, type):

        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':

            welcome(message)
        elif type.find('feedBackBot') != -1:

            db.executeSql('insert into feedback(UID,title) values({},"{}")'.format(message.chat.id, message.text), True)
            log(message.chat.id, 'добавил отзыв', message.text, 'feedback')
            send_message('Отзыв добален', message, state='sendMsg')
            welcome(message)
        elif type.find('feedBackUser') != -1:
            log(message.chat.id, 'добавил отзыв', message.text, 'feedback')
            user = db.executeSql('select * from users where UID={}'.format(message.chat.id))[0]
            username = user[3] if user[3] != None else user[6]
            db.executeSql('insert into reviews(contact,helpto) values("{}","{}")'.format(message.text, username), True)

            send_message('Отзыв добален', message, state='sendMsg')
            welcome(message)
        elif type.find('support') == 0:
            date = list(time.localtime())
            log(message.chat.id, 'написал поддержке', message.text, 'support')
            date = '{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4], date[5])
            chatId = db.executeSql('select chatId from support where UID = {}'.format(message.chat.id))[0][0]
            db.executeSql(
                'insert into supportMsg(chatId,text,type,date) values({},"{}","{}","{}")'.format(chatId, message.text,
                                                                                                 'user', date), True)

            admId = db.executeSql('select status from support where UID={}'.format(message.chat.id))[0][0]
            send_message(message.text, message, state='support')
            if admId != 'await':
                message.chat.id = admId
                send_message(message.text, message, state='support')


            else:
                db.executeSql('update support set status="{}" where chatId={}'.format('await', chatId), True)

                users = [id[0] for id in db.executeSql('select UID from users where type="admin"')]

                notify(users,
                       'Поступило новое обращение на тех. поддержку. Перейдите на вкладку тех. поддержка чтобы ответить на обращение',
                       'support')

        elif type.find('answerSupport') != -1:
            log(message.chat.id, 'ответил пользователю', message.text, 'support')
            date = list(time.localtime())

            date = '{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4], date[5])
            chatId = type.split('@')[1]

            db.executeSql('insert into supportMsg(chatId,text,type,date) values({},"{}","{}","{}")'.format(chatId,
                                                                                                           message.text,
                                                                                                           'support',
                                                                                                           date), True)

            usrId = db.executeSql('select UID from support where chatId={}'.format(chatId))[0][0]

            usrLastMsg = db.executeSql('select * from msg where UID={} and state="support"'.format(usrId))
            admLastMsg = db.executeSql('select * from msg where UID={} and state="support"'.format(message.chat.id))
            idMsg = admLastMsg[0][2] if admLastMsg[0][2].find('@') == -1 else admLastMsg[0][2].split('@')[-1]
            send_message(message.text, message, state='support', reply=idMsg)

            if len(usrLastMsg) > 0:

                idMsg = usrLastMsg[0][2] if usrLastMsg[0][2].find('@') == -1 else usrLastMsg[0][2].split('@')[-1]
                message.chat.id = usrId
                send_message(message.text, message, state='support', reply=idMsg)

            else:
                db.executeSql('update support set status="{}" where chatId={}'.format('answer', chatId), True)

                notify([usrId], 'Вам ответила служба поддержки!', 'support')

        else:
            send_message('Используйте кнопки', message, state='sendMsg')


    def feedBack(message):
        log(message.chat.id, 'перешел в', message.text, 'btn')
        back(message, 'feedBack')
        if message.text == 'Написать отзыв о боте':
            bot.delete_message(message.chat.id, message.id)
            Keyboard = telebot.types.ReplyKeyboardMarkup(True, True)

            Keyboard.add('На главную')

            bot.register_next_step_handler(
                send_message('Напишите отзыв', message, Keyboard, 'feedBack', foto='feedbackMain'), sendMsg,
                'feedBackBot')
        elif message.text == 'Похвалить пользователя':
            bot.delete_message(message.chat.id, message.id)
            Keyboard = telebot.types.ReplyKeyboardMarkup(True, True)

            Keyboard.add('На главную')

            bot.register_next_step_handler(
                send_message('Введите никнейм или номер пользователя', message, Keyboard, 'feedBack',
                             foto='feedBackUser'), sendMsg,
                'feedBackUser')
        elif message.text == 'На главную':

            welcome(message)
        else:
            send_message('Используйте кнопки', message, state='feedBack')


    def support(message, id):
        log(message.chat.id, 'переход в ' + message.text, '', 'btn')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)


    def info_for_user_submenu(message):
        help_text = '''Этот бот создан для экономии времени и комфортной помощи друг другу. Поэтому: 
            - Сомневаетесь в человеке, перевозимом предмете, условиях или уже на стадии общения Вам некомфортно – просто откажитесь от взаимодействия и будьте спокойны,
            - Не переводите денег вперед больше, чем Вы готовы подарить, 
            - Ценные вещи и товары старайтесь передавать и получать лично и в аэропорту,
            - Запрашивайте, а также сами предоставляйте больше информации о себе и о поездке, 
            - Сообщайте админу @asap_delivery о подозрительных пользователях, а также об откровенных мошенниках.'''
        if message.text == 'Назад':
            keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Поощряется', 'Запрещается')
            keyboard.add('На главную')
            bot.register_next_step_handler(
                bot.send_message(
                    message.chat.id,
                    help_text,
                    reply_markup=keyboard
                ), info_for_user
            )
        if message.text == 'На главную':
            welcome(message)


    def info_for_user(message):
        log(message.chat.id, 'переход в ', message.text, 'btn')
        bot.delete_message(message.chat.id, message.id)

        if message.text == 'На главную':
            welcome(message)
        if message.text == 'Поощряется':
            help_text = '''Максимально поощряется:
            1. Писать в службу поддержки. Нужна помощь- пишите в поддержку, сложная ситуация – пишите в поддержку, сомневаетесь в чем-либо – пишите в поддержку. Просто пишите в поддержку @asap_delivery
            2. Быть ответственными и корректными в ходе взаимодействия. No comment.
            3. Оставлять отзывы админу  и указывать тех, кто Вам помог -  это помогает остальным пользователям, и является основой данного сообщества. Мы против мошенников.
            4. Отказываться от перевозки, если что-то не совпадает. Лицо в переписке и фактический перевозчик/отправитель, легенда о происхождении, качестве и количестве груза, даты поездки и любые сомнительные новые вводные. Это несерьезно и сомнительно. 
            5. Запрашивать/предоставлять билеты и соответствующие документы о поездке.  
            6. Предлагать встречную помощь. Встретить или проводить в аэропорту, помощь с багажом, совместный обед, шоколадка и т.д. Это всегда приятно.  
            7. Заранее оповещать об отмене/переносе поездки или отправки. И тем, с кем есть договоренность, и поддержке – так мы сможем оперативнее предложить иные варианты. Всякое случается и это нормально.
            8. Запрашивать данные о различных соцсетях отправителя/ перевозчика. Также попросить о переписке в сторонней соцсети на случай сомнения. Больше информации – больше данных для анализа личности. Мы всегда против мошенников.'''
            keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Назад')
            keyboard.add('На главную')
            bot.register_next_step_handler(
                bot.send_message(
                    message.chat.id,
                    help_text,
                    reply_markup=keyboard
                ), info_for_user_submenu
            )
            # send_message(f'{help_text}', message, keyboard)
        elif message.text == 'Запрещается':
            help_text = '''Просто запрещается:
            1. Переводить предоплату за доставку. Только по факту доставки. Даже, в случае экстренной необходимости - оплата услуг местных курьерских служб, перемещения доставщика по Вашей просьбе, покупки дополнительного багажного места по Вашей просьбе и всех сопутствующих расходов ПРИ РЕАЛЬНОСТИ ПОЕЗДКИ и обоюдного согласия может быть покрыта ВАМИ через соответствующие приложения или же оплачена по факту доставки.   
            2. Обнадеживать. Указывать приблизительные даты вылета т.е. до приобретения Вами билетов. Мы стараемся решить вопрос срочности, потому и один день играет очень важную роль. 
            3. Без личной проверки брать к перевозке что-либо. Если что-то не так – Вы вправе отказаться. Всегда.
            4. Просить о перевозке чего-либо, в качестве или происхождении чего Вы не уверены. То же касается и передач от третьих лиц. '''
            keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Назад')
            keyboard.add('На главную')
            bot.register_next_step_handler(
                bot.send_message(
                    message.chat.id,
                    help_text,
                    reply_markup=keyboard
                ), info_for_user_submenu
            )
            # send_message(f'{help_text}', message, keyboard)


    def info_for_price(message):
        number = '4276 5500 5052 4258'
        text_for_price = ''' Выбор вида оплаты услуг доставки (деньги/встречная услуга/шоколадка и тд) достигается обоюдным согласием участников каждой отдельной доставки в самом начале переговоров. Поощрить команду бота Вы можете:'''
        log(message.chat.id, 'переход в ', message.text, 'btn')
        # bot.delete_message(message.chat.id, message.id)
        keyboard_menu = types.ReplyKeyboardMarkup(True, True)
        keyboard_menu.add('На главную')
        bot.send_message(message.chat.id, text_for_price, reply_markup=keyboard_menu)
        send_message('- Переводом любой суммы команде бота', message)
        bot.send_message(message.chat.id, f'`{number}`', parse_mode='Markdown')
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row_width = 2
        btn_tooba = types.InlineKeyboardButton(text='tooba', url='https://tooba.com/')
        btn_khabenskogo = types.InlineKeyboardButton(text='Фонд Хабенского',
                                                     url='https://qr.nspk.ru/AS1A007S6L54D2GE8BIP92DSJCED7O6M?type=01&bank=100000000007&crc=037F')
        btn_podari = types.InlineKeyboardButton(text='Фонд Подари Жизнь',
                                                url='https://podari-zhizn.ru/ru/donate')
        btn_help_animals = types.InlineKeyboardButton(
            text='Фонд помощи бездомным животным',
            url='https://dobrovmeste.ru/'
        )

        keyboard.add(btn_tooba, btn_khabenskogo)
        keyboard.add(btn_podari)
        keyboard.add(btn_help_animals)
        send_message('- Переводом любой суммы благотворительному фонду', message, keyboard)

        # bot.send_message(message.chat.id, reply)


    def searchAdds(message):
        log(message.chat.id, 'переход в ', message.text, 'btn')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'Поиск заявки':

            bot.register_next_step_handler(send_message('Введите номер заявки', message, state='searchAdds'), actEdit)

        elif message.text == 'На главную':
            welcome(message)
        elif message.text == 'Назад':
            back(message, 'adds')
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')

            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)
            adds = filterAdds(message)
            if adds != None:
                printAdds(message, adds, None, True, False, True)


        else:
            send_message('Используйте кнопки', message, state='searchAdds')


    def editAdds(message):
        log(message.chat.id, 'перешел в', message.text, 'btn')
        bot.delete_message(message.chat.id, message.id)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Мои заявк', 'На главную')
        if message.text == 'Город оправки':

            bot.register_next_step_handler(
                send_message('Укажите город отправки', message, keyboards.getCity(), User.CITY_IN), quest)

        elif message.text == 'Ресурс':
            bot.register_next_step_handler(
                send_message('Укажите ресурс', message, keyboard, User.REFER), quest)

        elif message.text == 'Город прибытия':

            bot.register_next_step_handler(
                send_message('Укажите город прибытия', message, keyboards.getCity(), User.CITY_TO), quest)
        elif message.text == 'Дату':

            send_message(
                f"Выберите дату",
                message, keyboard, state=User.DATE_IN)
            calendar(1, message)

        elif message.text == 'Контактные данные':

            bot.register_next_step_handler(send_message(
                'Введите котактные данные',
                message, keyboard, state=User.CONTACT)
                , quest)
        elif message.text == 'Описание':

            bot.register_next_step_handler(send_message(
                'Описание',
                message, keyboard, state=User.DESC)
                , quest)
        elif message.text == 'На главную':

            welcome(message)
        else:
            pass


    def password(message, password):
        bot.delete_message(message.chat.id, message.id)
        print(password)
        if message.text == str(password):
            back(message, 'password')
            db.executeSql('update users set countVi={} where UID={}'.format(1, message.chat.id), True)

        else:
            send_message('Не верный пароль', message, state='password')


    @bot.callback_query_handler(func=lambda call: call.data.find('1calendar') == 0)
    def cal(c):
        result = date(
            int(c.data.split('?')[1].split('@')[-1]),
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        if result:

            log(c.message.chat.id, 'указал дату', result, 'date')

            if active_user[c.message.chat.id].step == User.DATE_IN:
                if active_user[c.message.chat.id].state==User.TRANSFER:
                    active_user[c.message.chat.id].add_data('date', result,True)
                    key = telebot.types.ReplyKeyboardMarkup(True, True)
                    key.add('Да', 'Нет')
                    bot.register_next_step_handler(
                        send_message('Добавить пересадку?', c.message, key, state=User.TRANSFER,
                                     foto='carAddsInfo'),
                        quest)
                else:
                    active_user[c.message.chat.id].add_data('date_in', result)
                    # bot.edit_message_text(f'Интервал больше 7 дней.{active_user[c.message.chat.id].add["date_in"]}-',c.message.chat.id,c.message.id)
                    active_user[c.message.chat.id].step = User.DATE_TO

            else:
                if active_user[c.message.chat.id].add['date_in']:
                    if (date.fromisoformat(result) - date.fromisoformat(
                            active_user[c.message.chat.id].add['date_in'])).days > 7:
                        bot.answer_callback_query(c.id,
                                                  f'Интервал больше 7 дней.{active_user[c.message.chat.id].add["date_in"]}',
                                                  False)
                        return

                active_user[c.message.chat.id].add_data('date_to', result)
                keyboard = types.ReplyKeyboardMarkup(True, True)
                if active_user[c.message.chat.id].state == User.ADD_DELY:
                    keyboard.add('На главную')
                    bot.register_next_step_handler(
                        send_message(f"Опишите предмет, который нужно отправить", c.message, keyboard,
                                     state=User.DESC,
                                     foto='carAddsInfo'),
                        quest)
                if active_user[c.message.chat.id].state == User.ADD_SEND:
                    bot.register_next_step_handler(
                        send_message(f"Укажите детали поездки и требования к перевозимому грузу", c.message,
                                     keyboard,
                                     state=User.DESC,
                                     foto='carAddsInfo'),
                        quest)
                if active_user[c.message.chat.id].state in (User.SEARCH_SEND_CITY_IN , User.SEARCH_DELY_CITY_IN , User.SEARCH_DELY_ALL , User.SEARCH_SEND_ALL):
                    active_user[c.message.chat.id].search()


    @bot.callback_query_handler(func=lambda call: call.data.find('save') != -1)
    def save_bid(c):
        if checkAdm(c.message.chat.id) or c.data.find('win') != -1:
            save = active_user[c.message.chat.id].save()
            log(c.message.chat.id, 'нажал', 'создал заявку {} '.format(save[0]), 'add')
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Мои заявки', 'На главную')
            bot.register_next_step_handler(send_message(
                f'Заявка № {save[0]} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                c.message, keyboard, User.RES, foto='carCreateDeal'), res)
            settings.Thread(target=settings.worker(60).search, name='search', args=(save[0], save[1])).start()
        else:
            keys = []
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            sum = a + b
            rnd_code = [random.randint(a if a > b else b, sum + b) for k in range(1, 5)]
            rnd_code[random.randint(0, 3)] = sum
            key_code = types.InlineKeyboardMarkup(row_width=4)
            for code in rnd_code:
                if code == sum:
                    keys.append(types.InlineKeyboardButton(text=f'{code}',
                                                           callback_data=f'save@win'))
                else:
                    keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
            key_code.add(*keys, row_width=4)

            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')
            send_message(
                'Превышен лимит создания заявок. Скоро здесь будет монетизация, нажмите на кнопку с решением {}+{} для разблокировки создания 1 заявки'.format(
                    a, b), c.message, key_code, state=User.RES)


    @bot.callback_query_handler(func=lambda call: call.data.find('c_next') == 0)
    def c_next(c):
        ymonth = [0, 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентьбрь', 'Октябрь',
                  'Ноябряь', 'Декабрь']
        cm = date.today().month
        data = int(c.data.split('@')[1])

        id = int(c.data.split('@')[2])
        year_data = int(c.data.split('@')[-1])
        if data == 12:
            data = 0
            year_data += 1

        if data < cm + 2:
            month, key = calendar(id, c.message, 'next', data, year_data)

            bot.delete_message(c.message.chat.id, c.message.id)
            # send_message('aaa', c.message)
            send_message(month, c.message, key, 'calendar')


    @bot.callback_query_handler(func=lambda call: call.data.find('c_back') == 0)
    def c_back(c):
        ymonth = [0, 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентьбрь', 'Октябрь',
                  'Ноябряь', 'Декабрь']
        cm = date.today().month
        data = int(c.data.split('@')[1])
        id = int(c.data.split('@')[2])
        if data > cm:
            month, key = calendar(id, c.message, 'back', data)
            bot.delete_message(c.message.chat.id, c.message.id)
            send_message(month, c.message, key, 'calendar')


    @bot.callback_query_handler(func=lambda call: call.data.find('show') == 0)
    def show(c):
        print(c)
        inf = c.message.chat.id
        status_release = 'release'
        type_adds = SEARCH_DATA.get(f'{inf}')
        loc_city1 = c.data.split('@')[1]
        loc_city2 = c.data.split('@')[2]
        result = c.data.split('@')[3]
        lCity1 = [k[0] for k in db.executeSql(f'select name from cities where local="{loc_city1}"')]
        lCity2 = [k[0] for k in db.executeSql(f'select name from cities where local="{loc_city2}"')]
        lCity2 = str(lCity2).replace('[', '(').replace(']', ')')
        lCity1 = str(lCity1).replace('[', '(').replace(']', ')')
        altAdds = db.executeSql(
            'select * from adds where city1 in {} and city2 in {} and date ="{}" and status = "{}" and type = "{}"'.format(
                lCity1,
                lCity2,
                result,
                status_release,
                type_adds))
        altAdds += db.executeSql(
            'select * from adds where city1 in {} and city2 in {} and date in ("{}","{}","{}","{}", "{}", "{}", "{}", "{}", "{}", "{}") and status = "{}" and type = "{}"'.format(
                lCity1, lCity2,
                date.fromisoformat(result) + timedelta(days=1), date.fromisoformat(result) + timedelta(days=-1),
                date.fromisoformat(result) + timedelta(days=2), date.fromisoformat(result) + timedelta(days=-2),
                date.fromisoformat(result) + timedelta(days=3), date.fromisoformat(result) + timedelta(days=-3),
                date.fromisoformat(result) + timedelta(days=4), date.fromisoformat(result) + timedelta(days=-4),
                date.fromisoformat(result) + timedelta(days=5), date.fromisoformat(result) + timedelta(days=-5),
                status_release, type_adds))
        printAdds(c.message, altAdds, 'collapse', False)


    @bot.callback_query_handler(func=lambda call: call.data.find('erase') != -1)
    def erase(c):
        bot.answer_callback_query(c.id, 'Запись удалена', False)
        bot.delete_message(c.message.chat.id, c.message.id, 1)
        id = int(c.data.split('@')[1])
        log(c.message.chat.id, 'удалил заявку', str(id), 'search')
        db.executeSql('delete from adds where id="{}"'.format(id, True))
        db.executeSql('delete from possibleAdds where delyAdd={} or sendAdd={}'.format(id, id))


    @bot.callback_query_handler(func=lambda call: call.data.find('edit') == 0)
    def edit(c):

        bot.clear_step_handler_by_chat_id(c.message.chat.id)
        title = False

        id = c.data.split('@')[1] if len(c.data.split('@')) == 2 else None
        if id:
            active_user[c.message.chat.id].state = User.EDIT
            active_user[c.message.chat.id].add_data('id', id)

        else:
            active_user[c.message.chat.id].state = User.MODER

        log(c.message.chat.id, 'нажал', 'изменить заявку ', 'btn')

        bot.register_next_step_handler(
            send_message('Что меняем?', c.message, keyboards.editK(True, checkAdm(c.message.chat.id)), User.EDIT),
            editAdds)


    @bot.callback_query_handler(func=lambda call: call.data.find('seen') == 0)
    def seen(c):
        data = c.data.split('@')

        idAdd = data[1]

        idPos = data[2]
        log(c.message.chat.id, 'нажал', 'отработана заявка ' + idAdd + " и" + idPos, 'btn')
        bot.delete_message(c.message.chat.id, c.message.id)

        db.executeSql(
            'update possibleAdds set active="False" where delyAdd={} and sendAdd={} or sendAdd={} and delyAdd={}'.format(
                idAdd, idPos, idAdd, idPos), True)


    @bot.callback_query_handler(func=lambda call: call.data.find('code') != -1)
    def code(c):
        if c.data == 'win_codeAdd':
            db.executeSql('update users set countAdds={} where UID={}'.format(1, c.message.chat.id), True)
            bot.delete_message(c.message.chat.id, c.message.id)
            bot.register_next_step_handler(
                send_message('Укажите город отправки', c.message, keyboards.getCity(), User.CITY_IN,
                             foto='carCity1'), quest)

        elif c.data == 'wrong_codeAdd':
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('win_codeView') != -1:
            db.executeSql('update users set countViews=1 where UID={}'.format(c.message.chat.id), True)
            c.data = 'expand@{}@win'.format(c.data.split('@')[1])
            expandC(c)
        elif c.data.find('wrong_codeView') != -1:
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('wrong_codeRelease') != -1:
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('win_codeRelease') != -1:
            pass


    @bot.callback_query_handler(func=lambda call: call.data.find('pos') != -1)
    def possibleAdds(c):
        print(c.data)
        back(c.message, 'adds')
        idAdd = c.data.split('@')[1]
        log(c.message.chat.id, 'нажал', 'совпадение заявок ' + idAdd, 'btn')
        addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        addsKeyboard.add('На главную', 'Назад')
        typeAdd = db.executeSql('select type from adds where idAdds={} '.format(idAdd))[0][0]
        sql = 'select sendAdd from possibleAdds where delyAdd={} and active="True"'.format(idAdd) if typeAdd.find(
            'Dely') != -1 else 'select delyAdd from possibleAdds where sendAdd = {} and active="True"'.format(idAdd)
        ids = [k[0] for k in
               db.executeSql(sql)]

        ids = str(ids).replace('[', '(').replace(']', ')')
        bot.register_next_step_handler(send_message(c.message.text, c.message, addsKeyboard, 'adds'), searchAdds)

        adds = db.executeSql('select * from adds where idAdds in {}'.format(ids))
        if checkAdm(c.message.chat.id):
            printAdds(c.message, adds, 'collapse', False, True, False, idAdd)
        else:
            printAdds(c.message, adds, 'collapse', False, True, False)


    @bot.callback_query_handler(func=lambda call: call.data.find('expand') != -1)
    def expandC(c):
        id = int(c.data.split('@')[1])
        add = active_user[c.message.chat.id].get_add(id)
        text = add.expand()
        mode = add.mode(add.modes)
        if checkAdm(c.message.chat.id) or c.data.find('win') != -1:
            bot.edit_message_text(text, c.message.chat.id, c.message.id)
            bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=mode)




        else:
            keys = []
            a = random.randint(1, 50)
            b = random.randint(1, 50)
            sum = a + b
            rnd_code = [random.randint(a if a > b else b, sum + b) for k in range(1, 5)]

            rnd_code[random.randint(0, 3)] = sum
            key_code = types.InlineKeyboardMarkup(row_width=4)
            bot.answer_callback_query(c.id,
                                      'Превышен лимит показов заявок. Скоро здесь будет монетизация, нажмите на кнопку с решением {}+{} для разблокировки 1 показа заявки.'.format(
                                          a, b), show_alert=True)
            for code in rnd_code:
                if code == sum:
                    keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'win_codeView@{id}'))
                else:
                    keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
            key_code.add(*keys, row_width=4)
            bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=key_code)


    @bot.callback_query_handler(func=lambda call: call.data.find('collapse') != -1)
    def collapseC(c):
        id = int(c.data.split('@')[1])
        add = active_user[c.message.chat.id].get_add(id)
        text = add.collapse()
        mode = add.mode(add.modes)

        bot.edit_message_text(text, c.message.chat.id, c.message.id)
        bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=mode)


    @bot.callback_query_handler(func=lambda call: call.data.find('support') != -1)
    def supp(c):
        userId = [id[0] for id in db.executeSql('select UID from users where type ="{}"'.format('admin'))]

        id = c.data.split('@')[1]
        log(c.message.chat.id, 'нажал', 'открыть чат ' + id, 'btn')
        db.executeSql('update support set status="{}" where chatId={}'.format(c.message.chat.id, id), True)
        notify(userId, '', 'support', True)
        msgs = db.executeSql('select * from supportMsg where chatId={} order by date'.format(id))
        if len(msgs) > 0:

            main = send_message(f'Чат №{id}:', c.message, keyboards.supKeyboard, 'support')
            for msg in msgs:
                if msg[2] == 'support':
                    send_message('{}\n{}'.format(msg[1], msg[3]), c.message, state='support', reply=lastmsg)
                else:
                    lastmsg = send_message('{}\n{}'.format(msg[1], msg[3]), c.message, state='support').id
        bot.register_next_step_handler(main, sendMsg, f'answerSupport@{id}')


    bot.polling(none_stop=True)


except Exception:
    logging.exception('error', exc_info=True)
    exit(1)
