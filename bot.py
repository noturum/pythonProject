import random
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



SEARCH_DATA = {}



def collapse(add,id):
    text = 'Заявка с ресурса: {}\n'.format(add[9]) if add[9] not in ['None', None, ''] and checkAdm(
        id) else ''
    text += 'Заявка  №{} {}'.format(add[1], '🚗') if add[7].find('Car') != -1 else 'Заявка  №{} {}'.format(add[1], '✈')
    text += ' Хочу отправить \n{} - {} : {}'.format(add[2], add[3], month(add[4])) if add[7].find(
        'Send') != -1 else 'Могу доставить {}\n{} - {} : {}'.format(
        '(возьму попутчика🙋🏻‍♂️)' if add[8] not in (None, 'False') else '', add[2], add[3], month(add[4]))
    #text = entity(text)
    return text
    
def expand(add,id):
    user = db.executeSql('select * from users where UID={}'.format(add[0]))[0]
    username = user[3]
    text = 'Заявка с ресурса: {}\n'.format(add[9]) if add[9] not in ['None', None, ''] and checkAdm(
        id) else ''
    text += 'Заявка  №{} {}'.format(add[1], '🚗') if add[7].find('Car') != -1 else 'Заявка  №{} {}'.format(add[1],
                                                                                                           '✈')
    text += ' Хочу отправить \n{} - {} : {}\n{}\nКонтакты: {}'.format(add[2], add[3], month(add[4]),add[5] if add[5] not in ('None',None) else '', add[6]) if add[
                                                                                                                7].find(
        'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nКонтакты: {}'.format(
        '(возьму попутчика🙋🏻‍♂️)' if add[8] not in (None, 'False') else '', add[2], add[3], month(add[4]),add[5] if add[5] not in ('None',None) else '', add[6])

    reviews = db.executeSql('select * from reviews where contact="{}"'.format(username))
    reviews += db.executeSql('select * from reviews where contact="{}"'.format(add[6]))
    if len(reviews) > 0:
        help = ''
        for r in reviews: help += '@' + r + ', '
        text += '\ntg:@{} \n Помог пользователям:\n{}'.format(username,
                                                              help) if username != None else '\ntg:[{}](tg://user?id={})\nПомог пользователям:\n{}'.format(
            user[6], user[0], help)

    else:
        if user[1] != 'admin':
            text += '\ntg:@{}'.format(username) if username not in [None,'None']  else '\ntg:[{}](tg://user?id={})'.format(user[6], user[0]) 
            #text += '\ntg:@{}'.format(username) if username not in [None, 'None'] else ''
    #text = entity(text)
    return text


def printAdds(message, adds, folding=None, edit=False, count=False, possible=False,seen=None, mid=None):
    
    id = message.chat.id

    for add in adds:

            keyboard = types.InlineKeyboardMarkup()
            if edit:
                keyboard.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{add[1]}'),
                            types.InlineKeyboardButton('Удалить', callback_data=f'erase@{add[1]}'))

            if seen != None:
                keyboard.add(types.InlineKeyboardButton('Отработано', callback_data=f'seen@{possible}@{add[1]}'))
            if possible:
                sql= 'select * from possibleAdds where sendAdd = {} and active="True"'.format(add[1]) if add[7].find('Send')!=-1 else  'select * from possibleAdds where delyAdd = {} and active="True"'.format(add[1])
                posAdds=db.executeSql(sql)
                if len(posAdds) > 0:
                    keyPosAdd = types.InlineKeyboardButton(text='Есть совпадения ({})'.format(len(posAdds)),
                                                        callback_data='posAdd@{}'.format(add[1]))
                    keyboard.add(keyPosAdd)


            if folding != None :
                call = f'expand/' if folding == 'expand' else 'collapse/'
                call += 'Count/' if count else 'Nocount/'
                call += 'Seen' if seen!=None else 'Noseen'
                call+=f'/{seen}/'
                call+='Edit/' if edit else ''
                call += f'@{str(add[1])}'

                if folding == 'expand':
                    text = expand(add,id)

                    keyboard.add(
                        types.InlineKeyboardButton('Скрыть', callback_data=call))
                else:
                    
                    text = collapse(add,id)
                    keyboard.add(
                        types.InlineKeyboardButton('Показать информацию', callback_data=call))
                    
                if mid!=None:
                    bot.edit_message_text(text, id,
                                        mid)
                    bot.edit_message_reply_markup(id, mid, reply_markup=keyboard)
                else:
                    # bot.delete_message(message.chat.id, message.message_id) 
                    

                    send_message(
                        text,
                        message,
                        keyboard,
                        state='adds')
                    

            else:
                text = expand(add,id)
                # bot.delete_message(message.chat.id, message.message_id) 
                send_message(
                    text,
                    message,
                    keyboard,
                    state='adds')
def myAdds(message):
    adds = db.executeSql('select * from adds '.format(message.chat.id))
    for ad in adds:

        user = db.executeSql('select * from users where UID={}'.format(ad[0]))[0]
        username = user[3]
        text = 'Заявка с ресурса: {}\n'.format(ad[9]) if ad[9] not in ['None', None, ''] and checkAdm(
            message.chat.id) else ''
        text = 'Заявка  №{} {}'.format(ad[1], '🚗') if ad[7].find('Car') != -1 else 'Заявка  №{} {}'.format(ad[1], '✈')
        text += ' Хочу отправить \n{} - {} : {}\nтел. {}'.format(ad[2], ad[3], month(ad[4]), ad[6]) if ad[7].find(
            'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\nтел. {}'.format(
            '(возьму попутчика🙋🏻‍♂️)' if ad[8] not in (None, 'False') else '', ad[2], ad[3], month(ad[4]), ad[6])
        if text.find('отправить')!=-1 :

            posDelyAdds = db.executeSql('select * from possibleAdds where sendAdd = {} and active="True"'.format(ad[1]))


            if len(posDelyAdds)>0:

                if ad[1]==posDelyAdds[0][1]:
                    print('poss')
                    keyPosAdd = types.InlineKeyboardButton(text='Могут доставить ({})'.format(len(posDelyAdds)), callback_data='posSendAdd@{}'.format(ad[1]))
                    expandK.add(keyPosAdd)


        if text.find('доставить')!=-1 :

            posSendAdds = db.executeSql('select * from possibleAdds where delyAdd = {} and active="True"'.format(ad[1]))

            if len(posSendAdds) > 0:
                if ad[1]==posSendAdds[0][2]:
                    keyPosAdd = types.InlineKeyboardButton(text='Хотят отправить ({})'.format(len(posSendAdds)), callback_data='posDelyAdd@{}'.format(ad[1]))
                    expandK.add(keyPosAdd)


        text += '\ntg:@{}'.format(username)
        text = entity(text)
        expandK = types.InlineKeyboardMarkup()

        expandK.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{ad[1]}'),
                        types.InlineKeyboardButton('Удалить', callback_data=f'erase@{ad[1]}'))
        send_message(
            text,
            message,
            expandK,
            state='adds')

def log(uid,action,title,state):
    date = list(time.localtime())
    user = db.executeSql('select * from users where UID={}'.format(uid))[0]
    username = user[3] if user[3] not in [None,'None'] else user[6]
    title=re.sub('[^А-ЯЁа-яё0-9 ]+','',string=str(title))
    dateLog='{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4],date[5])
    db.executeSql('insert into log(UID,nickname,action,date,title,state) values({},"{}","{}","{}","{}","{}")'.format(uid,username,action,dateLog,title,state),True)

def exportLog(msg,state=None):

    if state ==None:
        logs=db.executeSql('select * from log')
        if len(logs)>0:


            with open('log.csv', 'w', newline='') as csvfile:
                fieldnames = ['uid', 'nickname','action','date','title']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()

                for log in logs:
                    try:
                        writer.writerow({'uid': log[1], 'nickname': log[2],'action':log[3],'date':log[4],'title':log[5]})
                    except:
                        pass

            bot.send_document(msg.chat.id,open('log.csv', 'r', newline=''))
        else:
            send_message('пусто',msg,state='log')

def statistic():
    pass

def entity(text):
    chars=['.','_','-','(',')','+']
    print(text)
    for char in chars:
        text=text.replace(char,f'\\{char}')
    print(text)



    return text


def notify(uid,text,state,clear=False):
    if uid:
        if clear==False:
            try:
                if isinstance(uid,list):
                    for id in uid:
                        if len(db.executeSql('select * from notify where UID={} and state="{}"'.format(id,state)))!=0:
                            lastMsg=db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id,state))[0][0]
                            db.executeSql('update notify set lastMsg="{}" where UID={} and state="{}"'.format('{}@{}'.format(lastMsg,bot.send_message(id,text).id),id,state),True)
                        else:
                            db.executeSql('insert into notify(UID,lastMsg,state) values({},"{}","{}")'.format(id,bot.send_message(id,text).id,state), True)

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
                if isinstance(uid,list):
                    for id in uid:
                        lastMsg=db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id,state))[0][0]
                        if lastMsg.find('@')!=-1:
                            for msg in lastMsg.split('@'):
                                bot.delete_message(id,msg)
                        else:
                            bot.delete_message(id,lastMsg)
                '''else:
                    lastMsg = db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(uid, state))[0][0]
                    if lastMsg.find('@') != -1:
                        for msg in lastMsg.split('@'):
                            bot.delete_message(uid, msg)
                    else:
                        bot.delete_message(uid, lastMsg)'''
            except:
                pass

def filterAdds(message,all=False,type=None,keyboardTitle=None):

    if all ==False and type==None:
        adds=db.executeSql('select * from adds where UID={} order by date asc'.format(message.chat.id))
    if all==False and type!=None:
        adds = db.executeSql('select * from adds where UID={} and type="{}" order by date asc'.format(message.chat.id,type))
    if all == True and type != None:
        adds = db.executeSql(
            'select * from adds where type="{}" order by date asc'.format(type))
    if all == True and type== None:
        adds = db.executeSql(
            'select * from adds order by date asc')
    if len(adds)>0:
        
        return adds
        '''for ad in adds:
            eraseKeyboard = types.InlineKeyboardMarkup()
            keyErase = types.InlineKeyboardButton(text='Удалить', callback_data='erase{}'.format(ad[1]))
            kerEdit = types.InlineKeyboardButton(text='Редактировать', callback_data='edit{}'.format(ad[1]))

            eraseKeyboard.add(kerEdit, keyErase)
            if ad[7].find('Car') != -1:
                if ad[7].find('createAddsSend') != -1:
                    send_message(
                        'Заявка  №{}\n🚗 Хочу отправить \n{} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                             month(ad[4]), ad[5],
                                                                                             ad[6]),
                        message, eraseKeyboard, 'searchAdds')
                if ad[7].find('createAddsDely') != -1:
                    if ad[8] in (None, 'False'):
                        text = 'Заявка  №{} 🚗 Могу доставить \n{} - {} : {}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                              month(ad[4]),
                                                                                              ad[6])
                    else:
                        text = 'Заявка  №{} 🚗 Могу доставить (возьму попутчика🙋🏻‍♂️)\n{} - {} : {}\nтел. {}'.format(
                            ad[1], ad[2], ad[3],
                            month(ad[4]),
                            ad[6])
                    send_message(
                        text,
                        message, eraseKeyboard, 'searchAdds')
            if ad[7].find('Air') != -1:
                if ad[7].find('createAddsSend') != -1:
                    send_message(
                        'Заявка  №{}\n✈ Хочу отправить \n{} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                            month(ad[4]), ad[5], ad[6]),
                        message, eraseKeyboard, 'searchAdds')
                if ad[7].find('createAddsDely') != -1:
                    send_message(
                        'Заявка  №{}\n✈ Могу доставить \n{} - {} : {}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                             month(ad[4]),
                                                                                             ad[6]),
                        message, eraseKeyboard, 'searchAdds')
            if ad[7].find('swapTick') != -1:
                send_message(
                    'Обмен билетов №{} {} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3], month(ad[4]), ad[5],
                                                                          ad[6]),
                    message, eraseKeyboard, 'searchAdds')'''
    else:
        send_message('Заявок нет',message,state='sendAdds')
        return None


