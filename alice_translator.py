from random import choice, shuffle
from flask import Flask, request
import logging
import json
from translate import translate_word, what_lang
from dictionary import phrases

from langs import langs

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='alice_translator.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
sessionStorage = {}
help_text = 'Привет! Я могу перевести текст с любого языка на русский язык. Для ' \
            ' этого нужно сказать "Переведи (текст) на (язык)". Я могу сказать на каком языке ' \
            ' написан текст. Просто скажите "На каком языке (текст)" или "Что за язык (текст)". ' \
            ' Если вам скучно, то мы можем сыграть в игру, где я перевожу ваше ' \
            ' слово на случайный язык, а вы пытаетесь отгадать что за язык. ' \
            ' (Для активации игры скажите "Давай сыграем в угадай язык"). ' \
            'Также вы можете проверить свои познания в каком-либо языке. ' \
            '(Для этого скажите "Давай проверим языкознание").'


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
            'game_started1': False,
            'game_started2': False,
            'lang': None
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
            res['response']['text'] = 'Привет, {}! Я могу: 1)перевести текст; ' \
                                      '2)сказать, на каком языке он написан; ' \
                                      '3)поиграть с тобой в языковые игры!'.format(username)
            res['response']['buttons'] = [
                {
                    'title': 'Помощь',
                    'hide': True
                },
                {
                    'title': 'Давай сыграем в угадай язык',
                    'hide': True
                },
                {
                    'title': 'Давай проверим языкознание',
                    'hide': True
                }
            ]

            return

    else:

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
                },
                {
                    'title': 'Давай сыграем в угадай язык',
                    'hide': True
                },
                {
                    'title': 'Давай проверим языкознание',
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
                        },
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]

        elif 'помощь' in f_req:
            res['response']['text'] = help_text
            res['response']['buttons'] = [
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]

        elif 'давай проверим языкознание' in f_req:
            sessionStorage[user_id]['game_started2'] = True
            res['response']['text'] = '{}! Назови язык, знание которого хочешь проверить.'.format(username)
            sessionStorage[user_id]['time'] = 1
            sessionStorage[user_id]['lang'] = False

        elif sessionStorage[user_id]['game_started2'] and (f_req in langs.keys()):
            sessionStorage[user_id]['lang'] = f_req
            res['response']['text'] = 'Продолжаем?'
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]

        elif sessionStorage[user_id]['game_started2'] and (sessionStorage[user_id]['lang'] is False) and (f_req not in langs.keys()):
            res['response']['text'] = 'Извини, но я не знаю такой язык. Попробуй ещё раз!'

        elif sessionStorage[user_id]['game_started2'] and sessionStorage[user_id]['lang'] and f_req in ['нет', 'стоп']:
            sessionStorage[user_id]['lang'] = False
            sessionStorage[user_id]['game_started2'] = False
            res['response']['text'] = 'Нет, так нет!'
            res['response']['buttons'] = [
                        {
                            'title': 'Помощь',
                            'hide': True
                        },
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]

        elif sessionStorage[user_id]['game_started2'] and sessionStorage[user_id]['lang']:
            play_game_knowledge(res, req)

        elif sessionStorage[user_id]['game_started2'] is False and sessionStorage[user_id]['lang'] and f_req in ['да', 'продолжаем']:
            sessionStorage[user_id]['game_started2'] = True
            sessionStorage[user_id]['time'] = 1
            play_game_knowledge(res, req)

        elif sessionStorage[user_id]['game_started2'] is False and sessionStorage[user_id]['lang'] and f_req in ['нет', 'стоп']:
            sessionStorage[user_id]['lang'] = False
            res['response']['text'] = 'Как скажешь!'
            res['response']['buttons'] = [
                        {
                            'title': 'Помощь',
                            'hide': True
                        },
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]

        elif 'давай сыграем в угадай язык' in f_req:
            sessionStorage[user_id]['game_started1'] = True
            res['response']['text'] = '{}! Назови любое слово, а потом попробуй угадать,' \
                                      ' на какой язык я его перевела.'.format(username)
            sessionStorage[user_id]['attempt'] = 1

        elif sessionStorage[user_id]['game_started1']:

            sessionStorage[user_id]['word'] = f_req
            play_game_guess_lang(res, req)

        else:
            res['response']['text'] = 'Я не понимаю! Попробуй ещё раз!'
            res['response']['buttons'] = [
                    {
                        'title': 'Помощь',
                        'hide': True
                    },
                    {
                        'title': 'Давай сыграем в угадай язык',
                        'hide': True
                    },
                    {
                        'title': 'Давай проверим языкознание',
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


def play_game_guess_lang(res, req):
    global tr_lang, tip1, tip2, tip3, tr_word
    user_id = req['session']['user_id']
    attempt = sessionStorage[user_id]['attempt']

    if attempt == 1:
        tr_lang = choice(list(langs.keys()))
        tr_word = translate_word(sessionStorage[user_id]['word'], langs[tr_lang])
        tips = [choice(list(langs.keys())), choice(list(langs.keys())), tr_lang]
        shuffle(tips)
        tip1 = tips[0]
        tip2 = tips[1]
        tip3 = tips[2]
        res['response']['text'] = tr_word
        res['response']['buttons'] = [
                    {
                        'title': tip1,
                        'hide': True
                    },
                    {
                        'title': tip2,
                        'hide': True
                    },
                    {
                        'title': tip3,
                        'hide': True
                    }
                ]
        sessionStorage[user_id]['attempt'] += 1
        return

    elif req['request']['original_utterance'].lower() == tr_lang:
                res['response']['text'] = 'Молодец, {}! Правильно!'.format(username)
                sessionStorage[user_id]['game_started1'] = False
                res['response']['buttons'] = [
                        {
                            'title': 'Помощь',
                            'hide': True
                        },
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]
                return
    else:

            if attempt == 3:
                right_word = translate_word(tr_word,'ru')
                res['response']['text'] = res['response']['text'] = f'Вы пытались. Это {tr_lang}.' \
                                                                    f'А слово переводится так: {right_word}.'
                res['response']['buttons'] = [
                        {
                            'title': 'Помощь',
                            'hide': True
                        },
                        {
                            'title': 'Давай сыграем в угадай язык',
                            'hide': True
                        },
                        {
                            'title': 'Давай проверим языкознание',
                            'hide': True
                        }
                    ]

                sessionStorage[user_id]['game_started1'] = False
                return
            else:
                res['response']['text'] = '{}, попробуй ещё раз!'.format(username)
                res['response']['buttons'] = [
                    {
                        'title': tip1,
                        'hide': True
                    },
                    {
                        'title': tip2,
                        'hide': True
                    },
                    {
                        'title': tip3,
                        'hide': True
                    }
                ]

    sessionStorage[user_id]['attempt'] += 1


def play_game_knowledge(res, req):
    global phrase
    user_id = req['session']['user_id']
    time = sessionStorage[user_id]['time']
    tr_lang = sessionStorage[user_id]['lang']

    if time == 1:
        phrase = choice(phrases)
        tr_text = translate_word(phrase, langs[tr_lang])
        res['response']['text'] = tr_text

    elif time == 2 and req['request']['original_utterance'].lower() == phrase:
            res['response']['text'] = 'Молодец, {}! Правильно! Продолжаем?'.format(username)
            res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]

            sessionStorage[user_id]['game_started2'] = False
            return

    else:

        res['response']['text'] = 'Нет! Это переводится так: {}. Продолжаем?'.format(phrase)
        res['response']['buttons'] = [
                {
                    'title': 'Да',
                    'hide': True
                },
                {
                    'title': 'Нет',
                    'hide': True
                }
            ]
        sessionStorage[user_id]['game_started2'] = False

    sessionStorage[user_id]['time'] += 1


if __name__ == '__main__':
    app.run()
