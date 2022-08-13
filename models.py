u""" Модуль со всеми классами """
import binascii
import os
import hashlib
import json
from functools import wraps

import redis
import sqlalchemy
import yaml
from flask import Flask, request

from sqlalchemy import create_engine, Integer, String, \
    Column, Date, ForeignKey, Numeric, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker, scoped_session
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from exceptions import *
import logging.config

with open('settings') as conf:
    config = yaml.safe_load(conf)

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

Base = declarative_base()

logging.config.dictConfig(config['logger'])
logger = logging.getLogger('server')

try:
    # red = redis.Redis(host=config['redis_host'], port=config['redis_port'], db=0)
    engine = create_engine(config['db_connection'])
    # session = Session(bind=engine)
    engine.connect()
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    # red.ping()
except Exception as e:
    print(e)
except redis.ConnectionError as e:
    logger.error('Connection Error!')
    exit()
except sqlalchemy.exc.OperationalError as e:
    logger.error('Connection Error!')
    exit()
# engine = create_engine("sqlite:///data_base.db")
salt = config['salt']


def object_to_dict(obj):
    u""" Функция преобразования объекта класса в словарь
     принимает объект, возвращает словарь """
    dict = {}
    for x in obj.__table__.columns:
        if (isinstance(x.type, Numeric)) and \
                (getattr(obj, x.name) != None) and \
                (x.name != 'latitude' and x.name != 'longitude'):
            dict[x.name] = round(getattr(obj, x.name), 2)
        else:
            dict[x.name] = getattr(obj, x.name)
    return dict


def dict_to_object(obj, dict):
    u""" Функция преобразования словаря с полями в объект класса
     принимает словарь, возвращает объект """
    for x in obj.__table__.columns:
        if x.name in dict:
            setattr(obj, x.name, dict[x.name])
    return obj


def object_exists(p):
    u""" Функция проверки существования объекта
     принимает объект """
    if p is None:
        raise NotFoundError


# def is_login(func):
#     u""" Функция-декоратор проверки аутентификации пользователя
#          принимает необходимую функцию, возвращает функцию, если аутентификация успешна """
#     @wraps(func)
#     def checking(client_data):
#         try:
#             token = 'token_' + client_data['token']
#             id = red.get(token).decode()
#             if red.ttl(name=token) < 30:
#                 red.expire(client_data['token'], 60)
#             return func(client_data, id)
#         except:
#             del client_data['token']
#             client_data['data'] = {}
#             raise UnauthorizedError
#     # print(checking)
#     return checking


#################################################

class People(Base):
    u""" Класс пользователя """
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    phone1 = Column(String(11), nullable=False)
    phone2 = Column(String(11), nullable=True)
    email = Column(String(100), nullable=True)
    is_client = Column(Boolean, nullable=False)
    position = Column(String(100), nullable=True)
    role_id = Column(Integer, nullable=True)
    comment = Column(String(250), nullable=True)
    photo = Column(String(200), nullable=True)
    self_registration = Column(Boolean, nullable=True)
    password = Column(String(200), nullable=False)
    token = Column(String(250), nullable=False)
    emp_id = Column(Integer, nullable=True)
    date_delete = Column(Date(), nullable=True)
    user_objects = relationship("Objects", back_populates="seller")
    client_searches = relationship("Searches", back_populates="client")
    favourite = relationship("Objects", secondary="favourites")

    __table_args__ = (
        Index('token_idx', 'token'),
        Index('delete_person_idx', 'date_delete')
    )

    @app.route('/users/sign_in', methods=['POST'])
    def sign_in():
        u""" Метод для авторизации пользователя
             принимает словарь с данными клиента, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        salted = hashlib.sha256(client_data['data']['password'].encode() + salt.encode()).hexdigest()
        p = session.query(People).filter(People.email == client_data['data']['email'],
                                         People.password == salted,
                                         People.date_delete == None).first()
        object_exists(p)
        # p.token = binascii.hexlify(os.urandom(20)).decode()
        p.token = '123456789'
        client_data['token'] = p.token
        # red.set('token_' + p.token, p.id, ex=60)
        del client_data['data']['password']
        del client_data['data']['email']
        client_data['data']['full_name'] = p.full_name
        return client_data

    @app.route('/users/add', methods=['POST'])
    def add_client():
        u""" Метод для регистрации/добавления клиента
            принимает словарь с данными клиента, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        p = People()
        salted = hashlib.sha256(client_data['data']['password'].encode() + salt.encode()).hexdigest()
        client_data['data']['password'] = salted
        p = People(**client_data['data'])

        p.is_client = True
        p.self_registration = True
        p.token = binascii.hexlify(os.urandom(20)).decode()  # RANDOM

        try:
            session.add(p)
            session.commit()
            client_data['data'] = {}
            # red.set('token_' + p.token, p.id, ex=60)
            client_data['token'] = p.token
            client_data['data']['full_name'] = p.full_name
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/edit', methods=['POST'])
    def edit_client():
        u""" Метод для редактирования данных пользователя
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        p = session.query(People).filter(People.token == client_data['token']).first()
        # p = session.query(People).get(id)
        object_exists(p)
        salted = hashlib.sha256(client_data['data']['password'].encode() + salt.encode()).hexdigest()
        client_data['data']['password'] = salted
        p = dict_to_object(p, client_data['data'])

        try:
            session.add(p)
            session.commit()
            client_data['data'] = {}
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/delete', methods=['POST'])
    def delete_client():
        u""" Метод для удаления пользователя
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        try:
            p = session.query(People).filter(People.token == client_data['token']).first()
            # p = session.query(People).get(id)
            if p is None:
                raise DeletedError
            p.date_delete = datetime.today()
            session.add(p)
            session.commit()
            del client_data['token']
        except DeletedError as e:
            session.rollback()
            client_data['status'] = e.status
            client_data['message'] = e.message
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/get_client', methods=['POST'])
    def get_client():
        u""" Метод для получения данных пользователя
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        try:
            p = session.query(People).filter(People.token == client_data['token']).first()
            # p = session.query(People).get(id)
            object_exists(p)
            client_data['data'] = object_to_dict(p)
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/get_objects', methods=['POST'])
    def get_client_objects():
        u""" Метод для получения данных об объектах пользователя
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        try:
            p = session.query(People).filter(People.token == client_data['token']).first()
            # p = session.query(People).get(id)
            object_exists(p)
            clients_objects = list(filter(lambda x: x.date_delete == None, p.user_objects))
            # fav = p.favourite
            # s = p.client_searches
            objects = []

            for o in clients_objects:
                obj = object_to_dict(o)
                objects.append(obj)

            client_data['data']['objects'] = objects
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/get_favs', methods=['POST'])
    def get_client_favourites():
        u""" Метод для получения данных об избранных клиента
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        try:
            p = session.query(People).filter(People.token == client_data['token']).first()
            # p = session.query(People).get(id)
            object_exists(p)
            c_fav = p.favourite
            objects = []

            for o in c_fav:
                obj = object_to_dict(o)
                objects.append(obj)

            client_data['data']['favourites'] = objects
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    # @is_login
    @app.route('/users/get_searches', methods=['POST'])
    def get_client_searches():
        u""" Метод для получения данных о поисках клиента
             принимает словарь с данными клиента и id, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        try:
            p = session.query(People).filter(People.token == client_data['token']).first()
            # p = session.query(People).get(id)
            object_exists(p)
            clients_searches = p.client_searches
            searches = []

            for o in clients_searches:
                obj = object_to_dict(o)
                searches.append(obj)

            client_data['data']['searches'] = searches
        except:
            session.rollback()
            raise InternalServerError
        return client_data

    @app.route('/users/sign_out', methods=['POST'])
    def sign_out():
        u""" Метод для выхода клиента из системы
             принимает словарь с данными клиента, возвращает преобразованный словарь """

        client_data = json.loads(request.form['json'].replace("'", '"'))
        # red.delete('token_' + json['token'])
        client_data['data'] = {}
        del client_data['token']
        return client_data


