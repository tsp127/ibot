import models
import config

import datetime

from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup


def get_markup(buttons: list):
	""" Получение reply клавиатуры
	"""
	keyboard = []
	for row in buttons:
		row_arr = []
		for button in row:
			row_arr.append(KeyboardButton(button))
		keyboard.append(row_arr)
	return ReplyKeyboardMarkup(keyboard, True)


def get_inline_markup(buttons: list):
	""" Получение inline клавиатуры
	"""
	keyboard = []
	for row in buttons:
		row_arr = []
		for button in row:
			row_arr.append(InlineKeyboardButton(text=button[0], callback_data=button[1]))
		keyboard.append(row_arr)
	return InlineKeyboardMarkup(keyboard)


def check_valid_enter_time(time):
	""" Проверка валидности введеного времени """
	try:
		return datetime.datetime.strptime(time, "%H:%M")
	except Exception:
		return False