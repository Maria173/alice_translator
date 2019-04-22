import requests


def translate_word(text_to_translate, req_lang):
    url = "https://translate.yandex.net/api/v1.5/tr.json/translate"

    params = {
            'key': 'trnsl.1.1.20190412T150802Z.4ea6dee357c34e16.4cb59aa7c9773dc13535380698ec49f46ae4a546',
            'text': text_to_translate,
            'lang': req_lang,
            'format': 'plain'
    }

    try:
        response = requests.get(url, params)
        json = response.json()
        return json['text'][0]
    except Exception as e:
        return e


def what_lang(text_to_know_lang):
    url = "https://translate.yandex.net/api/v1.5/tr.json/detect"

    params = {
            'key': 'trnsl.1.1.20190412T150802Z.4ea6dee357c34e16.4cb59aa7c9773dc13535380698ec49f46ae4a546',
            'text': text_to_know_lang
    }

    try:
        response = requests.get(url, params)
        json = response.json()
        return json['lang']
    except Exception as e:
        return e
