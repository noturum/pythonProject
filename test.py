import datetime
import time

import dbConn

# import dbConn as db
# user =db.executeSql('select UID from users')
# a= ['@'+b[0] for b in user]
# a=str(a).replace('[','').replace(']','')
# import re
city='''Алматы 				
Анталья 				
Астрахань				
Баку 				
о. Бали 				
Бишкек 				
Владивосток				
Волгоград				
Грозный				
Дубай 				
Екатеринбург				
Ереван 				
Иркутск				
Казань				
Каир 				
Красноярск				
Лос-Анжелес 				
Майами 				
Махачкала				
Минеральные Воды				
Минск 				
Москва				
Нижний Новгород				
Новосибирск				
Нур-Султан 				
Нью-Йорк 				
Пермь				
Самара				
Санкт-Петербург				
Сан-Франциско 				
Саратов				
Сочи				
Стамбул 				
Сургут				
Томск				
Тюмень				
Улан-Удэ				
Хабаровск				
Ханты-Мансийск				
Челябинск'''
# import datetime
# newUser=0
# activeUser=0
# week=datetime.date.today()+datetime.timedelta(days=-7)
# logs=db.executeSql('select * from log')
# for log in logs:
#
#     date=log[4].split(' ')[0].split('-')
#     date=datetime.date(int(date[0]),int(date[1]),int(date[2]))
#     if date >week and log[6]=='register':
#         newUser+=1
# print(f'новых пользователей за неделю: {newUser}')
dates=()
from datetime import date, timedelta
import sqlite3
from sqlite3 import Error, OperationalError


'''import dbConn as db


with open('air.txt','r',encoding='utf-8') as f:
    for city in f.readlines():
        db.executeSql('insert into cities(name,local,type) values("{}",{},"{}")'.format(city.replace('\n',''),'777','Air'),True)'''

'''import csv
import dbConn as db
results = []
with open('city.csv') as File:
    reader = csv.DictReader(File)
    lastAirPort=''
    print(reader.fieldnames)'''

'''import telebot
from telebot import types
import configparser
config = configparser.ConfigParser()
config.read('settings.ini')
bot = telebot.TeleBot(config['telegram']['token'])

@bot.message_handler(commands=['start'])
def st(msg):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)

    keyboard.add(button_phone)
    bot.send_message(msg.chat.id,'contact',reply_markup=keyboard)
@bot.message_handler(content_types=['contact'])
def hadle_contact(message):
    print(message)
    bot.send_message(message.from_user.id, f'Я получил твой контакт: {message.contact.phone_number}')
bot.polling()'''



'''local=db.executeSql('select local from cities where name="{}"'.format('Екатеринбург'))
print(local)
if len(local)>0:
    cities=[city[0] for city in db.executeSql('select name from cities where local="{}" '.format(local[0][0]))]
    adds=db.executeSql("select * from adds where city1 in {}".format(tuple(cities)))
    print(adds)'''