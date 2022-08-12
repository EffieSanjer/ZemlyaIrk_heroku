u""" Скрипт - имитация сервера """
import socket
import json
from threading import Thread
from time import sleep
from models import *
import os, sys
# import msvcrt


# def lock():
#     try:
#         fd = os.open(r'server.py', os.O_WRONLY | os.O_EXCL)
#         c = msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
#     except IOError as e:
#         print(e)

# lock()


# if os.path.isfile(pidfile):  # if file exists
#     pid = open(pidfile, 'r').read()
#     # if check_pid(int(pid)):
#     print("%s already exists!" % pidfile)
#     sleep(5)
#     exit()
# else:
#     pid = str(os.getpid())
#     new_file = open(pidfile, 'w')
#     new_file.write(pid)
#     new_file.close()


def start_server(conn, addr):
    u""" Функция запуска сервера
     ничего не принимает и не возвращает """


    ################################

    main_dict = {
        'authorization': People.sign_in,
        'add': People.add_client,
        'edit': People.edit_client,
        'delete': People.delete_client,
        'get': People.get_client,
        'get_objects': People.get_client_objects,
        'get_favs': People.get_client_favourites,
        'get_searches': People.get_client_searches,
        'sign_out': People.sign_out,
    }

    while True:
        logger.info('Connected:' + str(addr))
        while True:
            try:
                client_data = conn.recv(4096)
                client_data = client_data.decode()
                if client_data == 'close':
                    # os.unlink(pidfile)
                    conn.close()
                    return True
                client_data = json.loads(client_data)
            except:
                logger.error('Receiving Error!')

            if not client_data:
                logger.info('Disconnected:' + str(addr))
                exit()

            try:
                act = client_data['action']
                content = client_data['content']
                print(client_data)
                client_data['content'] = main_dict.get(act)(content)
                content['status'] = '200'
                content['message'] = ''
            except NotFoundError as e:
                content['status'] = e.status
                content['message'] = e.message
                logger.warning('Not Found!')
            except InternalServerError as e:
                content['status'] = e.status
                content['message'] = e.message
            except UnauthorizedError as e:
                content['status'] = e.status
                content['message'] = e.message
                logger.error('Unauthorized Error!')
            except Exception as e:
                print(e)

            logger.info(act + ' - ' + client_data['content']['status'])

            try:
                conn.sendall(bytes(json.dumps(client_data, ensure_ascii=False, default=str), 'UTF-8'))
            except:
                logger.error('Sending Error!')


def server_threading():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((config['address'], config['port']))
        sock.listen()
        logger.info('Server is running')
    except:
        print('Port is occupied')
        sock.settimeout(5)

    while True:
        conn, addr = sock.accept()
        thread = Thread(target=start_server, args=(conn, addr))
        thread.start()
        logger.info('Server is running in thread ' + thread.name)


# start_server()
# server_threading()