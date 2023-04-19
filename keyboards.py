import json
import telebot

import dbConn

from dbConn import redis_client



def mainK(id,admin=False):
    print('q')
    idAdd=[k[0] for k in dbConn.executeSql('select idAdds from adds where UID={}'.format(id))]
    idAdd=str(idAdd).replace('[','(').replace(']',')')
    notify=len(dbConn.executeSql('select * from possibleAdds where sendAdd in {} and active="True"'.format(idAdd)))
    notify+=len(dbConn.executeSql('select * from possibleAdds where delyAdd in {} and active="True"'.format(idAdd)))
    supportA=len(dbConn.executeSql('select * from support where status="await"'))
    supportU = len(dbConn.executeSql('select * from support where status="answer"'))
    main = telebot.types.ReplyKeyboardMarkup(True, True)
    main.add('Хочу отправить', 'Могу доставить')
    main.add('Поиск','Памятка пользователя')
    # main.add('Очистить историю')
    #main.add('Отзывы', 'Партнеры')
    if admin:
        main.add('Все заявки', f'Стоимость','Мои заявки' if notify==0 else 'Мои заявки ({})'.format(notify))
        main.add('Ресурс')

    else:
        text='Мои заявки' if notify==0 else 'Мои заявки ({})'.format(notify)
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

def getCity(type='car',key=None,mask=None):
    cityArr=[]
    if type.find('Car')!=-1:
        type='car'
    if type.find('Air')!=-1:
        type='air'
    citiesK = telebot.types.ReplyKeyboardMarkup(True, True)
    if mask is None:
        if key is None:
            # print(type)
            # print(redis_client.get('cities'))
            cities1 = redis_client.get('cities1')
            if cities1 is not None:
                print('redis')
                cities = json.loads(cities1)
            else:
                cities = dbConn.executeSql('select * from cities where type="{}" order by name'.format(type))
                print('sqlite')
                # print('cities', cities)
                redis_client.set('cities1', json.dumps(cities))


        else:
            cities=dbConn.executeSql('select * from cities where name like "{}%" and type="{}" order by name'.format(key,type))

    else:
        if key is None:
            cities = dbConn.executeSql('select * from cities where type="{}" and name!="{}" order by name'.format(type,mask))

        else:
            cities = dbConn.executeSql(
                'select * from cities where name like "{}%" and type="{}" and name!="{}" order by name'.format(key, type,mask))
    if type.find('car')!=-1:
        citiesK.add('На главную', 'Назад')
    else:

        citiesK.add('На главную')

    for city in cities:
        # print('city = ', city)
        cityArr.append(city[1])
        if len(cityArr)==2:
            # print('cityArr = ', cityArr)
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