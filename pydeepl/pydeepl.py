from http import cookiejar
import logging
import requests


class BlockAll(cookiejar.CookiePolicy):
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


logger = logging.getLogger()

BASE_URL = 'https://www2.deepl.com/jsonrpc'

LANGUAGES = {
    'auto': 'Auto',
    'DE': 'German',
    'EN': 'English',
    'FR': 'French',
    'ES': 'Spanish',
    'IT': 'Italian',
    'NL': 'Dutch',
    'PL': 'Polish'
}

JSONRPC_VERSION = '2.0'


class SplittingError(Exception):
    def __init__(self, message):
        super(SplittingError, self).__init__(message)


def split_sentences(text, proxies, lang='auto', json=False):
    if text is None:
        raise SplittingError('Text can\'t be be None.')
    if lang not in LANGUAGES.keys():
        raise SplittingError('Language {} not available.'.format(lang))

    parameters = {
        'jsonrpc': JSONRPC_VERSION,
        'method': 'LMT_split_into_sentences',
        'params': {
            'texts': [
                text
            ],
            'lang': {
                'lang_user_selected': lang
            },
        },
    }
    s = requests.Session()
    s.cookies.set_policy(BlockAll())
    response = s.post(BASE_URL, json=parameters, proxies=proxies).json()

    if 'result' not in response:
        raise SplittingError('DeepL call resulted in a unknown result.')

    splitted_texts = response['result']['splitted_texts']

    if len(splitted_texts) == 0:
        raise SplittingError('Text could not be splitted.')

    if json:
        return response
    return splitted_texts[0]


class TranslationError(Exception):
    def __init__(self, message):
        super(TranslationError, self).__init__(message)


def translate(text, to_lang, proxies, from_lang='auto', json=False):
    if text is None:
        raise TranslationError('Text can\'t be None.')
    if len(text) > 5000:
        raise TranslationError('Text too long (limited to 5000 characters).')
    if to_lang not in LANGUAGES.keys():
        raise TranslationError('Language {} not available.'.format(to_lang))
    if from_lang is not None and from_lang not in LANGUAGES.keys():
        raise TranslationError('Language {} not available.'.format(from_lang))

    parameters = {
        'jsonrpc': JSONRPC_VERSION,
        'method': 'LMT_handle_jobs',
        'params': {
            'jobs': [
                {
                    'kind':'default',
                    'raw_en_sentence': text
                }
            ],
            'lang': {
                'user_preferred_langs': [
                    from_lang,
                    to_lang
                ],
                'source_lang_user_selected': from_lang,
                'target_lang': to_lang
            },
        },
    }

    s = requests.Session()
    s.cookies.set_policy(BlockAll())

    response = s.post(BASE_URL, json=parameters, proxies=proxies).json()

    if 'result' not in response:
        logger.error('DeepL call resulted in a unknown result.' + repr(response))
        raise TranslationError('DeepL call resulted in a unknown result.')

    translations = response['result']['translations']

    if len(translations) == 0 \
            or translations[0]['beams'] is None \
            or translations[0]['beams'][0]['postprocessed_sentence'] is None:
        raise TranslationError('No translations found.')

    if json:
        return response
    return translations[0]['beams'][0]['postprocessed_sentence']