class Localities(Base):
    u""" Класс населенного пункта """
    __tablename__ = 'localities'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    show_name = Column(String(100), nullable=False)
    type = Column(Integer, nullable=False)
    distance = Column(Numeric, nullable=True)
    description = Column(String(250), nullable=True)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    photos = Column(String(250), nullable=True)
    date_delete = Column(String(100), nullable=True)

    loc_objects = relationship("Objects", foreign_keys=[id], primaryjoin="Objects.locality_id == Localities.id",
                               back_populates="locality")
    # parent_loc_objects = relationship("Objects", back_populates="parent", lazy='select')


class Objects(Base):
    u""" Класс объекта недвижимости """
    __tablename__ = 'objects'
    id = Column(Integer, primary_key=True)
    type = Column(Integer, nullable=False)
    seller_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    locality_id = Column(Integer, ForeignKey('localities.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('localities.id'), nullable=False)
    distance = Column(Numeric, nullable=True, default=0)
    address = Column(String(200), nullable=False)
    area = Column(Numeric, nullable=False)
    object_area = Column(Numeric, nullable=True)
    other_objects = Column(String(250), nullable=True)
    description = Column(String(250), nullable=True)
    date_update = Column(String(100), nullable=True, default=datetime.today())
    cadast_num = Column(String(20), nullable=True)
    rating = Column(Integer, nullable=True)
    status = Column(Integer, nullable=True)
    posession = Column(String(250), nullable=True)
    purpose = Column(String(250), nullable=True)
    source = Column(String(100), nullable=True)
    link = Column(String(200), nullable=True)
    resp_emp = Column(Integer, nullable=True)
    cost = Column(Numeric, nullable=False)
    comission = Column(Numeric, nullable=False)
    price_conditions = Column(String(250), nullable=True)
    good_price = Column(Boolean, nullable=True, default=False)
    bargain = Column(Boolean, nullable=True, default=False)
    invest_attract = Column(Boolean, nullable=True, default=False)
    latitude = Column(Numeric, nullable=False)
    longitude = Column(Numeric, nullable=False)
    date_delete = Column(String(100), nullable=True)

    seller = relationship("People", back_populates="user_objects")
    locality = relationship("Localities", foreign_keys=[locality_id],
                            primaryjoin="Objects.locality_id == Localities.id")
    parent = relationship("Localities", foreign_keys=[parent_id], primaryjoin="Objects.parent_id == Localities.id")
    # parent = relationship("Localities", foreign_keys='parent_id', back_populates="parent_loc_objects",  lazy='select')


class Searches(Base):
    u""" Класс сохраненного клиентом поиска """
    __tablename__ = 'searches'
    id = Column(Integer, primary_key=True)
    name = Column(String(300), nullable=False)
    query = Column(String(300), nullable=False)
    client_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    date = Column(String(100), nullable=False, default=datetime.today())
    count = Column(Integer, nullable=False, default=0)

    client = relationship("People", back_populates="client_searches")


class Favourites(Base):
    u""" Класс избранного пользователя """
    __tablename__ = 'favourites'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('people.id'), nullable=False)
    object_id = Column(Integer, ForeignKey('objects.id'), nullable=False)
    date_add = Column(String(100), nullable=False, default=datetime.today())

    # client_fav = relationship("People", back_populates="favourite")
    # client_fav = relationship("People", back_populates="favourite")

# Base.metadata.create_all(engine)


app.run(address='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
