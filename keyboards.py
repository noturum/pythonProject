import json
import telebot

import dbConn

#from dbConn import redis_client



def mainK(id,admin=False):


    count=dbConn.executeSql(f'select count(id) from possible where dely in (select id from adds where uid={id} and type="dely") or send in (select id from adds where uid={id} and type="send")')[0][0]

    main = telebot.types.ReplyKeyboardMarkup(True, True)
    main.add('Хочу отправить', 'Могу доставить')
    main.add('Поиск','Памятка пользователя')

    if admin:
        main.add('Все заявки', f'Стоимость','Мои заявки' if count else 'Мои заявки ({})'.format(count))
        main.add('Ресурс')

    else:
        text='Мои заявки' if not count else 'Мои заявки ({})'.format(count)
        main.add(text, f'Стоимость')

    return main
    
def addK(type):
    addsKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    if type=='Air':

        addsKeyboard.add('Хочу отправить','Могу доставить')
        addsKeyboard.add('Готовые заявки','На главную')
    if type=='Car':

        addsKeyboard.add('🙋‍♂️📦 Хочу отправить', '🙋‍♂️🚘 Могу доставить')
        addsKeyboard.add('📝 Готовые заявки', 'На главную')
    return addsKeyboard
dealKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
dealKeyboard.add('Хотят отправить','Могут доставить')
dealKeyboard.add('На главную')
tickKeyboard=telebot.types.ReplyKeyboardMarkup(True, True)
tickKeyboard.add('Обменять свой билет')
tickKeyboard.add('Поиск','На главную')
'''anskey=types.InlineKeyboardMarkup()
		ans=types.InlineKeyboardButton(text='Хочу топравить')'''
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

def garantDely(adm=False):
    gdKeyboard = telebot.types.ReplyKeyboardMarkup(True, True)
    if adm:
        gdKeyboard.add('Добавить', 'На главную')
    else:
        gdKeyboard.add('На главную')
    return gdKeyboard


cancel = telebot.types.InlineKeyboardMarkup()
can = telebot.types.InlineKeyboardButton(callback_data = 'can', text = 'Отмена')
cancel.add(can)

zayav = telebot.types.InlineKeyboardMarkup()
zaya = telebot.types.InlineKeyboardButton(callback_data = 'zaya', text = 'Создать заявку')
zayav.add(zaya)

zayav1 = telebot.types.InlineKeyboardMarkup()
zaya1 = telebot.types.InlineKeyboardButton(callback_data = 'zaya1', text = 'Создать заявку')
zayav1.add(zaya1) 

otpr_new_old = telebot.types.InlineKeyboardMarkup()
sear_otpr = telebot.types.InlineKeyboardButton(callback_data = 'sear_otpr', text = 'Выбрать из существующих предложений')
otpr_new_old.add(zaya)
otpr_new_old.add(sear_otpr)

pere_new_old = telebot.types.InlineKeyboardMarkup()
sear_pere = telebot.types.InlineKeyboardButton(callback_data = 'sear_pere', text = 'Выбрать из существующих предложений')
pere_new_old.add(zaya1)
pere_new_old.add(sear_pere)

transport = telebot.types.ReplyKeyboardMarkup(True, True)
transport.add('Автомобиль 🚗', 'Самолет ✈')
transport.add('На главную')

otpr_new_old1 = telebot.types.InlineKeyboardMarkup()
sear_otpr1 = telebot.types.InlineKeyboardButton(callback_data = 'sear_otpr', text = 'Новый поиск')
otpr_new_old1.add(zaya)
otpr_new_old1.add(sear_otpr1)

pere_new_old1 = telebot.types.InlineKeyboardMarkup()
sear_pere1 = telebot.types.InlineKeyboardButton(callback_data = 'sear_pere', text = 'Новый поиск')
pere_new_old1.add(zaya1)
pere_new_old1.add(sear_pere1)
alp=['А','Б','В','Г','Д','Е','Ж','З','И','К','Л','М','Н','О','П','Р','С','Т','У','Ф','Х','Ч','Ш','Щ','Э','Ю','Я']
def getAlp():
    alpKey=telebot.types.ReplyKeyboardMarkup(True, True)
    alp = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ж', 'З', 'И', 'К', 'Л', 'М', 'Н', 'О', 'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ч',
           'Ш', 'Щ', 'Э', 'Ю', 'Я']
    alpAr=[]
    for key in alp:
        alpAr.append(key)
        if len(alpAr)==2:
            alpKey.add(*alpAr)
            alpAr.clear()
        if alp.index(key)==len(alp)-1:
            alpKey.add(*alpAr,'На главную')



    return alpKey

def getCity(mask=None):
    cityArr=[]
    citiesK = telebot.types.ReplyKeyboardMarkup(True, True)
    citiesK.add('На главную')
    cities= dbConn.executeSql('select name from cities') if mask is None else dbConn.executeSql('select name from cities where name !="{}"'.format(mask))
    for city in cities:
        cityArr.append(city[0])
        if len(cityArr)==2:
            citiesK.add(*cityArr)
            cityArr.clear()

    return citiesK
    '''citys.add('Москва', 'Санкт - Петербург')
    citys.add('Астрахань', 'Баку')
    citys.add('Волгоград', 'Грозный')
    citys.add('Дубай', 'Екатеринбург')
    citys.add('Казань', 'Калининград')
    citys.add('Краснодар', 'Красноярск')
    citys.add('Магас', 'Махачкала')
    citys.add('Минеральные Воды', 'Мурманск')
    citys.add('Нальчик', 'Новосибирск')
    citys.add('Ростов-на-Дону', 'Симферополь')
    citys.add('Сочи', 'Стамбул')
    citys.add('Сургут', 'Тюмень')'''

delete = telebot.types.InlineKeyboardMarkup()
delet = telebot.types.InlineKeyboardButton(callback_data = 'delete', text = 'Удалить заявку')
delete.add(delet)
cities=[c[0] for c in dbConn.executeSql('select name from cities')]

#cities=('Москва', 'Санкт - Петербург','Астрахань', 'Баку','Волгоград', 'Грозный','Дубай', 'Екатеринбург','Казань', 'Калининград','Краснодар', 'Красноярск','Магас', 'Махачкала','Минеральные Воды', 'Мурманск','Нальчик', 'Новосибирск','Ростов-на-Дону', 'Симферополь','Сочи', 'Стамбул','Сургут', 'Тюмень')