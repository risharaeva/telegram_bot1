import random
import telebot
import openai
from bs4 import BeautifulSoup
import requests
import logging
from telebot import types
from constants import TELEGRAM_TOKEN, OPENAI_TOKEN

# Логирование
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

# OpenAI API ключ и ID организации
openai.api_key = OPENAI_TOKEN
openai.organization = "ORG_TOKEN"

def call_openai_api(prompt, openai_api_key):
    openai.api_key = openai_api_key
    try:
        logging.info(f"Sending request to OpenAI with prompt: {prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500  # Adjust as needed
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"OpenAI API Error: {e}")
        return f"Ошибка OpenAI: {str(e)}"

def run_whatstheholiday_bot(telegram_token: str, openai_token: str) -> None:
    bot = telebot.TeleBot(telegram_token, parse_mode=None)

    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        if message.text == "/start":
            keyboard = types.InlineKeyboardMarkup()
            key_1 = types.InlineKeyboardButton(text='Хочу узнать какой праздник сегодня', callback_data='holiday_list')
            keyboard.add(key_1)
            key_2 = types.InlineKeyboardButton(text='Расскажи мне о празднике', callback_data='about_holiday')
            keyboard.add(key_2)
            key_3 = types.InlineKeyboardButton(text='Мне скучно, давай придумаем новый праздник!', callback_data='new_holiday')
            keyboard.add(key_3)
            bot.send_message(message.chat.id, "Привет! Я знаю все обо всех праздниках. Даже о тех, которых не существует. Иногда даже придумываю новые от скуки.", reply_markup=keyboard)
        elif message.text == "":
            bot.send_message(message.chat.id, "Прием-прием, попробуй еще раз. Отправь мне /start")
        else:
            bot.send_message(message.chat.id, "Кажется произошла затупка 😲 Отправь мне /start и попробуем еще раз")

    @bot.callback_query_handler(func=lambda call: call.data == 'holiday_list')
    def holiday_list_handler(call):
        response = requests.get("https://celebratoday.com/ru/today").text
        soup = BeautifulSoup(response, 'lxml')
        blocks = soup.find('ul', class_='list-inside')
        li_elements = blocks.find_all('li')

        holiday_names = "\n".join([f"🎉 {li.text.strip()}" for li in li_elements])
        bot.send_message(call.message.chat.id, f'Сегодня день, богатый на праздники, ты только посмотри!\n{holiday_names}')

        keyboard = types.InlineKeyboardMarkup()
        key_2 = types.InlineKeyboardButton(text='Расскажи мне о празднике', callback_data='about_holiday')
        keyboard.add(key_2)
        key_3 = types.InlineKeyboardButton(text='Скучно! Давай придумаем новый праздник!', callback_data='new_holiday')
        keyboard.add(key_3)
        bot.send_message(call.message.chat.id, "Хочешь о них что-то узнать?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == 'new_holiday')
    def new_holiday_handler(call):
        words = ["День", "Международный день", "Фестиваль", "Праздник", "Всемирный день"]
        phrases = ["желтых тапочек", "кулебяки", "любви ходить в гости", "наоборот", "пустых баночек из-под кофе", "кисленькой жвачки", "Египетской силы", "селедки с молоком", "кучерявого чубчика", "копченых мокасин"]

        random_words = random.sample(words, 1)
        random_phrase = random.choice(phrases)
        new_holiday1 = " ".join(random_words) + " " + random_phrase

        bot.send_message(call.message.chat.id, f"\n {new_holiday1} \n")

        keyboard = types.InlineKeyboardMarkup()
        key_1 = types.InlineKeyboardButton(text='А что сегодня празднуют?', callback_data='holiday_list')
        keyboard.add(key_1)
        key_2 = types.InlineKeyboardButton(text='Расскажи мне о празднике?', callback_data='about_holiday')
        keyboard.add(key_2)
        key_3 = types.InlineKeyboardButton(text='Прикольно! Давай придумаем еще праздник!', callback_data='new_holiday')
        keyboard.add(key_3)
        bot.send_message(call.message.chat.id, "Ну как тебе новый праздник?", reply_markup=keyboard)

    @bot.callback_query_handler(func=lambda call: call.data == 'about_holiday')
    def about_holiday_handler(call):
        def generate_holiday(message):
            try:
                bot.send_message(message.chat.id, "Напиши название праздника, не важно, настоящего или выдуманного:")
                bot.register_next_step_handler(message, wait_for_holiday_name)
            except Exception as e:
                bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

        bot.send_message(call.message.chat.id, "Напиши название праздника, не важно, настоящего или выдуманного:")
        generate_holiday(call.message)

    def wait_for_holiday_name(message):
        try:
            prompt = 'I will give you the name of the holiday, in Russian or another language, and if this holiday exists, you will briefly talk about this holiday in Russian. If there is no such holiday, in the context of the holiday you come up with a funny, sometimes absurd story in Russian about the appearance of the holiday, as well as traditions of how it is celebrated.  Tell us about the holiday: ' + message.text
            logging.info(f"Generated prompt: {prompt}")
            response = call_openai_api(prompt, openai_token)
            bot.send_message(message.chat.id, "Секундочку, сейчас все расскажу...")

            # Send the response from OpenAI
            bot.send_message(message.chat.id, response)

            # Adding options to ask about another holiday or go back to the main menu
            keyboard = types.InlineKeyboardMarkup()
            key_1 = types.InlineKeyboardButton(text='Спросить про другой праздник', callback_data='about_holiday')
            keyboard.add(key_1)
            key_2 = types.InlineKeyboardButton(text='Вернуться к началу', callback_data='go_to_main_menu')
            keyboard.add(key_2)
            bot.send_message(message.chat.id, "Что бы вы хотели сделать дальше?", reply_markup=keyboard)

        except Exception as e:
            logging.error(f"Exception in wait_for_holiday_name: {e}")
            bot.send_message(message.chat.id, f"Ошибка: {str(e)}")

    @bot.callback_query_handler(func=lambda call: call.data == 'go_to_main_menu')
    def go_to_main_menu_handler(call):
        get_text_messages(call.message)

    bot.infinity_polling()

if __name__ == '__main__':
    run_whatstheholiday_bot(TELEGRAM_TOKEN, OPENAI_TOKEN)
