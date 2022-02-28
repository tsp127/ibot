from peewee import *

import config

db = SqliteDatabase(config.DATABASE_PATH)

def create_tables():
	"""
	Создать нужные таблицы
	"""
	db.connect()
	db.create_tables([TimeInterval, Users])


class BaseModel(Model):
	class Meta:
		database = db


class Users(BaseModel):

	uid = BigIntegerField(unique=True)


class TimeInterval(BaseModel):
	
	class Meta:
		db_table = 'time_interval'
		
	from_time = DateTimeField()
	before_time = DateTimeField()
	user = ForeignKeyField(Users)
	sended_is = BooleanField(default=False)
