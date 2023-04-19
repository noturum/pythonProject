import configparser
import time

import telebot
from threading import Thread
import dbConn as dc
import dbConn
import datetime
from datetime import date

config = configparser.ConfigParser()
config.read('/root/bot/settings.ini')
bot = telebot.TeleBot(config['telegram']['token'])
def compare(dely,send):
    pass

def notify(uid,text,state,clear=False):
    if uid:
        print(uid)
        if clear==False:
            try:
                if isinstance(uid,list):
                    for id in uid:
                        if len(dbConn.executeSql('select * from notify where UID={} and state="{}"'.format(id,state)))>0:
                            lastMsg=dbConn.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id,state))[0][0]
                            dbConn.executeSql('update notify set lastMsg="{}" where UID={} and state="{}"'.format('{}@{}'.format(lastMsg,bot.send_message(id,text).id),id,state),True)

                        else:
                            dbConn.executeSql('insert into notify(UID,lastMsg,state) values({},"{}","{}")'.format(id,bot.send_message(id,text).id,state), True)


                '''else:
                    if len(db.executeSql('select * from notify where UID={} and state="{}"'.format(uid,state)))!=0:
                        lastMsg=db.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(uid ,state))[0][0]
                        db.executeSql('update notify set lastMsg="{}" where UID={} and state="{}"'.format('{}@{}'.format(lastMsg,bot.send_message(uid,text).id), uid,state),True)
                    else:
                        db.executeSql('insert into notify(UID,lastMsg,state) values({},"{}","{}")'.format(uid,bot.send_message(uid,text).id),state, True)'''
            except Exception as e:
                print(e)
        else:
            try:
                if isinstance(uid,list):
                    for id in uid:
                        lastMsg=dbConn.executeSql('select lastMsg from notify where UID={} and state="{}"'.format(id,state))[0][0]
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
class worker():
    def __init__(self, timeout):
        self.timeout = timeout

    def cleaner(self):


        while True:
            print('cleaner run')
            adds = dbConn.executeSql('select * from adds')
            for ad in adds:
                if datetime.date.fromisoformat(ad[4]) < datetime.date.today():

                    dbConn.executeSql('delete from adds where idAdds={}'.format(ad[1]), True)
                    dbConn.executeSql('delete from possibleAdds where sendAdd={} or delyAdd={}'.format(ad[1],ad[1]),True)
            users=dbConn.executeSql('select * from users')
            for user in users:
                if date.fromisoformat(user[7])<date.today():
                    res = date(date.today().year, date.today().month, date.today().day)
                    dbConn.executeSql('update users set lastUpdate="{}" where UID={}'.format(res,user[0]),True)
                    dbConn.executeSql('update users set countAdds={} where UID={}'.format(2,user[0]), True)
                    dbConn.executeSql('update users set countViews={} where UID={}'.format(5, user[0]), True)
            time.sleep(self.timeout)

    def search(self, id, type,admin=False):
        msgDely = []  # доставщик
        msgSend = []  # отправитель
        sendAdds = None
        delyAdds = None

        time.sleep(.5)

        if type.find('createAddsSend') != -1:
            sendAdds = dbConn.executeSql('select * from adds where  idAdds={}'.format(int(id)))
            if len(sendAdds) > 0:
                uid = sendAdds[0][0]
            else:
                return
            delyAdds = dbConn.executeSql('select * from adds where type like "{}" and UID!={}'.format('createAddsDely%', uid)) if admin == False else dbConn.executeSql('select * from adds where type like "{}" '.format('createAddsDely%'))
        if type.find('createAddsDely') != -1:
            delyAdds = dbConn.executeSql('select * from adds where  idAdds={}'.format(int(id)))
            if len(delyAdds) > 0:
                uid = delyAdds[0][0]
            else:
                return
            sendAdds = dbConn.executeSql('select * from adds where type like "{}" and UID!={}'.format('createAddsSend%', uid)) if admin == False else dbConn.executeSql('select * from adds where type like "{}" '.format('createAddsSend%', ))

        try:
            for sendAdd in sendAdds:
                for delyAdd in delyAdds:
                    local = dbConn.executeSql('select local from cities where name="{}"'.format(sendAdd[3]))
                    if len(local) > 0:
                        cities = [city[0] for city in
                                  dbConn.executeSql('select name from cities where local="{}" and name!="{}"'.format(local[0][0],sendAdd[3]))]
                    if sendAdd[2] == delyAdd[2] and sendAdd[3] == delyAdd[3]:
                        if sendAdd[4] == delyAdd[4]:
                            dbConn.executeSql('insert into possibleAdds(sendAdd,delyAdd,overlap,active) values ("{}","{}","{}","True")'.format(sendAdd[1],delyAdd[1],'all'),True)
                            notify([sendAdd[0],delyAdd[0]],'Новое совпадение, пожалуйста проверьте "мои заявки"','adds')
                            '''hideK = telebot.types.InlineKeyboardMarkup()
                            hideK.add(telebot.types.InlineKeyboardButton('Скрыть', callback_data='hide'))
                            bot.send_message(sendAdd[0],
                                                 'По вашей заявке: \nМожет доставить {} - {} : {}\n{} \nтел. {}'.format(delyAdd[2],
                                                                                                     delyAdd[3],
                                                                                                     delyAdd[4],
                                                                                                     delyAdd[5],
                                                                                                     delyAdd[6]),
                                                 reply_markup=hideK)

                            hideK = telebot.types.InlineKeyboardMarkup()
                            hideK.add(telebot.types.InlineKeyboardButton('Скрыть', callback_data='hide'))

                            bot.send_message(delyAdd[0],
                                                 'По вашей заявке:\nХочет отправить {} - {} : {}\n{} \nтел. {}'.format(sendAdd[2],
                                                                                                     sendAdd[3],
                                                                                                     sendAdd[4],
                                                                                                     sendAdd[5],
                                                                                                     sendAdd[6]),
                                                 reply_markup=hideK)'''



                        elif datetime.date.fromisoformat(sendAdd[4]) + datetime.timedelta(
                                days=1) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(
                                sendAdd[4]) + datetime.timedelta(days=-1) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(sendAdd[4]) + datetime.timedelta(
                                days=2) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(
                                sendAdd[4]) + datetime.timedelta(days=-2) == datetime.date.fromisoformat(delyAdd[4]):
                            dbConn.executeSql('insert into possibleAdds(sendAdd,delyAdd,overlap,active) values ("{}","{}","{}","True")'.format(sendAdd[1],delyAdd[1],'date'),True)
                            notify ([sendAdd[0],delyAdd[0]],'Новое совпадение, пожалуйста проверьте "мои заявки"','adds')
                            '''hideK = telebot.types.InlineKeyboardMarkup()
                            hideK.add(telebot.types.InlineKeyboardButton('Скрыть', callback_data='hide'))

                            bot.send_message(sendAdd[0],
                                                 'По вашей заявке в ближайшие дни: Может доставит {} - {} : {}\n{} \nтел. {}'.format(delyAdd[2],
                                                                                                    delyAdd[3],
                                                                                                    delyAdd[4],
                                                                                                    delyAdd[5],
                                                                                                    delyAdd[6]),
                                                 reply_markup=hideK)'''
                    if sendAdd[2] == delyAdd[2] and sendAdd[3] in cities:
                        if sendAdd[4] == delyAdd[4]:
                            dbConn.executeSql(
                                'insert into possibleAdds(sendAdd,delyAdd,overlap,active) values ("{}","{}","{}","True")'.format(
                                    sendAdd[1], delyAdd[1], 'local'), True)
                            notify ([sendAdd[0],delyAdd[0]],'Новое совпадение, пожалуйста проверьте "мои заявки"','adds')

                        elif  datetime.date.fromisoformat(sendAdd[4]) + datetime.timedelta(
                                days=1) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(
                                sendAdd[4]) + datetime.timedelta(days=-1) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(sendAdd[4]) + datetime.timedelta(
                                days=2) == datetime.date.fromisoformat(delyAdd[4]) or datetime.date.fromisoformat(
                                sendAdd[4]) + datetime.timedelta(days=-2) == datetime.date.fromisoformat(delyAdd[4]):
                            dbConn.executeSql('insert into possibleAdds(sendAdd,delyAdd,overlap,active) values ("{}","{}","{}","True")'.format(sendAdd[1],delyAdd[1],'location'),True)
                            notify ([sendAdd[0],delyAdd[0]],'Новое совпадение, пожалуйста проверьте "мои заявки"','adds')
                            '''hideK = telebot.types.InlineKeyboardMarkup()
                            hideK.add(telebot.types.InlineKeyboardButton('Скрыть', callback_data='hide'))

                            bot.send_message(sendAdd[0],
                                             'По вашей заявке в ближайшие дни: Может доставит {} - {} : {}\n{} \nтел. {}'.format(
                                                 delyAdd[2],
                                                 delyAdd[3],
                                                 delyAdd[4],
                                                 delyAdd[5],
                                                 delyAdd[6]),
                                             reply_markup=hideK)'''
            return None
        except Exception as e:
            return None
    def donate(self,id):
        pass



procList = []

procList.append(Thread(name='cleaner', target=worker(60 * 60 ).cleaner, daemon=True))
procList[0].start()


def checkProc(name, clean=False):
    for proc in procList:
        if proc != None:
            if proc.name == name:
                if proc.is_alive():
                    return True
                else:
                    if clean:
                        procList.pop(procList.index(proc))
                        proc.join()

                    return False
        else:
            del proc

    return False
