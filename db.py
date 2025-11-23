from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine, select, BigInteger, Text, TIMESTAMP, func, DateTime, ForeignKey, Numeric, UniqueConstraint, update, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.exc import InvalidRequestError
import logging
from sqlalchemy.ext.mutable import MutableDict ,MutableList
import time
import traceback

database_url = "postgresql+psycopg://koyeb-adm:oqn3FJWkDi0f@ep-red-butterfly-82591662.eu-central-1.pg.koyeb.app/QuestsDB"
Base = declarative_base()
engine = create_engine(database_url, pool_pre_ping = True)
Session = sessionmaker(bind=engine)
session = Session()

class Player(Base):
    __tablename__ = 'players'
    userid = Column(BigInteger, primary_key = True, autoincrement = False)
    points = Column(Integer, default = 0)

class Config(Base):
    __tablename__ = 'config'
    config = Column(Integer, primary_key = True)
    quest_time = Column(Boolean, default = False)
    register_time = Column(Boolean, default = False)
    quest_chat_id = Column(BigInteger, default = 0)
    register_chat_id = Column(BigInteger, default = 0)

Base.metadata.create_all(engine)
def db_critical(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                traceback.print_exc()
                logging.critical(f"Critical Database error: {e}")
                session.rollback()
                break
    return wrapper

@db_critical
def player_exists(userid):
    player = session.get(Player, userid)
    return player is not None

@db_critical
def add_player(userid):
    new_player = Player(userid=userid, points=0)
    session.add(new_player)
    session.commit()

@db_critical
def add_points(userid, points):
    player = session.get(Player, userid)
    if player:
        player.points += points
        session.commit()

@db_critical
def quest_time_enabled():
    config = session.get(Config, 0)
    return config.quest_time

@db_critical
def register_time_enabled():
    config = session.get(Config, 0)
    return config.register_time

@db_critical
def toggle_quest_time():
    config = session.get(Config, 0)
    config.quest_time = not config.quest_time
    session.commit()

@db_critical
def toggle_register_time():
    config = session.get(Config, 0)
    config.register_time = not config.register_time
    session.commit()

@db_critical
def get_register_chat_id():
    config = session.get(Config, 0)
    return config.register_chat_id

@db_critical
def get_quest_chat_id():
    config = session.get(Config, 0)
    return config.quest_chat_id


@db_critical
def get_player_points(userid):
    player = session.get(Player, userid)
    if player:
        return player.points
    return 0