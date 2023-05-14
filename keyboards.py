import json
import telebot

import dbConn

#from dbConn import redis_client



def mainK(id,admin=False):
    count=dbConn.executeSql(f"select count(id) from possible where dely in (select id from adds where uid={id} and type='dely') or send in (select id from adds where uid={id} and type='send')")[0][0]
    main = telebot.types.ReplyKeyboardMarkup(True, True)
    #main.add('Хочу отправить', 'Могу доставить')
    main.add('Могу доставить')
    main.add('Поиск','Все заявки') if admin else main.add('Поиск','Памятка пользователя')
    text='Мои заявки' if not count else 'Мои заявки ({})'.format(count)
    main.add(text, f'Стоимость')


    return main

feedKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
feedKeyboard.add('Написать отзыв о боте','Похвалить пользователя')
feedKeyboard.add('На главную')
supKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
supKeyboard.add('Выход','На главную')
wantSendKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
wantSendKeyboard.add('Поиск','На главную')
wantDelyKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
wantDelyKeyboard.add('Поиск','На главную')
def editK(title=False,admin=False):
    editKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
    if admin:
        editKeyboard.add('Ресурс')

    editKeyboard.add('Город оправки','Город прибытия')

    editKeyboard.add('Дату','Контактные данные')
    if title:
        editKeyboard.add('Описание','На главную')
    else:
        editKeyboard.add('На главную')
    return  editKeyboard

def keys(modes=['main']):
    keyboard=telebot.types.ReplyKeyboardMarkup(True, True)
    for mode in modes:
        match mode:
            case 'main':
                keyboard.add('На главную')
    return keyboard





def getCity(mask=None):
    cityArr=[]
    citiesK = telebot.types.ReplyKeyboardMarkup(True, True)
    citiesK.add('На главную')
    cities= dbConn.executeSql('select name from cities order by name ASC') if mask is None else dbConn.executeSql('select name from cities where name !="{}" order by name ASC'.format(mask))
    for city in cities:
        cityArr.append(city[0])
        if len(cityArr)==2:
            citiesK.add(*cityArr)
            cityArr.clear()

    return citiesK

cities=[c[0] for c in dbConn.executeSql("select name from cities")]

