

import threading
import telegram
from telegram import ParseMode

from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton

from telegram.ext import Updater
from telegram.ext import Filters
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import CallbackQueryHandler

import util

import config

import models

import time
import datetime

SESSION = {}

bot = telegram.Bot(config.BOT_TOKEN)


def clean_user_session(uid):
	"""
	Очистить все действия пользователя
	"""

	if uid in SESSION:
		del SESSION[uid]
	pass


def start_handler(update, context):
	""" Обработка команды | /start
	"""
	uid = update.message.from_user.id

	clean_user_session(uid)

	if not models.Users.select().where(models.Users.uid == uid):
		models.Users.create(
			uid=uid,
		).save()

	text = "Добро пожаловать! \n\nВыберите нужное действие на клавиатуре снизу"
	markup = util.get_markup(config.main_markup)
	return update.message.reply_text(text, reply_markup=markup)


def help_handler(update, context):
	""" Обработка команды | /help
	"""
	uid = update.message.from_user.id

	clean_user_session(uid)

	if not models.Users.select().where(models.Users.uid == uid):
		models.Users.create(
			uid=uid,
		).save()

	text = "Для поддержания здоровья глаз желательно добавить в свой рацион: морковь, чернику, шпинат броколи и т.п. (больше информации на сайте https://stolichki.ru/news/32)"
	markup = util.get_markup(config.main_markup)
	return update.message.reply_text(text, reply_markup=markup)



def text_handler(update, context):
	""" Обработка входяших соообщений пользователя
	"""
	uid = update.message.from_user.id
	
	# Проверка регистрации пользователя
	user_db = models.Users.select().where(models.Users.uid == uid)
	if not user_db:
		text = "Для начала работы нужно зарегистрироваться в боте. /start"
		markup = ReplyKeyboardRemove()
		return update.message.reply_text(text, reply_markup=markup)

	user_obj = user_db.get()

	# Обработка сессии пользователя
	if uid in SESSION:
		# Обработка ввода времени "ОТ"
		if 'from_time' not in SESSION[uid]:
			# Проверка валидности даты
			from_time_obj = util.check_valid_enter_time(update.message.text)
			if not from_time_obj:
				text = 'Некорректно введено значение. Введите в формате: ЧЧ:ММ'
				return update.message.reply_text(text)
			SESSION[uid]['from_time'] = from_time_obj
			text = 'Принято\nВведите время конца работы в формате ЧЧ:ММ'
			return update.message.reply_text(text)

		# Обработка времени "ДО"
		if 'before_time' not in SESSION[uid]:
			# Проверка валидности даты
			before_time_obj = util.check_valid_enter_time(update.message.text)
			if not before_time_obj:
				text = 'Некорректно введено значение. Введите в формате: ЧЧ:ММ'
				return update.message.reply_text(text)
			SESSION[uid]['before_time'] = before_time_obj
			# Сохранить в БД
			if not models.TimeInterval.select().where(models.TimeInterval.user == user_obj):
				models.TimeInterval.create(
					from_time = SESSION[uid]['from_time'],
					before_time = SESSION[uid]['before_time'],
					user = user_obj
				).save()
			else:
				interval_obj = models.TimeInterval.get(models.TimeInterval.user == user_obj)
				interval_obj.from_time = SESSION[uid]['from_time']
				interval_obj.before_time = SESSION[uid]['before_time']
				interval_obj.save()			
			text = f'Время успешно сохранено!\n\nНе забываете следить за своим зрением'
			del SESSION[uid]
			return update.message.reply_text(text, reply_markup=util.get_markup(config.main_markup))

	# Обработка главного меню	
	if update.message.text == 'Изменить время работы':
		SESSION[uid] = {}
		text = 'Введите время начала работы в формате: ЧЧ:ММ\n\nПример: 09:30, 10:05'
		markup = util.get_markup([['Отмена']])
		return update.message.reply_text(text, reply_markup=markup)

	# В случае ввода неизвестной команды
	text = 'Неизвестная команда'
	markup = util.get_markup(config.main_markup)
	return update.message.reply_text(
		text, reply_markup=markup)


def scheduling():
	""" Обработка отправки сообщения """
	
	def send_message_two_hours():
		for interval_obj in models.TimeInterval.select():
			dt_now = datetime.datetime.now()
			one_date = datetime.datetime(
				dt_now.year, dt_now.month, dt_now.day,
				interval_obj.from_time.hour, interval_obj.from_time.minute
				)
			two_date = datetime.datetime(
				dt_now.year, dt_now.month, dt_now.day,
				interval_obj.before_time.hour, interval_obj.before_time.minute
				)
			if interval_obj.before_time < interval_obj.from_time:
				dt_now = datetime.datetime.now() + datetime.timedelta(days=1)
				two_date = datetime.datetime(
				dt_now.year, dt_now.month, dt_now.day,
				interval_obj.before_time.hour, interval_obj.before_time.minute
				)

			send = False
			time_sended = 0
			while True:
				time_sended += 60
				before_time = one_date + datetime.timedelta(minutes=time_sended)
				# Проверка выхода даты за диапазоны второй даты
				if before_time > two_date:
					break

				if (dt_now.hour == before_time.hour and dt_now.minute == before_time.minute):
					send = True
					break

			if send:
				if interval_obj.sended_is:
					continue
				try:
					bot.send_message(interval_obj.user.uid, config.DEFAULT_MESSAGE)
				except Exception as e:
					print(e)
				interval_obj.sended_is = True
				interval_obj.save()
			else:
				interval_obj.sended_is = False
				interval_obj.save()

	while True:
		try:
			send_message_two_hours()
		except Exception as e:
			print(e)
		
		time.sleep(2)


def main():

	threading.Thread(target=scheduling).start()

	models.create_tables()
	updater = Updater(config.BOT_TOKEN, use_context=True)
	print(
		'Ссылка на бота: https://t.me/{!s}'.format(updater.bot.get_me().username)
		)
	updater.dispatcher.add_handler(CommandHandler('start', start_handler))
	updater.dispatcher.add_handler(CommandHandler('help', help_handler))
	updater.dispatcher.add_handler(MessageHandler(Filters.text, text_handler))

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
