from flask import Flask, request
import logging
import json
from translate import translate_word, what_lang

from langs import langs

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, filename='alice_translator.log',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')


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

    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу перевести текст(переведи(те) ...) ' \
                                  'или сказать, на каком языке он написан(на каком языке ...)!'

        # ЗДЕСЬ КНОПКИ: ПЕРЕВДИ и ЧТО ЗА ЯЗЫК

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

    else:
        res['response']['text'] = 'Я не понимаю! Попробуй ещё раз!'


if __name__ == '__main__':
    app.run()
