u""" Скрипт - имитация клиента """
import json
import socket
import hashlib

sock = socket.socket()

prints = {
    'clients': {
        'full_name': 'ФИО',
        'phone1': 'основной телефон',
        'phone2': 'второй телефон',
        'email': 'email',
        'password': 'пароль'},

    'objects': {
       'id': 'Id',
       'type': 'Тип объекта',
       'address': 'Адрес',
       'area': 'Площадь',
       'cost': 'Стоимость',
       'status': 'Статус'},

    'searches': {
       'id': 'Id',
       'name': 'Название',
       'date': 'Дата',
       'count': 'Количество'}
}

def start_client():
    u""" Функция запуска клиента
        ничего не принимает и не возвращает """
    # x = sock.connect(('192.168.1.7', 8080))
    x = sock.connect(('127.0.0.1', 8080))

    main_dict = {
        0: ['clients', 'authorization', sign_in, False],  # не нужна авторизация
        1: ['clients', 'add', add_client, False],
        2: ['clients', 'edit', edit_client, True],
        3: ['clients', 'delete', del_client, True],
        4: ['clients', 'get', get_client, True],
        5: ['clients', 'get_objects', get_client_objects, True],
        6: ['clients', 'get_favs', get_client_favs, True],
        7: ['clients', 'get_searches', get_client_searches, True],
        8: ['clients', 'sign_out', sign_out, True]
    }
    while True:
        client_data = {'content': {'data': {}}}

        while True:
            if not is_auth(client_data):
                print('0 - авторизоваться')
                print('1 - зарегистрироваться')
            else:
                # print(client_data)
                print('')
                print('2 - изменить личные данные')
                print('3 - удалить профиль')
                print('4 - посмотреть профиль')
                print('5 - посмотреть объявления')
                print('6 - посмотреть избранное')
                print('7 - посмотреть поиски')
                print('8 - выйти')
            print('100 - закрыть сервер')

            try:
                my_choice = int(input())
                if my_choice == 100:
                    close_server()
                md = main_dict.get(my_choice)
                if md[3] == is_auth(client_data):
                    client_data['endpoint'] = md[0]
                    client_data['action'] = md[1]
                    client_data = md[2](client_data)
                else:
                    print('Введите верное значение!')
                    continue
            except ValueError:
                print('Введите числовое значение!')
                break
            except TypeError:
                print('Введите соответствующую цифру!')
                break
            except Exception as e:
                print(e)


def is_auth(client_data):
    u""" Функция проверки аутентификации пользователя
        принимает словарь с данными клиента, возвращает булево значение """
    if 'token' in client_data['content']:
        return True
    else:
        return False


def send_and_print(client_data, print_func):
    u""" Функция отправки и получения данных от сервера, а также вывода на экран
        принимает словарь с данными клиента и функцию для вывода данных, возвращает словарь данных """
    client_data = send_receive(client_data)

    if client_data['content']['status'] == '200':
        print_func(client_data['content']['data'])
    else:
        print(client_data['content']['message'])
    return client_data


def send_receive(client_data):
    u""" Функция отправки и получения данных от сервера
        принимает словарь с данными клиента, возвращает словарь данных """
    json_str = json.dumps(client_data)
    sock.sendall(bytes(json_str, 'UTF-8'))
    print(client_data)

    client_data = sock.recv(4096).decode()
    client_data = json.loads(client_data)
    return client_data


def print_input(client_data):
    u""" Функция ввода данных от пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    pr = prints[client_data['endpoint']]
    if client_data['action'] == 'authorization':
        pr = list(pr.items())
        pr = dict(pr[-2:])
    for p in pr:
        print('Введите ' + pr[p])
        client_data['content']['data'][p] = input()

    if client_data['endpoint'] == 'clients' \
            and 'password' in client_data['content']['data']:
        ps = client_data['content']['data']['password']
        client_data['content']['data']['password'] = hashlib.sha256(ps.encode()).hexdigest()
    return client_data


def print_output(client_data):
    u""" Функция вывода данных на экран
        принимает словарь с данными клиента, возвращает словарь данных """
    print('')
    if client_data['content']['data']:
        pr = prints[client_data['endpoint']]
        if client_data['action'] == 'get':
            pr = list(pr.items())
            pr = dict(pr[:-1])
        for p in pr:
            print(prints[client_data['endpoint']][p] + ': ' + client_data['content']['data'][p])
    return client_data


def print_fk_output(client_data, action):
    u""" Функция вывода данных внешних ключей на экран
        принимает словарь с данными клиента и перерменную с данными внешнего ключа, возвращает словарь данных """
    if client_data['content']['data']:
        for a in client_data['content']['data'][action]:
            print('')
            for p in prints[action]:
                print(prints[action][p] + ': ' + str(a[p]))
    return client_data

#####################


def sign_in(client_data):
    u""" Функция авторизации пользователя
            принимает словарь с данными клиента, возвращает словарь данных """
    print(client_data)
    client_data = print_input(client_data)
    client_data = send_and_print(client_data,
                                 lambda user: print('Добро пожаловать, ' + user['full_name']))
    print(client_data)
    return client_data


def add_client(client_data):
    u""" Функция регистрации пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    client_data = print_input(client_data)
    client_data = send_and_print(client_data,
                                 lambda user: print('Вы успешно зарегистрировались! Добро пожаловать, ', user['full_name']))
    return client_data


def edit_client(client_data):
    u""" Функция редактирования пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    client_data = print_input(client_data)
    client_data = send_and_print(client_data,
                                 lambda user: print('Данные успешно изменены!'))
    return client_data


def del_client(client_data):
    u""" Функция удаления пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    client_data = send_and_print(client_data,
                                 lambda user: print('Ваш профиль удален!'))
    client_data = {'content': {'data': {}}}
    return client_data


def get_client(client_data):
    u""" Функция получения данных пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    client_data = send_and_print(client_data,
                                 lambda user: print('Ваши данные:'))
    client_data = print_output(client_data)
    return client_data


def get_client_objects(client_data):
    u""" Функция получения данных об объектах пользователя
        принимает словарь с данными клиента, возвращает словарь данных """
    print('')
    client_data = send_and_print(client_data,
                                 lambda user: print('Ваши объявления:'))
    client_data = print_fk_output(client_data, 'objects')
    return client_data


def get_client_favs(client_data):
    u""" Функция получения данных об избранном клиента
        принимает словарь с данными клиента, возвращает словарь данных """
    print('')
    client_data = send_and_print(client_data,
                                 lambda user: print('Ваши избранные:'))
    client_data = print_fk_output(client_data, 'objects')
    return client_data


def get_client_searches(client_data):
    u""" Функция получения данных о сохраненных поисках клиента
        принимает словарь с данными клиента, возвращает словарь данных """
    print('')
    client_data = send_and_print(client_data,
                                 lambda user: print('Ваши поиски:'))
    client_data = print_fk_output(client_data, 'searches')
    return client_data


def sign_out(client_data):
    u""" Функция выхода пользователя из системы
        принимает словарь с данными клиента, возвращает словарь данных """
    client_data = send_and_print(client_data,
                                 lambda user: print('Выход...'))
    return client_data


def close_server():
    u""" Функция закрытия сервера
        ничего не принимает и не возвращает """
    sock.sendall(bytes('close', 'UTF-8'))
    print('Завершение работы...')
    exit()


# start_client()