def calendar(id, msg,mode=None,data=None,year_data=None, msgid=None):
    mdays = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ymonth = [0, 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентьбрь', 'Октябрь',
              'Ноябрь', 'Декабрь']
    mindate=date.today()
    if mode ==None:
        keyar = []

        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[mindate.month] + 1):

            keyar.append(types.InlineKeyboardButton(text=f'{i}'if i>=mindate.day else ' ', callback_data=f'{id}calendar${msgid}?{mindate.month}@{i}@{mindate.year}' if mindate.day >=c else ' ' ))
            if i % 7==0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)


        key.add(*(types.InlineKeyboardButton(text='<',callback_data=f'c_back@{mindate.month}@{id}'),
                 types.InlineKeyboardButton(text='>',callback_data=f'c_next@{mindate.month}@{id}@{mindate.year}')))
        send_message(f'{ymonth[mindate.month]}:', msg, key, 'calendar')
    if mode=='next':
        month=ymonth[data+1]
        # month=ymonth[1]
        keyar = []
        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[data+1] + 1):
        # for i in range(1, mdays[1] + 1):
        
            
            keyar.append(types.InlineKeyboardButton(text=f'{i}',
                                                    callback_data=f'{id}calendar${msgid}?{data+1}@{i}@{year_data}'))
            if i % 7 == 0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)

        key.add(*(types.InlineKeyboardButton(text='<', callback_data=f'c_back@{data+1}@{id}'),
                  types.InlineKeyboardButton(text='>', callback_data=f'c_next@{data+1}@{id}@{year_data}')))
        # send_message(f'month={month}', msg)
        
        return month,key
    if mode=='back':
        month=ymonth[data-1]
        keyar = []

        c = 0
        key = types.InlineKeyboardMarkup(row_width=7)
        for i in range(1, mdays[data-1] + 1):

            keyar.append(types.InlineKeyboardButton(text=f'{i}',
                                                    callback_data=f'{id}calendar${msgid}?{data-1}@{i}'))
            if i % 7 == 0:
                key.add(*keyar, row_width=7)
                keyar.clear()
        key.add(*keyar, row_width=7)

        key.add(*(types.InlineKeyboardButton(text='<', callback_data=f'c_back@{data-1}@{id}'),
                  types.InlineKeyboardButton(text='>', callback_data=f'c_next@{data-1}@{id}')))
        return month,key


def checkAdm(id):
    if db.executeSql('select type from users where UID={}'.format(id))[0][0] == 'admin':
        return True
    else:
        return False


def send_message(text, msg, keyboard=None, state=None, foto=None,reply=False,video=None, help_text=None):
    allmsg=[]
    block=True if len(db.executeSql('select * from blist where UID={}'.format(msg.chat.id))) >0  else False
    if not block:
        if reply!=False:
            print(reply)

            lastMsg = bot.send_message(chat_id=msg.chat.id, text=text,reply_to_message_id=reply,allow_sending_without_reply=False)

        else:
            if video is not None:
                bot.send_video(msg.chat.id,open(f'/root/bot/img/{video}.mp4','rb'))
            if foto is not None:
                fotoMsg=bot.send_photo(msg.chat.id,open('/root/bot/img/'+foto+'.png','rb'))
                allmsg.append(fotoMsg)
            if keyboard != None:
                
                lastMsg = bot.send_message(chat_id=msg.chat.id, text=text, reply_markup=keyboard)
            else:
                print('b')
                lastMsg = bot.send_message(chat_id=msg.chat.id, text=text)

        allmsg.append(lastMsg)
        for message in allmsg:
            lastState = db.executeSql('select * from msg where UID={} and state="{}"'.format(msg.chat.id, state))

            if len(lastState) > 0:
                msgs = db.executeSql('select lastMsg from msg where UID={} and state="{}"'.format(msg.chat.id, state))[0][0]
                db.executeSql('update msg set lastMsg="{}" where UID={} and state="{}"'.format('{}@{}'.format(msgs, message.id),
                                                                                               msg.chat.id, state), True)
            else:
                db.executeSql('insert into msg(UID,state,lastMsg) values ({},"{}","{}")'.format(msg.chat.id, state, message.id))
        #send_message(lastMsg, msg)
        return lastMsg
    else:
        bot.send_message(chat_id=msg.chat.id, text='Упс, у вас блокировка')


def back(message, state):
    bot.clear_step_handler_by_chat_id(message.chat.id)

    ids = db.executeSql('select lastMsg from msg where UID={} and state="{}"'.format(message.chat.id, state))
    db.executeSql('delete from msg where UID={} and state="{}"'.format(message.chat.id, state))
    for id in ids:
        if len(id[0].split('@')) > 0:
            for i in id[0].split('@'):
                try:

                    bot.delete_message(message.chat.id, i)
                except Exception as e:
                    print(e)
                    pass
        else:
            try:
                bot.delete_message(message.chat.id, id[0])
            except:
                print('111')
                pass


def clear(uid):
    msgs = db.executeSql('select lastMsg from msg where UID={}'.format(uid))
    if len(msgs) > 0:
        for msg in msgs:

            if len(msg[0].split('@')) > 0:

                for id in msg[0].split('@'):

                    try:
                        bot.delete_message(uid, id)
                    except Exception as e:
                        continue

            else:
                try:
                    bot.delete_message(uid, msg[0])
                except:
                    pass

    db.executeSql(f'delete from msg where UID={uid}', True)


