from random import choice
from flask import Flask, request
import logging
import json
from translate import translate_word, what_lang

from langs import langs

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='alice_translator.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
sessionStorage = {}
help_text = 'Привет! Я могу перевести текст с любого языка на русский язык. Для' \
            ' этого нужно сказать "Переведи "текст" на "язык"". Я могу сказать на каком языке' \
            ' написан текст. Просто скажите "на каком языке..." или "что за язык...".' \
            ' Если вам скучно, то мы можем сыграть в игру, где я перевожу ваше ' \
            ' слово на случайный язык, а вы пытаетесь отгадать что за язык.' \
            ' Для активации игры скажите "Давай сыграем в угадывание".'  # Надо будет придумать норм название


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(response, request.json)

    logging.info('Request: %r', response)

    return json.dumps(response)


def handle_dialog(res, req):
    user_id = req['session']['user_id']
    global username
    if req['session']['new']:
        res['response']['text'] = 'Привет! Назови своё имя!'
        sessionStorage[user_id] = {
            'first_name': None,
            'game_started': False
        }

        return
    if sessionStorage[user_id]['first_name'] is None:
        first_name = get_first_name(req)
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
            return
        else:
            sessionStorage[user_id]['first_name'] = first_name
            username = sessionStorage[user_id]['first_name'].capitalize()
            res['response']['text'] = 'Привет, {}! Я могу перевести текст(переведи(те) ...) ' \
                                  'или сказать, на каком языке он написан(на каком языке ...)!'.format(username)
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]

            return

    f_req = req['request']['original_utterance'].lower()

    if 'переведи' in f_req or 'переведите' in f_req:
        words = f_req.split()

        if 'привет' in words[0]:
            del words[0]

        if words[-1] == 'язык':
            text_lang = words[-2]               # нужный язык на русском языке
            text_to_translate = ''
            for i in range(1, len(words) - 3):
                new = words[i] + ' '
                text_to_translate += new        # текст для перевода
        else:
            text_lang = words[-1]
            text_to_translate = ''
            for i in range(1, len(words) - 2):
                new = words[i] + ' '
                text_to_translate += new

        req_lang = langs[text_lang]             # нужный язык в аббревиатуре
        res['response']['text'] = translate_word(text_to_translate, req_lang).capitalize()
        res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]

    elif 'на каком языке' in f_req or 'что за язык' in f_req:
        words = f_req.split()

        if 'привет' in words[0]:
            del words[0]

        text_to_know_lang = ''
        for i in range(3, len(words)):
            new = words[i] + ' '
            text_to_know_lang += new            # текст для определения языка

        abb_lang = what_lang(text_to_know_lang)
        for key, value in langs.items():        # ищем нуюную аббревиатуру в словаре
            if value == abb_lang:
                res['response']['text'] = key.title()
                res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]

    elif 'помощь' in f_req:
        res['response']['text'] = help_text

    elif 'давай сыграем в угадывание' in f_req:
        sessionStorage[user_id]['game_started'] = True
        res['response']['text'] = '{}! Назови любое слово, а потом попробуй угадать' \
                                  ' на какой язык я его перевела.'.format(username)
        sessionStorage[user_id]['attempt'] = 1
    elif sessionStorage[user_id]['game_started']:

        sessionStorage[user_id]['word'] = f_req
        play_game(res, req)

    else:
        res['response']['text'] = 'Я не понимаю! Попробуй ещё раз!'
        res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                }
            ]


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name', то возвращаем её значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)



def play_game(res, req):
    global tr_lang
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']

    if attempt == 1:
        tr_lang = ''
        tr_word = translate_word(sessionStorage[user_id]['word'], choice(list(langs.values())))
        abb_lang = what_lang(tr_word)
        for key, value in langs.items():        # ищем нуюную аббревиатуру в словаре
            if value == abb_lang:
                tr_lang = key
        res['response']['text'] = tr_word



    elif req['request']['original_utterance'].lower() == tr_lang:
                res['response']['text'] = 'Молодец, {}! Правильно!'.format(username)
                sessionStorage[user_id]['game_started'] = False
                return
    else:
            if attempt == 4:
                res['response']['text'] = res['response']['text'] = f'Вы пытались. Это {tr_lang}. Сыграем ещё?'
                sessionStorage[user_id]['game_started'] = False
                return
            else:
                 res['response']['text'] = '{}, попробуй ещё раз!'.format(username)
    sessionStorage[user_id]['attempt'] += 1





if __name__ == '__main__':
    app.run()