try:

    @bot.message_handler(content_types=['contact'])
    def hadle_contact(message):
        bot.send_message(message.from_user.id, f'Я получил твой контакт: {message.contact.phone_number}')


    @bot.message_handler(commands=['reply'])
    def reply(message):
        pass


    @bot.message_handler(commands=['adm'])
    def adm(m):
        pass


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
        db.executeSql(f'delete from adds where status="notrelease" and UID={message.chat.id}')
        try:
            bot.delete_message(message.chat.id, message.id)
        except:
            pass

        db.executeSql('delete from history where UID={}'.format(message.chat.id), True)

        clear(message.chat.id)

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
            # send_message('Привет, выберите задачу, которую я Вам помогу решить', message,
            #              keyboards.mainK(message.chat.id, checkAdm(message.chat.id)), 'welcome', video='video1')
            # send_message('Привет', message, )
            # bot.send_video(message.chat.id, video_1)
            
            # send_message(f'{help_text}', message,
            #              keyboards.mainK(message.chat.id, checkAdm(message.chat.id)), 'welcome', foto='welcome')


    @bot.message_handler(commands=['up'])
    def keyUp(message):
        bot.edit_message_reply_markup(message.chat.id)


    @bot.message_handler(content_types=['text'])
    def start(message):
        type = 'Air'
        count = db.executeSql('select countAdds from users where UID={}'.format(message.chat.id))[0][0]
        log(message.chat.id, 'переход в', message.text, 'btn')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)
        elif message.text == 'Назад':
            welcome(message)
        elif message.text == 'con':

            calendar(5, message)


        # bot.send_message(message.chat.id,message.from_user)
        elif message.text == '🚘 Кто едет':
            back(message, 'welcome')

            bot.register_next_step_handler(
                send_message('Выберите действие', message, keyboards.addK('Car'), 'creatAdds', foto='carCreateAdds'),
                creatAdds, 'Car')
        elif message.text == '✈️ Кто летит':
            back(message, 'welcome')

            bot.register_next_step_handler(
                send_message('Выберите действие', message, keyboards.addK('Air'), 'creatAdds', foto='airCreateAdds'),
                creatAdds, 'Air')
        # elif message.text == 'Очистить историю':
        #     # bot.send_message(message.chat.id, message.message_id + 1)
        #     for i in range(10):
        #         bot.delete_message(message.chat.id, message.message_id - i)
            # welcome(message)
        elif message.text == '🎫 Обмен билетов':
            bot.register_next_step_handler(send_message('Обмен билетов', message, keyboards.tickKeyboard, 'swapTick'),
                                           swapTick)
            for ad in db.executeSql('select * from adds where type="{}" order by date asc'.format('swapTick')):
                send_message(
                    'Обмен билетов №{} {} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3], ad[4], ad[5], ad[6]),
                    message, state='swapTick')
        elif message.text.find('Хочу отправить') != -1:
            back(message, 'welcome')
            type = 'createAddsSend' + type
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity1', foto='carCity1'),
                    setAlp,
                    type)
            else:
                bot.register_next_step_handler(
                    send_message('Выберите из списка пункт отправления', message, keyboards.getCity(type),
                    'chooseCity1', foto='carCity1'), chooseCity1, type)
        elif message.text.find('Могу доставить') != -1:
            back(message, 'welcome')
            type = 'createAddsDely' + type
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity1', foto='carCity1'),
                    setAlp,
                    type)
            else:
                bot.register_next_step_handler(
                    send_message('Выберите из списка пункт отправления', message, keyboards.getCity(type),
                    'chooseCity1', foto='carCity1'), chooseCity1, type)
            
        elif message.text.find('Поиск') != -1:
            back(message, 'welcome')
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Искать тех, кто хочет отправить', 'Искать тех, кто хочет доставить')
            #keyboard.add('Поиск по дате и маршруту', 'Поиск по дате и городу отправления')

            keyboard.add('На главную')

            adds = db.executeSql(
                'select * from adds where type like "{}" order by date asc'.format('createAdds%' + type))
            bot.register_next_step_handler(
                send_message(
                    f'Актуальных предложений по всем направлениям:{len(adds) + 111}\nПопулярные направления:\n🇮🇩Индонезия, 🇦🇪ОАЭ, 🇷🇺Россия и СНГ, 🇺🇲США, 🇹🇭Таиланд, 🇹🇷Турция',
                    message, keyboard, 'creatAdds'), show_sub_menu_search,
                type)





        elif message.text == '✅📦 Гарантированная доставка':
            bot.register_next_step_handler(
                send_message('Гарантированная доставка', message, keyboards.garantDely(checkAdm(message.chat.id)),
                             'gdAct'),
                gdAct)

            adds = filterAdds(message, True)
            if adds != None:
                printAdds(message, adds, None, True, False, True)

        elif message.text.find('Мои заявки') != -1:
            back(message, 'welcome')
            notify([message.chat.id], '', 'adds', True)
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')

            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)
            adds = filterAdds(message)
            if adds != None:
                printAdds(message, adds, None, True, False, True)


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

    
    #     elif message.text == 'Запрещается':
    #         help_text = '''Просто запрещается:
    # 1. Переводить предоплату за доставку. Только по факту доставки. Даже, в случае экстренной необходимости - оплата услуг местных курьерских служб, перемещения доставщика по Вашей просьбе, покупки дополнительного багажного места по Вашей просьбе и всех сопутствующих расходов ПРИ РЕАЛЬНОСТИ ПОЕЗДКИ и обоюдного согласия может быть покрыта ВАМИ через соответствующие приложения или же оплачена по факту доставки.   
    # 2. Обнадеживать. Указывать приблизительные даты вылета т.е. до приобретения Вами билетов. Мы стараемся решить вопрос срочности, потому и один день играет очень важную роль. 
    # 3. Без личной проверки брать к перевозке что-либо. Если что-то не так – Вы вправе отказаться. Всегда.
    # 4. Просить о перевозке чего-либо, в качестве или происхождении чего Вы не уверены. То же касается и передач от третьих лиц. '''
    #         keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    #         keyboard.add('На главную')
    #         send_message(f'{help_text}', message, keyboard)
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
            #send_message(f'{help_text}', message, addsKeyboard)
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
            back(message, 'welcome')
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')
            bot.register_next_step_handler(
                send_message('Написать администратору\n@asap_delivery', message, addsKeyboard, state='support'),
                support, 'support')
        elif message.text.find('Стоимость') != -1:
            info_for_price(message)
            
            
            

            '''        if checkAdm(message.chat.id):
                notify([message.chat.id], '', 'support', True)
                if len(db.executeSql('select * from support where status="{}"'.format(message.chat.id)))>0:
                    chatId=db.executeSql('select chatId from support where status="{}"'.format(message.chat.id))[0][0]
                    msgs = db.executeSql('select * from supportMsg where chatId={} order by date'.format(chatId))
                    if len(msgs) > 0:

                        main = send_message(f'Чат №{chatId}:', message, keyboards.supKeyboard, 'support')
                        for msg in msgs:
                            if msg[2] == 'support':
                                send_message('{}\n{}'.format(msg[1], msg[3]), message, state='support', reply=lastmsg)
                            else:
                                lastmsg = send_message('{}\n{}'.format(msg[1], msg[3]), message, state='support').id
                    bot.register_next_step_handler(main, sendMsg, f'answerSupport@{chatId}')




                else:
                    sup = db.executeSql('select * from support where status = "{}"'.format('await'))
                    if len(sup) > 0:
                        for inc in sup:
                            eraseKeyboard = types.InlineKeyboardMarkup()
                            keyErase = types.InlineKeyboardButton(text='Ответить', callback_data=f'support@{inc[0]}')
                            eraseKeyboard.add(keyErase)
                            user=db.executeSql('select * from users where UID={}'.format(inc[1]))[0]

                            username=user[3] if user[3]!=None else user[6]
                            send_message('Чат №{} \n {} '.format(inc[0], username), message,
                                         eraseKeyboard, state='support')

                    else:

                        bot.register_next_step_handler(
                            send_message('Обращений нет.', message, keyboards.supKeyboard, state='support'), support,0)


            else:
                notify([message.chat.id], '', 'support', True)
                if len(db.executeSql('select chatId from support where UID={}'.format(message.chat.id)))<1:
                    db.executeSql('insert into support(UID) values({})'.format(message.chat.id))

                chatId=db.executeSql('select chatId from support where UID = {}'.format(message.chat.id))[0][0]
                msgs=db.executeSql('select * from supportMsg where chatId={} order by date'.format(chatId))
                if len(msgs) > 0:

                    main=send_message(f'Чат №{chatId}:', message, keyboards.supKeyboard, 'support')
                    for msg in msgs:
                        if msg[2]=='support':
                            send_message('{}\n{}'.format(msg[1],msg[3]),message,state='support',reply=lastmsg)

                        else:
                            lastmsg=send_message('{}\n{}'.format(msg[1],msg[3]), message, state='support').id



                else:
                    main = send_message('Сообщений нет. Введите сообщение, специалист тех.поддержки вскоре свяжется с вами.', message, keyboards.supKeyboard, state='support')
                bot.register_next_step_handler(main, sendMsg,'support')'''

        else:
            send_message('Используйте кнопки', message, False)


    def gdAct(message):
        log(message.chat.id, 'gdAct', message.text)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('На главную')
        if message.text == 'Добавить':
            type = 'garantDely'
            bot.delete_message(message.chat.id, message.id)

            bot.register_next_step_handler(send_message('Виберите город', message, keyboard, state='searchCity'),
                                           searchCity, type, 'city1')

        elif message.text == 'На главную':
            welcome(message)
        else:
            send_message('Используйте кнопки', message, state='searchCity')


    def creatAdds(message, type):
        log(message.chat.id, 'переход в', message.text, 'btn')
        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatAdds')
        count = db.executeSql('select countAdds from users where UID={}'.format(message.chat.id))[0][0]
        if message.text == '🙋‍♂️📦 Хочу отправить':
            if checkAdm(message.chat.id):
                type = 'createAddsSend' + type
                if type.find('Car') != -1:
                    bot.register_next_step_handler(
                        send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity1', foto='carCity1'),
                        setAlp,
                        type)
                else:
                    bot.register_next_step_handler(
                        send_message('Укажите город отправки', message, keyboards.getCity(type), 'chooseCity1',
                                     foto='carCity1'), chooseCity1, type)
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
                                                               callback_data=f'win_codeAdd'))
                    else:
                        keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
                key_code.add(*keys, row_width=4)

                addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                addsKeyboard.add('На главную')
                send_message(
                    'Превышен лимит создания заявок. Скоро здесь будет монетизация, нажмите на кнопку с решением {}+{} для разблокировки создания 1 заявки'.format(
                        a, b), message, key_code, state='createAdds')

        elif message.text == 'con':
            raise Exception
        elif message.text == '🙋‍♂️✈️  Могу доставить' or message.text == '🙋‍♂️🚘 Могу доставить':
            if checkAdm(message.chat.id):
                type = 'createAddsDely' + type
                if type.find('Car') != -1:
                    bot.register_next_step_handler(
                        send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity1', foto='carCity1'),
                        setAlp,
                        type)
                else:
                    bot.register_next_step_handler(
                        send_message('Укажите город отправки', message, keyboards.getCity(type), 'chooseCity1',
                                     foto='carCity1'), chooseCity1, type)
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
                                                               callback_data=f'win_codeAdd'))
                    else:
                        keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
                key_code.add(*keys, row_width=4)

                addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                addsKeyboard.add('На главную')
                send_message(
                    'Превышен суточный лимит заявок, нажмите на кнопку с решением {}+{} для разблокировки создания 1 заявки'.format(
                        a, b), message, key_code, state='createAdds')
        elif message.text == '📝 Готовые заявки':
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Поиск по дате и направлению', 'Поиск по дате')
            keyboard.add('Поиск по направлению', 'На главную')

            bot.register_next_step_handler(
                send_message('Заявки', message, keyboard, 'creatAdds'), getAdds,
                type)
            adds = db.executeSql(
                'select * from adds where type like "{}" order by date asc'.format('createAdds%' + type))
            printAdds(message, adds, 'expandcount')


        elif message.text == 'На главную':
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
        
    def show_sub_menu_search(message, type):
    
        log(message.chat.id, 'переход в ' + message.text, '', 'btn')
        back(message, 'search')
        bot.delete_message(message.chat.id, message.id)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Поиск по дате и маршруту', 'Поиск по дате и городу отправления')
        keyboard.add('На главную')
        adds = db.executeSql(
                'select * from adds where type like "{}" order by date asc'.format('createAdds%' + type))
        if message.text == 'На главную':
            welcome(message)
        if message.text == 'Искать тех, кто хочет отправить':
            SEARCH_DATA[f'{message.chat.id}'] = 'createAddsSendAir'
            bot.register_next_step_handler(
                send_message(
                    'Выберите пункт',message, keyboard, 'creatAdds'), getAdds,
                type)
        if message.text == 'Искать тех, кто хочет доставить':
            SEARCH_DATA[f'{message.chat.id}'] = 'createAddsDelyAir'
            bot.register_next_step_handler(
                send_message(
                    'Выберите пункт',message, keyboard, 'creatAdds'), getAdds,
                type)
        '''
        else:
            send_message('Используйте кнопки', message, state='getDely')
        '''
    
    def getAdds(message, type):
        
        log(message.chat.id, 'переход в ' + message.text, '', 'btn')
        back(message, 'search')
        bot.delete_message(message.chat.id, message.id)
        if message.text == 'На главную':
            welcome(message)
        elif message.text == 'Поиск по дате и городу отправления':
            bot.register_next_step_handler(
                send_message('Выберите город', message, keyboards.getCity(type), state='search'),
                chooseCity1, 'searchAdds' + type + 'onlyCity1')
        elif message.text == 'Поиск по дате и маршруту':
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds'), setAlp,
                    'searchAdds' + type)
            else:
                bot.register_next_step_handler(
                    send_message('Выберите город', message, keyboards.getCity(type), state='search'),
                    chooseCity1, 'searchAdds' + type)
        elif message.text == 'Поиск по дате':
            send_message('Выберете дату:', message, state='search')
            calendar(6, message)
        elif message.text == 'Поиск по направлению':
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds'), setAlp,
                    'searchCity' + type)
            else:
                bot.register_next_step_handler(
                    send_message('Выберите город', message, keyboards.getCity(type), state='search'),
                    chooseCity1, 'searchCity' + type)
                    
        else:
            send_message('Используйте кнопки', message, state='getDely')


    def setAlp(message, type, city=1, mask=None):

        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatAdds')
        if message.text == 'На главную':
            welcome(message)
        elif message.text in keyboards.alp:
            back(message, 'chooseCity1')
            if city == 1:
                bot.register_next_step_handler(
                    send_message('Укажите город отправки', message, keyboards.getCity('car', message.text),
                                 'chooseCity1', foto='carCity1'), chooseCity1, type)

            if city == 2:
                bot.register_next_step_handler(
                    send_message('Отлично! Теперь укажите город назначения', message,
                                 keyboards.getCity('car', message.text, mask),
                                 'chooseCity2', foto='carCity2'), chooseCity2, type)
        else:
            send_message('Используйте кнопки', message, state='setTransport')


    def searchCity(message, type, stage):
        log(message.chat.id, 'searchCity', message.text)
        bot.delete_message(message.chat.id, message.id)
        Keyboard = types.InlineKeyboardMarkup()

        if message.text == 'На главную':

            welcome(message)
        else:
            for c in db.executeSql('select * from cities'):

                if c[1].lower().find(message.text.lower()) >= 0:
                    if 'city1' == stage:
                        Keyboard.add(
                            telebot.types.InlineKeyboardButton(c[1], callback_data='city1@{}?{}'.format(c[0], type)))
                    if 'city2' == stage:
                        Keyboard.add(
                            telebot.types.InlineKeyboardButton(c[1], callback_data='city2@{}?{}'.format(c[0], type)))
            if len(Keyboard.keyboard) <= 0:

                bot.register_next_step_handler(
                    send_message('Такого города нет, введите другой', message, state='searchCity'), searchCity, type,
                    stage)
            else:

                bot.register_next_step_handler(send_message('Выберите город', message, Keyboard, 'searchCity'),
                                               searchCity,
                                               type, stage)


    def chooseCity1(message, type):
        bot.delete_message(message.chat.id, message.id)
        back(message, 'chooseCity1')
        if message.text in keyboards.cities:
            if type.find('editCity1') != -1:
                city1 = db.executeSql('select city1 from adds where idAdds={}'.format(type.split('@')[1]))
                log(message.chat.id, 'изменил город отправки {}->{}'.format(city1, message.text), '', 'edit')
                db.executeSql('update adds set city1="{}" where idAdds={}'.format(message.text, type.split('@')[1]),
                              True)
                db.executeSql('delete from possibleAdds where sendAdd={} or delyAdd={}'.format(type.split('@')[1],
                                                                                               type.split('@')[1]))
                typeAdd = db.executeSql('select type from adds where idAdds={}'.format(type.split('@')[1]))[0][0]
                settings.Thread(target=settings.worker(60).search, name='search',
                                args=(type.split('@')[1], typeAdd, checkAdm(message.chat.id))).start()
                back(message, 'adds')
                keyboard = types.ReplyKeyboardMarkup(True, True)
                keyboard.add('Мои заявки', 'На главную')
                add = db.executeSql(
                    'select * from adds where idAdds = {}'.format(type.split('@')[1])
                )
                send_message('Город отправления изменен', message, keyboard, state='edit')
                printAdds(message, add)
                #back(message, 'edit')
                if len(str(type).split('@')) >= 2:
                    msg = str(type).split('@')[2]
                    add = db.executeSql('select * from adds where idAdds={}'.format(str(type).split('@')[1]))[0]
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton('Редактировать',
                                                            callback_data=f'edit@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'),
                                 types.InlineKeyboardButton('Опубликовать',
                                                            callback_data=f'cd@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'))
                    text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                        '✈')
                    text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(add[2],
                                                                                      add[3],
                                                                                      month(add[4]),
                                                                                      add[5], add[6]) if add[7].find(
                        'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],
                                                                                                 add[3],
                                                                                                 month(add[4]),
                                                                                                 add[5], add[6])

                    bot.edit_message_text(text, message.chat.id, msg, reply_markup=keyboard)
                else:
                    addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                    addsKeyboard.add('На главную')

                    bot.register_next_step_handler(
                        send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                        searchAdds)
                    adds = filterAdds(message)
                    if adds != None:
                        printAdds(message, adds, None, True, False, True)
            elif type.find('searchSend') != -1 or type.find('searchDely') != -1 or type.find(
                    'searchSwapTick') != -1 or type.find('searchAdds') != -1 or type.find('searchCity') != -1:
                log(message.chat.id, 'поиск по городу отправки {}'.format(message.text), '', 'search')

                db.executeSql(
                    'insert into history(UID,type,city1,status) values({},"{}","{}","{}")'.format(int(message.chat.id),
                                                                                                  type, message.text,
                                                                                                  'searchChoosedCity1'),
                    True)
                if type.find('onlyCity1') != -1:
                    keyboard = types.ReplyKeyboardMarkup(True, True)
                    keyboard.add('На главную')
                    send_message('Выберете дату:', message, keyboard, state='calendar')

                    calendar(5, message)

                else:
                    if type.find('Air') != -1:
                        bot.register_next_step_handler(
                            send_message('Выберите из списка пункт назначения', message, keyboards.getCity(type),
                                         'chooseCity2', foto='carCity2'), chooseCity2, type)
                    else:

                        bot.register_next_step_handler(
                            send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity2', foto='carCity2'),
                            setAlp,
                            type, 2)



            else:
                log(message.chat.id, 'выбор города отправки ' + message.text, '', 'city1')

                db.executeSql(
                    'insert into history(UID,type,city1,status) values({},"{}","{}","{}")'.format(int(message.chat.id),
                                                                                                  type, message.text,
                                                                                                  'coosedCity1'), True)
                if type.find('Car') != -1:
                    bot.register_next_step_handler(
                        send_message('Поиск города', message, keyboards.getAlp(), 'chooseCity1', foto='carCity2'),
                        setAlp,
                        type, 2, message.text)
                else:
                    bot.register_next_step_handler(
                        send_message('Выберите из списка пункт назначения', message,
                                     keyboards.getCity(type, mask=message.text), 'chooseCity2', foto='carCity2'),
                        chooseCity2,
                        type)
        elif message.text == 'Назад':
            bot.delete_message(message.chat.id, message.id)
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds', foto='carCity2'), setAlp,
                    type)

        elif message.text == 'На главную':

            welcome(message)
        elif message.text.find('/start') != -1:
            welcome(message)


    def chooseCity2(message, type):

        bot.delete_message(message.chat.id, message.id)
        back(message, 'chooseCity2')
        if message.text in keyboards.cities:
            if type.find('editCity2') != -1:
                city2 = db.executeSql('select city2 from adds where idAdds={}'.format(type.split('@')[1]))
                log(message.chat.id, 'изменил город доставки {}->{}'.format(city2, message.text), '', 'edit')
                db.executeSql('update adds set city2="{}" where idAdds={}'.format(message.text, type.split('@')[1]),
                              True)
                db.executeSql('delete from possibleAdds where sendAdd={} or delyAdd={}'.format(type.split('@')[1],
                                                                                               type.split('@')[1]))
                typeAdd = db.executeSql('select type from adds where idAdds={}'.format(type.split('@')[1]))[0][0]
                settings.Thread(target=settings.worker(60).search, name='search',
                                args=(type.split('@')[1], typeAdd, checkAdm(message.chat.id))).start()
                back(message, 'adds')
                keyboard = types.ReplyKeyboardMarkup(True, True)
                keyboard.add('Мои заявки', 'На главную')
                add = db.executeSql(
                    'select * from adds where idAdds = {}'.format(type.split('@')[1])
                )
                send_message('Город назначения изменен', message, keyboard, state='edit')
                printAdds(message, add)
                #time.sleep(1)
                #back(message, 'edit')
                if len(str(type).split('@')) >= 2:
                    msg = str(type).split('@')[2]
                    add = db.executeSql('select * from adds where idAdds={}'.format(str(type).split('@')[1]))[0]
                    keyboard = types.InlineKeyboardMarkup()
                    keyboard.add(types.InlineKeyboardButton('Редактировать',
                                                            callback_data=f'edit@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'),
                                 types.InlineKeyboardButton('Опубликовать',
                                                            callback_data=f'cd@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'))
                    text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                        '✈')
                    text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(add[2],
                                                                                      add[3],
                                                                                      month(add[4]),
                                                                                      add[5], add[6]) if add[7].find(
                        'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],
                                                                                                 add[3],
                                                                                                 month(add[4]),
                                                                                                 add[5], add[6])

                    bot.edit_message_text(text, message.chat.id, msg, reply_markup=keyboard)
                else:
                    addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                    addsKeyboard.add('На главную')

                    bot.register_next_step_handler(
                        send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                        searchAdds)
                    adds = filterAdds(message)
                    if adds != None:
                        printAdds(message, adds, None, True, False, True)
            elif type.find('searchSend') != -1 or type.find('searchDely') != -1 or type.find(
                    'searchSwapTick') != -1 or type.find('searchAdds') != -1:
                log(message.chat.id, 'поиск по городу доставки {}'.format(message.text), '', 'search')
                db.executeSql(
                    'update history set city2="{}" where UID={} and status="{}"'.format(message.text, message.chat.id,
                                                                                        'searchChoosedCity1'), True)
                db.executeSql(
                    'update history set status="{}" where UID={} and status="{}"'.format('searchChoosedCity2',
                                                                                         message.chat.id,
                                                                                         'searchChoosedCity1'), True)

                keyboard = types.ReplyKeyboardMarkup(True, True)

                keyboard.add('На главную')
                send_message('Выберете дату:', message, keyboard, state='calendar')

                calendar(5, message)




            elif type.find('searchCity') != -1:
                log(message.chat.id, 'поиск по городу доставки {}'.format(message.text), '', 'search')
                keyboard = types.ReplyKeyboardMarkup(True, True)
                keyboard.add('Поиск по дате и маршруту', 'Поиск по дате и городу отправления')

                keyboard.add('На главную')

                adds = db.executeSql('select * from adds where city1="{}" and city2="{}"'.format(db.executeSql(
                    'select city1 from history where UID={} and status="{}"'.format(message.chat.id,
                                                                                    'searchChoosedCity1'))[0][0],
                                                                                                 message.text))

                back(message, 'search')
                db.executeSql('delete from history where UID ={}'.format(message.chat.id), True)
                bot.register_next_step_handler(send_message('Найденные заявки', message, keyboard, state='search'),
                                               getAdds,
                                               type)

                if len(adds) > 0:
                    printAdds(message, adds, 'collapse', False, True, False, None)






            else:
                log(message.chat.id, 'выбор города доставки ' + message.text, '', 'city2')
                db.executeSql(
                    'update  history set city2="{}"  where UID={} and type="{}"'.format(message.text,
                                                                                        int(message.chat.id),
                                                                                        type), True)
                db.executeSql(
                    'update  history set status="{}"  where UID={} and type="{}"'.format('choosedCity2',
                                                                                         int(message.chat.id), type),
                    True)
                if type.find('createAddsSend') != -1:
                    send_message(f"Выберите дату", message, state='calendar')
                    calendar(1, message)

                if type.find('createAddsDely') != -1:
                    send_message(f"Выберите дату", message, state='calendar')
                    calendar(2, message)
                if type.find('swapTick') != -1:
                    send_message(f"Выберите дату", message, state='calendar')
                    calendar(3, message)
        elif message.text == 'Назад':
            bot.delete_message(message.chat.id, message.id)
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds'), setAlp,
                    type, 2)
        elif message.text == 'На главную':

            welcome(message)
        elif message.text.find('/start') != -1:
            welcome(message)


    def creatDealContact(message, id):
        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatDealContact')
        if message.text.find('Мои заявки') != -1:
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')
            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)
            adds = filterAdds(message)
            if adds != None:
                printAdds(message, adds, None, True, False, True)

        elif message.text.find('На главную') != -1:
            welcome(message)
            db.executeSql('delete from adds where idAdds = {}'.format(id), True)
        elif message.text.find('/start') != -1:
            welcome(message)
            db.executeSql('delete from adds where idAdds = {}'.format(id), True)
        elif str(id).find('editContact') != -1:
            contact = db.executeSql('select contact from adds where idAdds={}'.format(str(id).split('@')[1]))
            log(message.chat.id, 'изменил контакт {}->{}'.format(contact, message.text), '', 'edit')
            db.executeSql('update adds set contact="{}" where idAdds={}'.format(message.text, str(id).split('@')[1]),
                          True)
            back(message, 'adds')
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Мои заявки', 'На главную')
            add = db.executeSql(
                'select * from adds where idAdds = {}'.format(
                    str(id).split('@')[1]
                )
            )
            send_message('Контактные данные изменены', message, keyboard, state='edit')
            printAdds(message, add)
            #time.sleep(1)
            #back(message, 'edit')
            if len(str(id).split('@')) >= 2:
                msg = str(id).split('@')[2]
                add = db.executeSql('select * from adds where idAdds={}'.format(str(id).split('@')[1]))[0]
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton('Редактировать',
                                                        callback_data=f'edit@{str(id).split("@")[1] + "@" + str(id).split("@")[2]}'),
                             types.InlineKeyboardButton('Опубликовать',
                                                        callback_data=f'cd@{str(id).split("@")[1] + "@" + str(id).split("@")[2]}'))
                text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                    '✈')
                if add[7].find('Send') != -1:
                    text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
                    add[2],add[3],month(add[4]),add[5], add[6])
                else:
                    text += 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],add[3],month(add[4]),add[5], add[6])

                bot.edit_message_text(text, message.chat.id, msg, reply_markup=keyboard)
            else:
                addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                addsKeyboard.add('На главную')

                bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                               searchAdds)
                adds = filterAdds(message)
                if adds != None:
                    printAdds(message, adds, None, True, False, True)
        elif id == 'readyContact':
            log(message.chat.id, 'ввел контакт ', message.text, 'contact')

            db.executeSql(
                'update  history set contact="{}" where UID={} and status="{}"'.format(message.text, message.chat.id,
                                                                                       'readyContact'))

            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyDeal', message.chat.id,'readyContact'), True
            )
            add = db.executeSql(f'select * from history where UID={message.chat.id} and status="readyDeal"')[0]
                
            db.executeSql(
                'insert into adds(UID,city1,city2,date,title,contact,type,status) values({},"{}","{}","{}","{}","{}","{}","notrelease")'.format(
                    add[1], add[3], add[4], add[5], add[6], add[7], add[2]))
            id = db.executeSql(f'select * from adds where UID={message.chat.id} and status="notrelease"')[0][1]
            db.executeSql(f'delete from history where id = {add[0]}')
            

            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{id}@release'),
            types.InlineKeyboardButton('Опубликовать', callback_data=f'cd@{id}'))
                
            text = 'Заявка {}'.format('🚗') if add[2].find('Car') != -1 else 'Заявка{}'.format(
                    '✈'
                )
                
            if add[2].find('Send') != -1:
                text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
                    add[3],add[4],month(add[5]),add[6], add[7]
                ) 
            if add[2].find('Dely') != -1:
                text += 'Могу доставить \n{} - {} : {}\n{}\nтел. {}'.format(
                    add[3], add[4], month(add[5]), add[6], add[7]
                )                                                         
            bot.register_next_step_handler(send_message(text, message, keyboard,
                                            'releaseAdd'), creatDealRefer,
                                            'readyRefer')



            if checkAdm(message.chat.id):

                keyboard = types.ReplyKeyboardMarkup(True, True)
                db.executeSql(
                    'update history set status="{}" where UID={} and status="{}"'.format('readyRefer', message.chat.id,'readyContact'), True)
                keyboard.add('Пропустить', 'На главную')
                bot.register_next_step_handler(
                    send_message(
                        'Укажите ресурс заявки', message, keyboard,'creatDealRefer', foto='carAddsInfo'
                    ), creatDealRefer,
                'readyRefer')

            '''if not settings.checkProc('search', True):
                settings.procList.append(
                    settings.Thread(target=settings.worker(90).search, name='search', args=(id, ad[0])).start())'''



    def creatDealTitle(message, type):

        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatDealTitle')
        if message.text == 'На главную':

            welcome(message)

        elif message.text.find('/start') != -1:
            welcome(message)
        elif type.find('editTitle') != -1:
            title = db.executeSql('select title from adds where idAdds={}'.format(type.split('@')[1]))
            log(message.chat.id, 'изменил описание {}'.format(title), message.text, 'edit')
            db.executeSql('update adds set title="{}" where idAdds={}'.format(message.text, type.split('@')[1]), True)
            back(message, 'adds')

            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Мои заявки', 'На главную')
            add = db.executeSql(
                'select * from adds where idAdds = {}'.format(type.split('@')[1])
            )
            send_message('Описание изменено', message, keyboard, state='edit')
            printAdds(message, add)
            #time.sleep(1)
            #back(message, 'edit')
            if len(str(type).split('@')) >= 2:
                msg = str(type).split('@')[2]
                add = db.executeSql('select * from adds where idAdds={}'.format(str(type).split('@')[1]))[0]
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton('Редактировать',
                                                        callback_data=f'edit@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'),
                             types.InlineKeyboardButton('Опубликовать',
                                                        callback_data=f'cd@{str(type).split("@")[1] + "@" + str(type).split("@")[2]}'))
                text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                    '✈'
                )
                print('a = ',add[7])
                bot.send_message(message.chat.id, f'a={add[7]}')
                if add[7].find('Send') != -1:
                    text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
                    add[2],add[3],month(add[4]),add[5], add[6]) 
                else:
                    text += 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],add[3],month(add[4]),add[5], add[6])

                bot.edit_message_text(text, message.chat.id, msg, reply_markup=keyboard)
            else:
                addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                addsKeyboard.add('На главную')

                bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                               searchAdds)
                adds = filterAdds(message)
                if adds != None:
                    printAdds(message, adds, None, True, False, True)


        else:
            log(message.chat.id, 'ввел описание', message.text, 'title')

            db.executeSql(
                'update  history set title="{}" where UID={} and status="{}"'.format(message.text, message.chat.id,
                                                                                     'readyTitle'))
            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyContact', message.chat.id,
                                                                                     'readyTitle'), True)

            '''keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
            button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
            keyboard.add(button_phone)'''
            bot.register_next_step_handler(
                send_message('Укажите контакты для связи', message, state='creatDealContact', foto='carAddsInfo'),
                creatDealContact, 'readyContact')


    

    def donate(msgs, card):

        print(msgs.id)
        msg = db.executeSql('select * from msg where UID={} and state="{}"'.format(msgs.chat.id, 'donate'))

        if len(msg) == 0:
            hideK = telebot.types.InlineKeyboardMarkup()
            hideK.add(telebot.types.InlineKeyboardButton('Скрыть', callback_data='hide'))
            send_message('Если наш Бот помог Вам можете поддержать нас любой суммой от 1₽', msgs, state='donate')
            send_message(card, msgs, hideK, 'donate')


    def creatDealRefer(message, id):
        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatDealRefer')

        if message.text.find('На главную') != -1:
            welcome(message)
        elif message.text.find('/start') != -1:
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

        if str(id).find('editRefer') != -1:
            id = int(str(id).split('@')[1])

            db.executeSql('update adds set refer="{}" where idAdds={}'.format(message.text, id), True)
            back(message, 'adds')
            send_message('Ресурс изменен', message, state='edit')
            time.sleep(1)
            back(message, 'edit')

            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')

            bot.register_next_step_handler(send_message('Заявки:', message, addsKeyboard, 'adds', foto='MyAdds'),
                                           searchAdds)
            adds = filterAdds(message)
            if adds != None:
                printAdds(message, adds, None, True, False, True)

        elif str(id) != 'back':
            ad = db.executeSql('select type,city1,city2,date,title,contact from adds where idAdds={}'.format(id))[0]
            userid = db.executeSql('select UID from users where username like "{}"'.format(ad[5].replace('@', '')))
            if len(userid) > 0:
                db.executeSql('update adds set UID = {} where idAdds={}'.format(userid, id))
            if message.text.find('Пропустить') != -1:
                db.executeSql('update adds set refer="{}" where idAdds={}'.format('None', id), True)
            else:
                db.executeSql('update adds set refer="{}" where idAdds={}'.format(message.text, id), True)

            if ad[0].find('createAddsDelyCar') != -1:
                keyboard = types.ReplyKeyboardMarkup(True, True)
                keyboard.add('Да', 'Нет')
                keyboard.add('На главную')

                bot.register_next_step_handler(send_message('Возьмете попутчиков?', message, keyboard,
                                                            'creatDealContact', foto='carAddsInfo'), creatDealPassenger,
                                               id)
            else:
                keyboard = types.ReplyKeyboardMarkup(True, True)
                keyboard.add('Мои заявки', 'На главную')

                if ad[0].find('createAddsSend') != -1:
                    bot.register_next_step_handler(
                        send_message(
                            f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                            message, keyboard,
                            state='creatDealContact', foto='carCreateDeal'), creatDealRefer, 'back')

                if ad[0].find('createAddsDely') != -1:
                    bot.register_next_step_handler(
                        send_message(
                            f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                            message, keyboard, state='creatDealContact', foto='carCreateDeal'), creatDealRefer, 'back')

                db.executeSql('delete from history where UID={} and status="{}"'.format(message.chat.id, 'readyDeal'),
                              True)
                if ad[0].find('swapTick') != -1:
                    bot.register_next_step_handler(
                        send_message(f'Заявка №{id} на обмен билетов добавлена', message, keyboard,
                                     state='creatDealContact'), creatDealRefer, 'back')

                settings.Thread(target=settings.worker(60).search, name='search',
                                args=(id, ad[0], checkAdm(message.chat.id))).start()


    def creatDealPassenger(message, id):
        log(message.chat.id, 'creatDealPassenger', message.text)
        bot.delete_message(message.chat.id, message.id)
        back(message, 'creatDealPassenger')

        if message.text == 'Да':
            db.executeSql('update adds set passenger ="True" where idAdds={} '.format(int(id)), True)
            send_message(f'Заявка №{id} создана', message, state='creatDealPassenger')
            welcome(message)
        elif message.text == 'Нет':
            db.executeSql('update adds set passenger ="False" where idAdds={} '.format(int(id)), True)
            send_message(f'Заявка №{id} создана', message, state='creatDealPassenger')
            welcome(message)

        elif message.text == 'На главную':
            welcome(message)


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


    def swapTick(message):
        log(message.chat.id, 'swapTick', message.text)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('На главную')

        bot.delete_message(message.chat.id, message.id)
        if message.text == 'Обменять свой билет':
            type = 'swapTick'

            bot.register_next_step_handler(send_message('Введите город', message, keyboard, state='swapTick'),
                                           searchCity,
                                           type, 'city1')
        elif message.text == 'Поиск':

            bot.register_next_step_handler(send_message('Введите город', message, keyboard, state='swapTick'),
                                           searchCity,
                                           'searchSwapTick', 'city1')

        elif message.text == 'На главную':

            welcome(message)
        else:
            send_message('Используйте кнопки', message, state='swapTick')


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
        '''else :
            if checkAdm(message.chat.id):
                date = list(time.localtime())

                date = '{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4], date[5])
                chatId = id
                db.executeSql('insert into supportMsg(chatId,text,type,date) values({},"{}","{}","{}")'.format(chatId,
                                                                                                               message.text,
                                                                                                               'support',
                                                                                                               date), True)
                db.executeSql('update support set status="{}" where chatId={}'.format('answer', chatId), True)
            else:
                date = list(time.localtime())

                date = '{}-{}-{} {}:{}:{}'.format(date[0], date[1], date[2], date[3], date[4], date[5])
                chatId = db.executeSql('select chatId from support where UID = {}'.format(message.chat.id))[0][0]
                db.executeSql('insert into supportMsg(chatId,text,type,date) values({},"{}","{}","{}")'.format(chatId,message.text,'user',date),True)
                db.executeSql('update support set status="{}" where chatId={}'.format('await',chatId),True)'''

    
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
        bot.send_message(message.chat.id,f'`{number}`', parse_mode='Markdown')
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
        send_message('- Переводом любой суммы благотворительному фонду',message, keyboard)
        
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


    def actEdit(message):
        log(message.chat.id, 'actEdit', message.text)
        bot.delete_message(message.chat.id, message.id)
        for ad in db.executeSql('select * from adds where idAdds="{}" order by date asc'.format(message.text)):

            eraseKeyboard = types.InlineKeyboardMarkup()
            keyErase = types.InlineKeyboardButton(text='Удалить', callback_data='erase{}'.format(ad[1]))
            kerEdit = types.InlineKeyboardButton(text='Редактировать', callback_data='edit{}'.format(ad[1]))
            eraseKeyboard.add(keyErase, kerEdit)
            if ad[7].find("swapTick") != -1:
                send_message(
                    'Обмен билетов №{} {} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3], ad[4], ad[5], ad[6]),
                    message, eraseKeyboard, state='actEdit')

            if ad[7].find("createAddsSend") != -1:
                send_message(
                    'Отправка №{} {} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3], ad[4], ad[5], ad[6]),
                    message, eraseKeyboard, state='actEdit')

            if ad[7].find("createAddsDely") != -1:
                send_message(
                    'Доставка №{} {} - {} : {}\n{} \nтел. {}'.format(ad[1], ad[2], ad[3], ad[4], ad[5], ad[6]),
                    message, eraseKeyboard, state='actEdit')


    def editAdds(message, id):
        log(message.chat.id, 'перешел в', message.text, 'btn')
        nid = id.split('@')[0]
        bot.delete_message(message.chat.id, message.id)
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Мои заявк','На главную')
        type = db.executeSql('select type from adds where idAdds={}'.format(int(nid)))[0][0]
        if message.text == 'Город оправки':
            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds'), setAlp,
                    f'editCity1@{id}')
            else:
                bot.register_next_step_handler(
                    send_message('Укажите город отправки', message, keyboards.getCity(type), 'edit'), chooseCity1,
                    f'editCity1@{id}')
        if message.text == 'asa Город отправления изменен':
            bot.register_next_stop_handler(
                send_message(
                    None, message, keyboard, 'edit'
                ), show_menu_bid_and_home
            )
        elif message.text == 'Ресурс':
            bot.register_next_step_handler(
                send_message('Укажите ресурс', message, keyboard, 'edit'), creatDealRefer, f'editRefer@{id}')

        elif message.text == 'Город прибытия':

            if type.find('Car') != -1:
                bot.register_next_step_handler(
                    send_message('Поиск города', message, keyboards.getAlp(), 'creatAdds'), setAlp,
                    f'editCity2@{id}', 2)
            else:
                bot.register_next_step_handler(
                    send_message('Укажите город прибытия', message, keyboards.getCity(type), 'edit'), chooseCity2,
                    f'editCity2@{id}')
        elif message.text == 'Дату':

            send_message(
                f"Выберите дату",
                message, keyboard, state='edit')
            calendar(4, message, msgid=id.split('@')[1] if '@' in id else None)

            lastType = \
            db.executeSql('select type from adds where idAdds={}'.format(id.split('@')[0] if '@' in id else id))[0][0]
            db.executeSql('update adds set type="{}" where idAdds={}'.format(f'editDate@{lastType}',
                                                                             id.split('@')[0] if '@' in id else id),
                          True)
        elif message.text == 'Контактные данные':

            bot.register_next_step_handler(send_message(
                'Введите котактные данные',
                message, keyboard, state='edit')
                , creatDealContact, f'editContact@{id}')
        elif message.text == 'Описание':

            bot.register_next_step_handler(send_message(
                'Описание',
                message, keyboard, state='edit')
                , creatDealTitle, f'editTitle@{id}')
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





    @bot.callback_query_handler(func=lambda call: call.data.find('cd') == 0)
    def cd(c):

        id = c.data.split('@')[1]
        
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
                                                               callback_data=f'save@{id}'))
            else:
                keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
        key_code.add(*keys, row_width=4)

        addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        addsKeyboard.add('На главную')
        send_message(
                    'Превышен лимит создания заявок. Скоро здесь будет монетизация, нажмите на кнопку с решением {}+{} для разблокировки создания 1 заявки'.format(
                    a, b), c.message, key_code, state='createAdds')
        '''
        bot.delete_message(c.message.chat.id, c.message.id)
        db.executeSql(f'update adds set status="release" where idAdds={id}')
        ad = db.executeSql('select * from adds where idAdds={}'.format(id))[0]

        log(c.message.chat.id, 'создал заявку {} {} {}'.format(ad[2], ad[3], ad[4]),
            '{} {}'.format(ad[5], ad[6]), 'add')

        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Мои заявки', 'На главную')

        if ad[7].find('createAddsSend') != -1:
            bot.register_next_step_handler(send_message(
                f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                c.message, keyboard, state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        if ad[7].find('createAddsDely') != -1:
            bot.register_next_step_handler(send_message(
                f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                c.message, keyboard, state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        db.executeSql(
            'delete from history where UID={} and status="{}"'.format(c.message.chat.id, 'readyDeal'), True)
        if ad[7].find('swapTick') != -1:
            bot.register_next_step_handler(
                send_message(f'Заявка №{id} на обмен билетов добавлена', c.message, keyboard,
                             state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        settings.Thread(target=settings.worker(60).search, name='search', args=(id, ad[7])).start()

        '''
    @bot.callback_query_handler(func=lambda call: call.data.find('1calendar') == 0)
    def cal(c):
        back(c.message, 'choosedCity2')
        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        

        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        # today = date.today().isoformat()
        
        if result:
            log(c.message.chat.id, 'указал дату', result, 'date')

            db.executeSql('update history set date="{}" where UID={} and status="{}"'.format(result, c.message.chat.id,
                                                                                                'choosedCity2'), True)
            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyTitle', c.message.chat.id,
                                                                                        'choosedCity2'), True)
            back(c.message, 'calendar')
            
            keyboard = types.ReplyKeyboardMarkup(True, True)

            keyboard.add('На главную')
            bot.register_next_step_handler(
                send_message(f"Опишите предмет, который нужно отправить", c.message, keyboard, state='creatDealTitle',
                                foto='carAddsInfo'),
                creatDealTitle, '')


    @bot.callback_query_handler(func=lambda call: call.data.find('2calendar') == 0)
    def cal(c):
        back(c.message, 'choosedCity2')

        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        if result:
            '''log(c.message.chat.id, 'указал дату', result, 'date')
            db.executeSql('update history set date="{}" where UID={} and status="{}"'.format(result, c.message.chat.id,
                                                                                             'choosedCity2'), True)
            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyDeal', c.message.chat.id,
                                                                                     'choosedCity2'), True)
            add = db.executeSql(
                'select city1,city2,date,type from history where UID={} and status="{}"'.format(c.message.chat.id,
                                                                                                'readyDeal'))[0]
            db.executeSql('insert into adds(UID,city1,city2,date,type) values({},"{}","{}","{}","{}")'.format(
                c.message.chat.id, add[0], add[1], add[2], add[3]), True)

            id = db.executeSql('select idAdds from adds where UID={} and date="{}" and title is NULL and contact is NULL'.format(c.message.chat.id, add[2]))[0][0]
            back(c.message, 'calendar')
            keyboard = types.ReplyKeyboardMarkup(True, True)

            keyboard.add('На главную')
            bot.register_next_step_handler(
                send_message(f"Укажите номер телефона для связи", c.message, keyboard,state='creatDealContact',foto='carAddsInfo'), creatDealContact,
                id)'''
            log(c.message.chat.id, 'указал дату', result, 'date')

            db.executeSql('update history set date="{}" where UID={} and status="{}"'.format(result, c.message.chat.id,
                                                                                             'choosedCity2'), True)
            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyTitle', c.message.chat.id,
                                                                                     'choosedCity2'), True)
            back(c.message, 'calendar')
            keyboard = types.ReplyKeyboardMarkup(True, True)

            keyboard.add('На главную')
            bot.register_next_step_handler(
                send_message(f"Укажите детали поездки и требования к перевозимому грузу", c.message, keyboard,
                             state='creatDealTitle',
                             foto='carAddsInfo'),
                creatDealTitle, '')


    @bot.callback_query_handler(func=lambda call: call.data.find('3calendar') == 0)
    def cal(c):
        back(c.message, 'choosedCity2')
        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        if result:
            log(c.message.chat.id, 'указал дату', result, 'date')
            db.executeSql('update history set date="{}" where UID={} and status="{}"'.format(result, c.message.chat.id,
                                                                                             'choosedCity2'), True)
            db.executeSql(
                'update history set status="{}" where UID={} and status="{}"'.format('readyDeal', c.message.chat.id,
                                                                                     'choosedCity2'), True)

            add = db.executeSql(
                'select city1,city2,date,type from history where UID={} and status="{}"'.format(c.message.chat.id,
                                                                                                'readyDeal'))[0]
            db.executeSql('insert into adds(UID,city1,city2,date,type) values({},"{}","{}","{}","{}")'.format(
                c.message.chat.id, add[0], add[1], add[2], add[3]), True)

            id = db.executeSql(
                'select idAdds from adds where UID={} and date="{}" and city1="{}" and city2="{}" and title is NULL and contact is NULL'.format(
                    c.message.chat.id,
                    add[2], add[0],
                    add[1]))[0][0]
            back(c.message, 'calendar')
            keyboard = types.ReplyKeyboardMarkup(True, True)

            keyboard.add('На главную')
            bot.register_next_step_handler(
                send_message(f"Укажите номер телефона для связи", c.message, keyboard, state='creatDealContact',
                             foto='carAddsInfo'), creatDealContact,
                id)

    def get_text_for_add(message, add):
        # bot.send_message()
        text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                    '✈')
        # bot.send_message(message.chat.id, 'testt')
        text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
            add[2],add[3],month(add[4]),add[5], add[6]) if add[7].find(
                'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],add[3],month(add[4]),add[5], add[6])
        return text

    @bot.callback_query_handler(func=lambda call: call.data.find('4calendar') == 0)
    def cal(c):

        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        if result:
            lastdate = db.executeSql(
                'select date from adds where UID={} and type like "{}%"'.format(c.message.chat.id, 'editDate'))[0][0]
            log(c.message.chat.id, 'изменил дату с {}->{}'.format(lastdate, result), '', 'edit')
            bot.delete_message(c.message.chat.id, c.message.message_id)
            idAdd = db.executeSql(
                'select idAdds from adds where UID = {} and  type like "{}%"'.format(c.message.chat.id, 'editDate'))[0][
                0]
            db.executeSql(
                'update adds set date="{}" where UID={} and type like "{}%"'.format(result, c.message.chat.id,
                                                                                    'editDate'),
                True)
            lastType = db.executeSql(
                'select type from adds where UID={} and type like "{}%"'.format(c.message.chat.id, 'editDate'))[
                0][0].split('@')[1]

            db.executeSql(
                'update adds set type="{}" where UID={} and type like "{}%"'.format(lastType, c.message.chat.id,
                                                                                    'editDate'), True)
            db.executeSql('delete from possibleAdds where sendAdd={} or delyAdd={}'.format(idAdd,idAdd))
            type = db.executeSql('select type from adds where idAdds={}'.format(idAdd))[0][0]
            settings.Thread(target=settings.worker(60).search, name='search',
                            args=(idAdd, type, checkAdm(c.message.chat.id))).start()
            back(c.message, 'adds')
            
            keyboard = types.ReplyKeyboardMarkup(True, True)
            keyboard.add('Мои заявки', 'На главную')
            add = db.executeSql(
                'select * from adds where idAdds={}'.format(idAdd)
            )
            # bot.send_message(c.message.chat.id, f'idAdd={str(add[7])}')
            send_message('Дата изменена', c.message, keyboard, state='edit')
            printAdds(c.message, add)
            # text_add = get_text_for_add(c.message, add=add)
            # if add[7].find('Car') != -1:
            #     text_add = 'Заявка {}'.format('🚗') 
            # else:
            #     text_add = 'Заявка{}'.format('✈')
            # if add:
            #     bot.send_message(c.message.chat.id, f'yes')
            # else:
            #     bot.send_message(c.message.chat.id, 'no')
            # if text_add:
            #     send_message(text_add, c.message, keyboard)
            # else:
            #     send_message('text_add', c.message, keyboard)
        # bot.send_message(message.chat.id, 'testt')
            text_add += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
                add[2],add[3],month(add[4]),add[5], add[6]) if add[7].find(
                'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],add[3],month(add[4]),add[5], add[6])

            # bot.send_message(c.message.chat.id, 'test')
            # bot.send_message(c.message.chat.id, f'add={str(idAdd)}')
            # bot.send_message(c.message.chat.id, text_add)
            #time.sleep(1)
            #back(c.message, 'edit')
            msg = c.data.split('?')[0].split('$')[1]
            if msg != None:
                add = db.executeSql('select * from adds where idAdds={}'.format(idAdd))[0]
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(
                    types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{str(idAdd) + "@" + str(msg)}'),
                    types.InlineKeyboardButton('Опубликовать', callback_data=f'cd@{str(idAdd) + "@" + str(msg)}'))
                text = 'Заявка {}'.format('🚗') if add[7].find('Car') != -1 else 'Заявка{}'.format(
                    '✈')
                text += ' Хочу отправить \n{} - {} : {}\n{}\nконтакты: {}'.format(
                    add[2],add[3],month(add[4]),add[5], add[6]) if add[7].find(
                    'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\n{}\nтел. {}'.format(add[2],add[3],month(add[4]),add[5], add[6])

                bot.edit_message_text(text, c.message.chat.id, msg, reply_markup=keyboard)
            else:
                addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
                addsKeyboard.add('На главную')

                bot.register_next_step_handler(send_message('Заявки:', c.message, addsKeyboard, 'adds', foto='MyAdds'),
                                               searchAdds)
                adds = filterAdds(c.message)
                if adds != None:
                    printAdds(c.message, adds, None, True, False, True)


    def month(d):
        ymonth = [0, 'Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентьбря', 'Октября',
                  'Ноября', 'Декабря']
        day = date.fromisoformat(d)

        return '{} {} {}'.format(day.day, ymonth[day.month], str(day.year))


    def region(r):
        reg = {'tr': 'Турция', 'kz': 'Казахстан', 'ru': 'Россия', 'az': 'Азербайджан', 'th': 'Таиланд',
               'kg': 'Киргизия', 'id': 'Индонезия', 'qa': 'Катар', 'ae': 'Объединенные Арабские Эмираты',
               'am': 'Армения', 'eg': 'Египет', 'us': 'Соединенные Штаты', 'by': 'Беларусь', 'bg': 'Болгария'}
        return reg[r]


    @bot.callback_query_handler(func=lambda call: call.data.find('5calendar') == 0)
    def cal(c):
        
        inf = c.message.chat.id
        status_release = 'release'
        type_adds = SEARCH_DATA.get(f'{inf}')
        
        adds_one_city = None
        adds_two_city = None
        today = date.today().isoformat()
        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        search = db.executeSql(
            'select * from history where UID={} and status like "{}%"'.format(c.message.chat.id, 'searchChoosedCity'))[0]
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Поиск по дате и маршруту', 'Поиск по дате и городу отправления')

        keyboard.add('На главную')
        log(c.message.chat.id, 'поиск по дате', result, 'search')
        if search[4] == None:
            adds_one_city = db.executeSql(
                'select * from adds where city1="{}" and date ="{}" and status="{}" and type = "{}" order by date asc'.format(
                    search[3],
                    result,
                    status_release, type_adds))
            
        else:
            loc_city1 = db.executeSql(f'select local from cities where name="{search[3]}"')[0][0]
            loc_city2 = db.executeSql(f'select local from cities where name="{search[4]}"')[0][0]
            lCity1 = [k[0] for k in db.executeSql(f'select name from cities where local="{loc_city1}"')]
            lCity2 = [k[0] for k in db.executeSql(f'select name from cities where local="{loc_city2}"')]
            lCity2 = str(lCity2).replace('[', '(').replace(']', ')')
            lCity1 = str(lCity1).replace('[', '(').replace(']', ')')
            adds_two_city = db.executeSql(
                'select * from adds where city1 in {} and city2 in {} and date ="{}" and status = "{}" and type = "{}"'.format(
                    lCity1,
                    lCity2,
                    result,
                    status_release,
                    type_adds))
            adds_two_city += db.executeSql(
                'select * from adds where city1 in {} and city2 in {} and date in ("{}","{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}") and status = "{}" and type = "{}" order by date asc'.format(
                    lCity1, lCity2,
                    date.fromisoformat(result) + timedelta(days=1), date.fromisoformat(result) + timedelta(days=-1),
                    date.fromisoformat(result) + timedelta(days=2), date.fromisoformat(result) + timedelta(days=-2), date.fromisoformat(result) + timedelta(days=3), date.fromisoformat(result) + timedelta(days=-3), date.fromisoformat(result) + timedelta(days=4), date.fromisoformat(result) + timedelta(days=-4), date.fromisoformat(result) + timedelta(days=5), date.fromisoformat(result) + timedelta(days=-5), status_release, type_adds))
        back(c.message, 'search')
        msg = send_message('Найденные заявки', c.message, keyboard, state='search')
        db.executeSql('delete from history where UID ={}'.format(c.message.chat.id), True)
        back(c.message, 'calendar')
        
        '''
        if not adds_one_city:
            send_message('Заявок на указанную дату нет', c.message, state='search')
        '''
        if search[4] == None:
            if adds_one_city:
                printAdds(msg, adds_one_city, 'collapse', False, True, False)
            
            else:
                send_message('Заявок на указанную дату нет', c.message, state='search')
        else:
            if adds_two_city:
                key = types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton('Показать', callback_data=f'show@{loc_city1}@{loc_city2}@{result}'))
                send_message(f'Предложений по направлению {region(loc_city1)} - {region(loc_city2)} сейчас {len(adds_two_city)}',
                            c.message,
                            key, state='search')
            if not adds_two_city:
                send_message('Заявок на указанную дату нет', c.message, state='search')
        
        bot.clear_step_handler_by_chat_id(chat_id=c.message.chat.id)

        bot.register_next_step_handler(msg, getAdds,
                                       'Air')
        

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
                date.fromisoformat(result) + timedelta(days=2), date.fromisoformat(result) + timedelta(days=-2),date.fromisoformat(result) + timedelta(days=3), date.fromisoformat(result) + timedelta(days=-3),
                date.fromisoformat(result) + timedelta(days=4), date.fromisoformat(result) + timedelta(days=-4), date.fromisoformat(result) + timedelta(days=5), date.fromisoformat(result) + timedelta(days=-5), status_release, type_adds))
        printAdds(c.message, altAdds, 'collapse', False)


    @bot.callback_query_handler(func=lambda call: call.data.find('6calendar') == 0)
    def cal(c):

        # result = date(int(date.today().year), int(c.data.split("?")[1].split("@")[0]),
        #               int(c.data.split("?")[1].split("@")[1])).isoformat()
        result = date(
            int(c.data.split('?')[1].split('@')[-1]), 
            int(c.data.split("?")[1].split("@")[0]),
            int(c.data.split("?")[1].split("@")[1])).isoformat()
        log(c.message.chat.id, 'поиск по дате', result, 'search')
        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Поиск по дате и направлению', 'Поиск по дате')
        keyboard.add('Поиск по направлению', 'На главную')
        back(c.message, 'search')
        bot.register_next_step_handler(send_message('Найденные заявки', c.message, keyboard, state='search'), getAdds,
                                       '')
        db.executeSql('delete from history where UID ={}'.format(c.message.chat.id), True)

        if result:
            adds = db.executeSql('select * from adds where date="{}"'.format(result))
            printAdds(c.message, adds, 'expand')


    @bot.callback_query_handler(func=lambda call: call.data.find('erase') != -1)
    def erase(c):
        bot.delete_message(c.message.chat.id, c.message.id)
        id = int(c.data.split('@')[1])
        ad = db.executeSql('select * from adds where idAdds={}'.format(id))[0]
        log(c.message.chat.id, 'удалил заявку', str(id), 'search')
        '''lastIds=db.executeSql(f'select lastMsg from msg where UID={c.message.chat.id}')[0][0].replace(f'{c.message.id}@','')


        db.executeSql('update msg set lastMsg="{}" where UID={}'.format(lastIds,c.message.chat.id),True)'''
        db.executeSql('delete from adds where idAdds="{}"'.format(id, True))
        db.executeSql('delete from possibleAdds where delyAdd={} or sendAdd={}'.format(id, id))
        send_message('Запись удалена.', c.message, state='erase')


    @bot.callback_query_handler(func=lambda call: call.data.find('edit') == 0)
    def edit(c):

        bot.clear_step_handler_by_chat_id(c.message.chat.id)
        title = False

        id = c.data.split('@')[1]
        log(c.message.chat.id, 'нажал', 'изменить заявку ' + id, 'btn')
        if db.executeSql('select title from adds where idAdds={}'.format(id))[0][0] != None:
            title = True

        bot.register_next_step_handler(
            send_message('Что меняем?', c.message, keyboards.editK(title, checkAdm(c.message.chat.id)), 'edit'),
            editAdds, id if len(c.data.split('@')) == 2 else id + f'@{c.message.id}')


    '''@bot.callback_query_handler(func=lambda call: call.data.find('back')!=-1)
    def back(c):
        bot.clear_step_handler(c.message)'''


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


    @bot.callback_query_handler(func=lambda call: call.data.find('home') != -1)
    def home(c):
        welcome(c.message)


    @bot.callback_query_handler(func=lambda call: call.data.find('code') != -1)
    def code(c):
        if c.data == 'win_codeAdd':
            db.executeSql('update users set countAdds={} where UID={}'.format(1, c.message.chat.id), True)
            bot.delete_message(c.message.chat.id, c.message.id)
            bot.register_next_step_handler(
                send_message('Укажите город отправки', c.message, keyboards.getCity('Air'), 'chooseCity1',
                             foto='carCity1'), chooseCity1,'createAddsSend' +'Air')

        elif c.data == 'wrong_codeAdd':
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('win_codeView') != -1:
            db.executeSql('update users set countViews=1 where UID={}'.format(c.message.chat.id), True)
            c.data = 'expand@{}@count'.format(c.data.split('@')[1])
            expand(c)
        elif c.data.find('wrong_codeView') != -1:
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('wrong_codeRelease') != -1:
            bot.answer_callback_query(c.id, 'Неверный код!', False)
        elif c.data.find('win_codeRelease') != -1:
            pass


    @bot.callback_query_handler(func=lambda call: call.data.find('city') != -1)
    def setCity(c):
        bot.clear_step_handler_by_chat_id(c.message.chat.id)
        idCity = c.data.split('?')[0].split('@')[1]

        city = db.executeSql('select name from cities where id={}'.format(idCity))[0][0]
        type = c.data.split("?")[1]

        if c.data.split('?')[0].split('@')[0].find('city1') != -1:

            if type.find('editCity1') != -1:
                db.executeSql('update adds set city1="{}" where idAdds={}'.format(city, type.split('@')[1]), True)
                send_message('Город изменен', c.message, state='setCity')
                welcome(c.message)
            elif type.find('searchSend') != -1 or type.find('searchDely') != -1 or type.find('searchSwapTick') != -1:
                bot.delete_message(c.message.chat.id, c.message.id)
                db.executeSql(
                    'insert into history(UID,type,city1,status) values({},"{}","{}","{}")'.format(
                        int(c.message.chat.id),
                        type, city,
                        'searchChoosedCity1'),
                    True)

                bot.register_next_step_handler(
                    send_message('Отлично! Теперь введите город назначения', c.message, state='setCity'), searchCity,
                    type,
                    'city2')
            else:
                bot.delete_message(c.message.chat.id, c.message.id)
                db.executeSql(
                    'insert into history(UID,type,city1,status) values({},"{}","{}","{}")'.format(
                        int(c.message.chat.id),
                        type, city,
                        'coosedCity1'), True)
                if type != 'tickSwap':
                    msg = send_message('Отлично! Теперь введите город получения', c.message, False)

                else:
                    msg = send_message('Отлично! Теперь введите город назначения', c.message, False)

                bot.register_next_step_handler(msg, searchCity, type, 'city2')

        if c.data.split('?')[0].split('@')[0].find('city2') != -1:

            if type.find('editCity2') != -1:
                db.executeSql('update adds set city2="{}" where idAdds={}'.format(city, type.split('@')[1]), True)
                send_message('Город изменен', c.message, False)
                welcome(c.message)
            elif type.find('searchSend') != -1 or type.find('searchDely') != -1 or type.find('searchSwapTick') != -1:
                db.executeSql(
                    'update history set city2="{}" where UID={} and status="{}"'.format(city, c.message.chat.id,
                                                                                        'searchChoosedCity1'),
                    True)
                db.executeSql(
                    'update history set status="{}" where UID={} and status="{}"'.format('searchChoosedCity2',c.message.chat.id,'searchChoosedCity1'), True)
                send_message('Выберете дату:', c.message, state='setCity')
                calendar(5, c.message)






            else:
                db.executeSql(
                    'update  history set city2="{}"  where UID={} and type="{}"'.format(city, int(c.message.chat.id),
                                                                                        type), True)
                db.executeSql(
                    'update  history set status="{}"  where UID={} and type="{}"'.format('choosedCity2',
                                                                                         int(c.message.chat.id), type),
                    True)
                send_message(f"Выберите дату", c.message, state='setCity')
                if type.find('createAddsSend') != -1:
                    calendar(1, c.message)

                if type.find('createAddsDely') != -1:
                    calendar(2, c.message)
                if type.find('swapTick') != -1:
                    calendar(3, c.message)


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


    @bot.callback_query_handler(func=lambda call: call.data.find('hide') != -1)
    def hide(c):
        back(c.message, 'donate')


    @bot.callback_query_handler(func=lambda call: call.data.find('donate') != -1)
    def hideD(c):
        back(c.message, 'donate')


    @bot.callback_query_handler(func=lambda call: call.data.find('expand') != -1)
    def expandC(c):
        print(c.data)
        edit = True if c.data.find('Edit') != -1 else False
        countf = True if c.data.find('Count') != -1 else False
        possible = True if c.data.find('possible') != -1 else False
        seen = int(c.data.split('/')[3]) if c.data.find('Seen') != -1 else None
        id = int(c.data.split('@')[1])
        log(c.message.chat.id, 'нажал', 'раскрыть ' + str(id), 'btn')
        count = db.executeSql('select countViews from users where UID={}'.format(c.message.chat.id))[0][0]
        if checkAdm(c.message.chat.id) or countf == False:
            if checkAdm(c.message.chat.id) == False and c.data.find('NoCount') == -1:
                db.executeSql('update users set countViews={} where UID={}'.format(count - 1, c.message.chat.id), True)
            printAdds(c.message, db.executeSql('select * from adds where idAdds={}'.format(id)), 'collapse', edit,
                      countf, False, seen, c.message.id)

            '''ad=db.executeSql('select * from adds where idAdds={}'.format(id))[0]
            call = f'collapse@{ad[1]}' if c.data.find('Edit') == -1 else f'collapseEdit@{ad[1]}'
            call += '@noCount' if c.data.find('noCount') != -1 else '@count'
            user=db.executeSql('select * from users where UID={}'.format(ad[0]))[0]
            username =user[3]
            text = 'Заявка с ресурса: {}\n'.format(ad[9]) if ad[9] not in ['None', None, ''] and checkAdm(
                c.message.chat.id) else ''
            text += 'Заявка  №{} {}'.format(ad[1], '🚗') if ad[7].find('Car') != -1 else 'Заявка  №{} {}'.format(ad[1], '✈')
            text += ' Хочу отправить \n{} - {} : {}\nКонтакты: {}'.format(ad[2], ad[3], month(ad[4]), ad[6]) if ad[7].find(
                'Send') != -1 else 'Могу доставить {}\n{} - {} : {}\nКонтакты: {}'.format(
                '(возьму попутчика🙋🏻‍♂️)' if ad[8] not in (None, 'False') else '', ad[2], ad[3], month(ad[4]), ad[6])

            reviews = db.executeSql('select * from reviews where contact="{}"'.format(username))
            reviews +=  db.executeSql('select * from reviews where contact="{}"'.format(ad[6]))
            if len(reviews) > 0:
                help=''
                for r in reviews:help+='@'+r+', '
                text+='\ntg:@{} \n Помог пользователям:\n{}'.format(username, help) if username != None else '\ntg:[{}](tg://user?id={})\nПомог пользователям:\n{}'.format(user[6],user[0],help)

            else:
                if user[1]!='admin':
                    text += '\ntg:@{}'.format(username) if username != None else '\ntg:[{}](tg://user?id={})'.format(user[6],user[0])
            text=entity(text)
            expandK = types.InlineKeyboardMarkup()
            if c.data.find('seen')!=-1:
                call+='@seen'
                expandK.add(
                    types.InlineKeyboardButton('Скрыть', callback_data=call), types.InlineKeyboardButton('Отработано', callback_data=c.message.reply_markup.keyboard[1][0].callback_data))

            elif c.data.find('Edit')==-1:
                expandK.add(
                    (types.InlineKeyboardButton('Скрыть', callback_data=call)))
            else:
                expandK.add(types.InlineKeyboardButton('Редактировать', callback_data=f'edit@{ad[1]}'),
                            types.InlineKeyboardButton('Удалить', callback_data=f'erase@{ad[1]}'))
                expandK.add(
                    (types.InlineKeyboardButton('Скрыть', callback_data=call)))


            bot.edit_message_text(text, c.message.chat.id,
                                  c.message.id,parse_mode='MarkdownV2')
            bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)'''

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

        '''if username == None:
            if ad[7].find('Car') != -1:

                if ad[7].find('Send') != -1:
                    text='Заявка  №{} 🚗 Хочу отправить \n{} - {} : {}\n{}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                              month(ad[4]), ad[5],
                                                                              ad[6])
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))

                    bot.edit_message_text('Заявка  №{} 🚗 Хочу отправить \n{} - {} : {}\n{}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                              month(ad[4]), ad[5],
                                                                              ad[6]),c.message.chat.id,c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id,c.message.id,reply_markup=expandK)
                if ad[7].find('Dely') != -1:
                    if ad[8] in (None,'False'):
                        text='Заявка  №{} 🚗 Могу доставить \n{} - {} : {}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                           month(ad[4]),
                                                                                           ad[6])
                    else:
                        text = 'Заявка  №{} 🚗 Могу доставить (возьму попутчика🙋🏻‍♂️)\n{} - {} : {}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                                  month(ad[4]),
                                                                                                  ad[6])

                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        text, c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
            if ad[7].find('Air') != -1:
                if ad[7].find('Send') != -1:
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        'Заявка  №{} ✈ Хочу отправить \n{} - {} : {}\n{}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                                   month(ad[4]), ad[5],
                                                                                                   ad[6]),
                        c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
                if ad[7].find('Dely') != -1:
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        'Заявка  №{} 🚗 Могу доставить \n{} - {} : {}\nтел. {}'.format(ad[1], ad[2], ad[3],
                                                                                           month(ad[4]),
                                                                                           ad[6]), c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
        else:

            if ad[7].find('Car') != -1:

                if ad[7].find('Send') != -1:
                    text = 'Заявка  №{} 🚗 Хочу отправить \n{} - {} : {}\n{}\nтел. {}\ntg:@{}'.format(ad[1], ad[2], ad[3],
                                                                                              month(ad[4]), ad[5],
                                                                                              ad[6],username)
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))

                    bot.edit_message_text(
                        'Заявка  №{} 🚗 Хочу отправить \n{} - {} : {}\n{}\nтел. {}\ntg:@{}'.format(ad[1], ad[2], ad[3],
                                                                                           month(ad[4]), ad[5],
                                                                                           ad[6],username), c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
                if ad[7].find('Dely') != -1:
                    if ad[8] in (None, 'False'):
                        text = 'Заявка  №{} 🚗 Могу доставить \n{} - {} : {}\nтел. {}\ntg:@{}'.format(ad[1], ad[2], ad[3],
                                                                                                  month(ad[4]),
                                                                                                  ad[6],username)
                    else:
                        text = 'Заявка  №{} 🚗 Могу доставить (возьму попутчика🙋🏻‍♂️)\n{} - {} : {}\nтел. {}\ntg:@{}'.format(
                            ad[1], ad[2], ad[3],
                            month(ad[4]),
                            ad[6],username)

                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        text, c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
            if ad[7].find('Air') != -1:
                if ad[7].find('Send') != -1:
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        'Заявка  №{} ✈ Хочу отправить \n{} - {} : {}\n{}\nтел. {}\ntg:@{}'.format(ad[1], ad[2], ad[3],
                                                                                                  month(ad[4]), ad[5],
                                                                                                  ad[6], username),
                        c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)
                if ad[7].find('Dely') != -1:
                    expandK = types.InlineKeyboardMarkup().add(
                        (types.InlineKeyboardButton('Скрыть', callback_data=f'collapse{ad[1]}')))
                    bot.edit_message_text(
                        'Заявка  №{} 🚗 Могу доставить \n{} - {} : {}\nтел. {}\ntg:@{}'.format(ad[1], ad[2], ad[3],
                                                                                           month(ad[4]), ad[5],
                                                                                           ad[6],username), c.message.chat.id,
                        c.message.id)
                    bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)'''



    @bot.callback_query_handler(func=lambda call: call.data.find('save') != -1)
    def save_bid(c):
        id = c.data.split('@')[1]
        db.executeSql(f'update adds set status="release" where idAdds={id}')
        ad = db.executeSql('select * from adds where idAdds={}'.format(id))[0]

        log(c.message.chat.id, 'создал заявку {} {} {}'.format(ad[2], ad[3], ad[4]),
            '{} {}'.format(ad[5], ad[6]), 'add')

        keyboard = types.ReplyKeyboardMarkup(True, True)
        keyboard.add('Мои заявки', 'На главную')

        if ad[7].find('createAddsSend') != -1:
            bot.register_next_step_handler(send_message(
                f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                c.message, keyboard, state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        if ad[7].find('createAddsDely') != -1:
            bot.register_next_step_handler(send_message(
                f'Заявка № {id} создана. Встречные предложения, а также возможность редактирования заявки доступны в меню "Мои заявки"',
                c.message, keyboard, state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        db.executeSql(
            'delete from history where UID={} and status="{}"'.format(c.message.chat.id, 'readyDeal'), True)
        if ad[7].find('swapTick') != -1:
            bot.register_next_step_handler(
                send_message(f'Заявка №{id} на обмен билетов добавлена', c.message, keyboard,
                             state='creatDealContact', foto='carCreateDeal'), creatDealContact, 0)

        settings.Thread(target=settings.worker(60).search, name='search', args=(id, ad[7])).start()


    @bot.callback_query_handler(func=lambda call: call.data.find('bid') != -1)
    def collapseC(c):
        print(c)
        
        id = int(c.data.split('@')[1])
        log(c.message.chat.id, 'нажал', 'скрыть ' + str(id), 'btn')
        ad = db.executeSql('select * from adds where idAdds={}'.format(id))
        edit = True if c.data.find('Edit') != -1 else False
        countf = True if c.data.find('Count') != -1 else False
        seen = int(c.data.split('/')[3]) if c.data.find('Seen') != -1 else None
        # bot.send_message(c.message.chat.id, ad)
        # bot.delete_message(c.message.chat.id, c.message.message_id - 1) 
        
        printAdds(c.message, ad, 'expand', edit, countf, False, seen, c.message.id)
        # printAdds(c.message, ad, 'expand', edit, countf, False, seen, c.message.id)







    @bot.callback_query_handler(func=lambda call: call.data.find('collapse') != -1)
    def collapseC(c):
        print(c)
        bot.delete_message(c.message.chat.id, c.message.message_id)
        id = int(c.data.split('@')[1])
        log(c.message.chat.id, 'нажал', 'показать информацию ' + str(id), 'btn')
        ad = db.executeSql('select * from adds where idAdds={}'.format(id))
        edit = True if c.data.find('Edit') != -1 else False
        countf = True if c.data.find('Count') != -1 else False
        seen = int(c.data.split('/')[3]) if c.data.find('Seen') != -1 else None
        if not checkAdm(c.message.chat.id):
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
                                                                callback_data=f'bid@{id}'))
                else:
                    keys.append(types.InlineKeyboardButton(text=f'{code}', callback_data=f'wrong_codeAdd'))
            key_code.add(*keys, row_width=4)
            addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
            addsKeyboard.add('На главную')
            send_message(
                    'Скоро тут будет монетизация, а пока решите {}+{} для продолжения'.format(
                    a, b), c.message, key_code, state='createAdds')
        else:
            printAdds(c.message, ad, 'expand', edit, countf, False, seen, c.message.id)
        '''call = f'expand@{ad[1]}' if c.data.find('Edit') == -1 else f'expandEdit@{ad[1]}'
        call += '@noCount' if c.data.find('noCount') != -1 else '@count'
        expandK = types.InlineKeyboardMarkup()
        if c.data.find('seen')!=-1:
            call+='@seen'
            expandK.add(
                (types.InlineKeyboardButton('Раскрыть', callback_data=call)))

            expandK.add(types.InlineKeyboardButton('Отработано', callback_data=c.message.reply_markup.keyboard[0][1].callback_data))
        else:
            expandK.add(
                (types.InlineKeyboardButton('Раскрыть', callback_data=call)))

        text = 'Заявка с ресурса: {}\n'.format(ad[9]) if ad[9] not in ['None', None, ''] and checkAdm(
            c.message.chat.id) else ''
        text += 'Заявка  №{} {}'.format(ad[1], '🚗') if ad[7].find('Car') != -1 else 'Заявка  №{} {}'.format(ad[1], '✈')
        text += ' Хочу отправить \n{} - {} : {}'.format(ad[2], ad[3], month(ad[4])) if ad[7].find(
            'Send') != -1 else 'Могу доставить {}\n{} - {} : {}'.format(
            '(возьму попутчика🙋🏻‍♂️)' if ad[8] not in (None, 'False') else '', ad[2], ad[3], month(ad[4]))
        text=entity(text)
        bot.edit_message_text(text, c.message.chat.id,
                              c.message.id, parse_mode='MarkdownV2')
        bot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=expandK)'''


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

