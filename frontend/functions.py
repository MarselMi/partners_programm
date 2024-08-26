from datetime import datetime, timedelta
import requests
import json
from django.shortcuts import redirect
import re

from variables import domain_api2, domain_api1, tg_debug_key, chat_id

date_for_api2 = re.compile(r'(\d+).(\d+).(\d+)')
date_for_api1 = re.compile(r'(\d+)-(\d+)-(\d+)')


DOMAIN_API = domain_api2
BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BANKS = {
    "PUBLIC JOINT STOCK COMPANY PROMSVYAZBANK": "ПромсвязьБанк",
    "SBERBANK OF RUSSIA": "Сбербанк",
    "SBERBANK of Russia": "Сбербанк",
    "SAVINGS BANK OF THE RUSSIAN FEDERATION (SBERBANK)": "Сбербанк",
    "Sberbank": "Сбербанк",
    "QIWI Bank (JSC)": "Qiwi",
    "QIWI Bank": "Qiwi",
    "RNCB": "РНСБ",
    "Bank Otkritie Financial Corporation": "Открытие",
    "CB OTKRITIE CJSC": "Открытие",
    "TINKOFF BANK": "Тинькофф",
    "JSCB AK BARS": "Ак Барс",
    "CJSC ALFA-BANK": "Альфа-Банк",
    "Alfa-Bank": "Альфа-Банк",
    "JOINT STOCK COMPANY 'ALFA-BANK'": "Альфа-Банк",
    "JOINT STOCK COMPANY ALFA-BANK": "Альфа-Банк",
    "AO RAIFFEISENBANK": "Райффайзенбанк",
    "ZAO RAIFFEISENBANK": "Райффайзенбанк",
    "Raiffeisenbank": "Райффайзенбанк",
    "Belarusbank JSC": "Беларусбанк",
    "JSCB JSCB BINBANK": "БинБанк",
    "Post Bank": "Почта Банк",
    "GAZPROMBANK (JOINT STOCK COMPANY)": "Газпром Банк",
    "GAZPROMBANK OJSC": "Газпром Банк",
    "OJSC RUSSIAN AGRICULTURAL BANK": "Россельхозбанк",
    "JOINT STOCK COMPANY RUSSIAN AGRICULTURAL BANK": "Россельхозбанк",
    "POCHTA BANK": "Почта Банк",
    "YANDEX.MONEY NBCO LLC": "ЮМоney",
    "VTB Bank PJSC": "ВТБ",
    "OJSC BANK URALSIB": "Уралсиб",
    "ASIAN PACIFIC BANK": "Азиатско-Тихоокеанский банк",
    "VTB BANK (PUBLIC JOINT-STOCK COMPANY)": "ВТБ",
    "JSB AVANGARD": "Банк Авангард",
    "PJSC ROSBANK": "РосБанк",
    "SVIAZ-BANK": "Связь-Банк",
    "QIWI BANK (JSC)": "Qiwi",
    "CREDIT UNION PAYMENT CENTER (LIMITED LIABILITY COMPANY)": "РНКО Платежный Центр",
    "COMMERCIAL BANK RENAISSANCE CREDIT (LIMITED LIABILITY COMPANY)": "РНКО Платежный Центр",
    "NOVIKOMBANK": "Новикомбанк",
    "PUBLIC JOINT-STOCK COMPANY BANK OTKRITIE FINANCIAL CORPORATION": "Открытие",
    "PUBLIC JOINT STOCK COMPANY BANK URALSIB ": "УралСиб",
    "URAL BANK FOR RECONSTRUCTION AND DEVELOPMENT": "Уральский банк реконструкции и развития",
    "OZON Bank Limited Liability Company": "ОЗОН Банк",
    "VTB": "ВТБ",
    "CHINA AND SOUTH SEA BANK, LTD.": "China & South Sea Bank",
    "GENBANK": "GenBank",
    "UNICREDIT BANK": "Юникредит банк",
    "VTB BANK OJSC": "ВТБ",
    "Public Joint-Stock Company The Ural Bank for Reconstruction & Development": "УБРР",
    "Joint Stock Company Alfa-Bank": "Альфа-Банк",
    "JSCB MOSCOW INDUSTRIAL BANK": "Московский индустриальный банк",
    "Promsvyazbank": "Промсвязьбанк",
    "OJSC PROMSVYAZBANK": "Промсвязьбанк"
}


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_postback(postbacks_dict):
    '''функция для преобразования event_id у постбеков'''
    for post in postbacks_dict:
        if post.get('event_id'):
            if len(post.get('event_id')) > 2:
                post['event_id'] = post.get('event_id').replace(' ', '').split(',')
            else:
                post['event_id'] = list(post.get('event_id'))


def isInt(dct_str: str):
    dct_str = float(dct_str)
    if dct_str % 1 == 0:
        return int(dct_str)
    else:
        return round(dct_str, 2)


def encode(num, alphabet):
    """Encode a positive number into Base X and return the string.

    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    if num == 0:
        return alphabet[0]
    arr = []
    arr_append = arr.append  # Extract bound-method for faster access.
    _divmod = divmod  # Access to locals is faster.
    base = len(alphabet)
    while num:
        num, rem = _divmod(num, base)
        arr_append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def decode(string, alphabet=BASE62):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for decoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def getting_percent(today, yesterday):
    '''Деление полученных данных, проверка на ноль'''
    if today == 0 and yesterday == 0:
        return 0
    elif today == 0:
        return -100
    elif yesterday == 0:
        return 100
    else:
        return int(today / yesterday * 100 - 100)


def get_percents_list_hour(lst_in):
    '''функция создает список с данными по процентам в соотношении вчера/сегодня'''
    k = 1
    lst_out = []
    for i in lst_in:
        if k <= len(lst_in) - 1:
            res = getting_percent(lst_in[k], i)
            lst_out.append(res)
            k += 1
        else:
            break
    return lst_out


def get_percents_list(lst_in):
    '''функция создает список с данными по процентам в соотношении вчера/сегодня'''
    k = 1
    lst_out = []
    for i in lst_in:
        if k <= len(lst_in) - 1:
            res = getting_percent(i, lst_in[k])
            lst_out.append(res)
            k += 1
        else:
            break
    return lst_out


def convert_calculate(first, second):
    '''Логика для конверта'''
    if int(first) == 0:
        res = 0
    elif int(second) == 0:
        res = first
    else:
        res = int(first) / int(second)
    return int(res)


def general_last_day_stat(result_dict, inner_dict):
    '''Функция для вывода информации статистики по дням'''
    result_dict.setdefault(
        (datetime.today() - timedelta(days=7)).strftime('%d.%m.%Y'), {
            'hosts': 0,
            'registrations': 0,
            'activations': 0,
            'subscribes': 0,
            'unsubscribes': 0,
            'profit': 0,
            'income': 0,
            'rebills': 0,
            'bad_rebills': 0
        }
    )
    for key in inner_dict:
        try:
            result_dict[datetime.strptime(key['day'], '%Y-%m-%d').strftime('%d.%m.%Y')][key['model']] = key['count']
        except KeyError:
            pass
    return result_dict


def general_day_stat(result_dict, inner_dict, daystart=(datetime.today() - timedelta(days=7)), end_day=datetime.today()):
    '''Функция для вывода информации для Главной страницы статистики по дням'''
    for key in range((end_day - daystart).days):
        result_dict.setdefault(
            (end_day - timedelta(days=key)).strftime('%d.%m.%Y'), {
                'hosts': 0,
                'registrations': 0,
                'activations': 0,
                'subscribes': 0,
                'unsubscribes': 0,
                'profit': 0,
                'income': 0,
                'rebills': 0,
                'bad_rebills': 0
            }
        )
    for key in inner_dict:
        try:
            result_dict[datetime.strptime(key['day'], '%Y-%m-%d').strftime('%d.%m.%Y')][key['model']] = key['count']
        except KeyError:
            pass
    return result_dict


def days_general_stat(result_dict, inner_dict, last_day):
    '''Функция для вывода информации статистики по дням'''
    result_dict.setdefault(
        datetime.strptime(last_day, '%Y-%m-%d').strftime('%d.%m.%Y'), {
            'hosts': 0,
            'registrations': 0,
            'activations': 0,
            'subscribes': 0,
            'unsubscribes': 0,
            'profit': 0,
            'income': 0,
            'rebills': 0,
            'bad_rebills': 0
        }
    )
    for key in inner_dict:
        try:
            result_dict[datetime.strptime(key['day'], '%Y-%m-%d').strftime('%d.%m.%Y')][key['model']] = key['count']
        except KeyError:
            pass
    return result_dict


def get_hour_general_stat(inner_hour, hour, date, list_result):
    '''Функция для вывода списка главной статистики по часам'''
    dict_result = dict()
    '''Функция для вывода статичтики по часам'''
    for key in inner_hour:
        if key['model'] == 'activations' and key['day'] == date:
            dict_result.setdefault(key['hour'], key['count'])
    for key in range(hour + 1):
        if dict_result.get(key):
            list_result.append(dict_result[key])
        else:
            list_result.append(0)
    return list_result


def get_filter_dict(result_filter, inner_filter):
    '''Создание словаря для фильтра'''
    for dct_obj in inner_filter:
        if inner_filter[dct_obj][0]:
            result_filter.setdefault(dct_obj, inner_filter[dct_obj][0])
        inner_filter[dct_obj] = inner_filter[dct_obj][0]


def get_filter_dict_other(result_filter, inner_filter):
    '''Создание словаря для фильтра'''
    for dct_obj in inner_filter:
        if inner_filter[dct_obj][0] and dct_obj != 'page':
            result_filter.setdefault(dct_obj, inner_filter[dct_obj][0])
        inner_filter[dct_obj] = inner_filter[dct_obj][0]
    return result_filter


def session_request_subs_offers_balance(request):
    '''Функция для обновления данных при переходе по страничкам для сессии:
     - по подпискам (активные, просроченные, неребильные, отписанные);
     - по офферам;
     - по балансу; '''
    try:
        response_balance = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/balance/').content)
    except:
        response_balance = {
            'paid': 0, 'overdue': 0, 'no_rebill': 0, 'unsubscribes': 0, 'balance': 0
        }
    ''' Список Офферов в сессию '''
    try:
        all_offers_list = json.loads(requests.get(f'{DOMAIN_API}/offers/').content)
        offers_list = []
        '''Добавление приватоного Оффера партнеру'''
        for offer in all_offers_list:
            if (offer['private_partner'] is None) or (offer['private_partner'] == 'None'):
                offer['private_partner'] = []
            else:
                offer['private_partner'] = offer['private_partner'].replace(' ', '').split(',')
            if (offer['type'] == 'PRIVATE') and (str(request.session['id']) in offer['private_partner']):
                offers_list.append(offer)
            elif offer['type'] == 'PUBLIC':
                offers_list.append(offer)
            else:
                pass
    except:
        if request.session.get('offers_list'):
            offers_list = request.session.get('offers_list')
        else:
            offers_list = []

    request.session['paid'] = response_balance.get("paid")
    request.session['overdue'] = response_balance.get("overdue")
    request.session['unrebill'] = response_balance.get("no_rebill")
    request.session['unsubscribes'] = response_balance.get("unsubscribes")
    request.session['offers_list'] = offers_list
    request.session['balance'] = response_balance.get('balance')
    if request.session.get('manager') is None:
        requests.patch(f'{domain_api1}/partners/{request.session["id"]}/', {'last_activity': datetime.now()})
    try:
        request.session['ticket_un_msgs'] = int(json.loads(requests.get(f'{DOMAIN_API}/ticketmessages/{request.session["id"]}/unread/').content).get('count'))
    except:
        request.session['ticket_un_msgs'] = 0


def get_privat_landings(inner_dict, offer_id, user_id):
    result_list = []
    '''Проверка доступных лендов для офферов'''
    for land in inner_dict:
        land['offer_id_id'] = int(land.get('offer_id_id'))
        land['id'] = int(land.get('id'))
        if int(land.get('offer_id_id')) == int(offer_id):
            if land['private_partner']:
                land['private_partner'] = land['private_partner'].replace(' ', '').split(',')
            else:
                land['private_partner'] = []
            if (land.get('type') == 'PRIVATE') and (str(user_id) in land['private_partner']):
                result_list.append(land)
            elif land.get('type') == 'PUBLIC':
                result_list.append(land)
            else:
                pass
    return result_list


def get_privat_landings_api1(inner_dict, offer_id, user_id):
    result_list = []
    '''Проверка доступных лендов для офферов'''
    for land in inner_dict:
        if int(land.get('offer_id')) == int(offer_id):
            if land.get('type') == 'PRIVATE' and int(user_id) in land['private_partner']:
                result_list.append(land)
            elif land.get('type') == 'PUBLIC':
                pass
                result_list.append(land)
            else:
                pass
    return result_list


def get_all_access_land(inner_dict, id_offer_public, user_id):
    result_list = []
    '''Все лендинги для пользователя'''
    for land in inner_dict:
        if land['private_partner']:
            land['private_partner'] = land['private_partner'].replace(' ', '').split(',')
        else:
            land['private_partner'] = []
        land['offer_id_id'] = int(land.get('offer_id_id'))
        land['id'] = int(land.get('id'))
        if int(land.get('offer_id_id')) in id_offer_public:
            if (land.get('type') == 'PRIVATE') and (str(user_id) in land['private_partner']):
                result_list.append(land)
            elif land.get('type') == 'PUBLIC':
                result_list.append(land)
            else:
                pass
    return result_list


def get_all_access_land_api1(inner_dict, id_offer_public, user_id):
    result_list = []

    for land in inner_dict:
        land['offer_id_id'] = land.get('offer_id')
        if land.get('offer_id') in id_offer_public:
            if (land.get('type') == 'PRIVATE') and (int(user_id) in land['private_partner']):
                result_list.append(land)
            elif land.get('type') == 'PUBLIC':
                result_list.append(land)
        else:
            pass
    return result_list


def filter_stream(request, filter_get):
    '''Запрос на фильтр по потокам'''
    if request.session.get(filter_get.get('stream_id')):
        if filter_get.get('stream_id') not in request.session.get('stream_id'):
            filter_srteam_request = requests.post(
                f'https://api2.offering.pro/statistic/{request.session["id"]}/',
                json.dumps({"stat": "Stream"}))
            stream_response = json.loads(filter_srteam_request.content)
            request.session['stream_id'] = {i['name']: i['id'] for i in stream_response}
        else:
            pass
    else:
        filter_srteam_request = requests.post(
            f'https://api2.offering.pro/statistic/{request.session["id"]}/',
            json.dumps({"stat": "Stream"})
        )
        stream_response = json.loads(filter_srteam_request.content)
        request.session['stream_id'] = {i['name']: i['id'] for i in stream_response}


def post_filter(session, filter_req, filter_session):
    '''Запрос на фильтр'''
    filter_request = requests.post( f'{DOMAIN_API}/statistic/{session["id"]}/',
        json.dumps({"stat": filter_req})
    )
    filter_response = json.loads(filter_request.content)
    session[filter_session] = {i['name']: i['id'] for i in filter_response}
    return filter_request


def collapse(request, page_item):
    '''Запрос на открытие и скрытие доп параметров'''
    if request.GET.get('collapse'):
        col = request.session.get(page_item)
        if col == 2:
            request.session[page_item] = 1
            return request.session[page_item]
        else:
            request.session[page_item] = 2
            return request.session[page_item]


def check_and_request_filter(request, filter_dict, filter_element, filter_req):
    '''Для правильной работы фильтров, если в сессии отстутствует данные
    по выбранным фильтрам, выполняется соответствующий запрос'''
    if request.session.get(filter_element):
        if request.session.get(filter_element).get(filter_dict[filter_element]):
            filter_dict[filter_element] = request.session[filter_element].get(filter_dict.get(filter_element))
    else:
        filter_request = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
            json.dumps({"stat": filter_req})
        )
        filter_response = json.loads(filter_request.content)
        request.session[filter_element] = {i['name']: i['id'] for i in filter_response}
        filter_dict[filter_element] = request.session[filter_element].get(filter_dict.get(filter_element))


def check_profile(func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('id') is None:
            return redirect('login')

        if request.session.get('telegram_id') is None:
            request.session['telegram_id'] = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content).get('telegram_id')
        if request.session.get('profile_info') is None:
            request.session['profile_info'] = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)

        if request.session.get('ban_web') and (request.session.get('manager') is None):
            return redirect('ban_web')
        elif request.session.get('user') is None:
            return redirect('login')
        elif (request.session.get('telegram_id') is None or request.session.get('telegram_id') == 'None' or request.session.get('telegram_id') == 'null') and (request.session.get('manager') is None):
            return redirect('lockpage')
        else:
            return func(request, *args, **kwargs)
    return wrapper


def set_page(request_dict):
    if 'page' in request_dict:
        page = int(request_dict['page'])
    else:
        page = 1
    return page


def set_offset(page, limit):
    if page == 1:
        return 0
    elif page == 2:
        return limit
    else:
        return limit * (page - 1)


def auth_block(func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('id') is None:
            return redirect('login')
        if request.session.get('ban_web') and (request.session.get('manager') is None):
            return redirect('ban_web')
        elif request.session.get('user') is None:
            return redirect('login')
        else:
            return func(request)
    return wrapper


def get_error(func):
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except BaseException:
            from ipware import get_client_ip
            user_ip = get_client_ip(request)
            if user_ip[0] == '127.0.0.1':
                return func(request, *args, **kwargs)
            import traceback
            import telepot
            bot = telepot.Bot(tg_debug_key)
            bot.sendMessage(chat_id, text=f'Ошибка в партнерке\n: Партнер - {request.session["id"]}', parse_mode='HTML')
            bot.sendMessage(chat_id, text=traceback.format_exc(), parse_mode='HTML')
            return func(request, *args, **kwargs)
    return wrapper


def check_payout_limit(summ, limit, partner, comission, requisites, fix, selected_requisites):
    if summ > limit:
        check = 2
        loop = True
        while loop:
            if summ / check < limit:
                sum_part = round(float(summ / check), 2)
                for i in range(check):
                    transaction_req = requests.post(f'{DOMAIN_API}/transactions/',
                        json.dumps({'sum': 0 - sum_part, 'partner_id': partner, 'direction': 2}))

                    transaction_info = json.loads(transaction_req.content)
                    transaction_id = transaction_info.get('id')

                    try:
                        requests.post(f'{DOMAIN_API}/payouts/',
                                      json.dumps({
                                          'sum': sum_part, 'partner_id': partner,
                                          "selected_requisites": selected_requisites,
                                          'comission': comission, 'status': 'IN_PROCESS',
                                          'requisites': requisites,
                                          "fix": fix, "type": "PAYMENT_REQUEST",
                                          "transaction_id": transaction_id
                                      }))
                    except:
                        summ = 0
                        requests.patch(f'{DOMAIN_API}/payouts/{transaction_id}/',
                                       json.dumps({'sum': summ, 'partner_id': partner,
                                        'selected_requisites': selected_requisites,
                                        'comission': comission, 'status': 'IN_PROCESS',
                                        'requisites': requisites,
                                        'fix': fix, 'type': 'PAYMENT_REQUEST'}))
                loop = False
            else:
                check += 1
    else:
        transaction_req = requests.post(f'{DOMAIN_API}/transactions/',
            json.dumps({'sum': 0 - summ, 'partner_id': partner, 'direction': 2}))

        transaction_info = json.loads(transaction_req.content)
        transaction_id = transaction_info.get('id')

        try:
            requests.post(f'{DOMAIN_API}/payouts/',
                          json.dumps({
                              'sum': summ, 'partner_id': partner,
                              "selected_requisites": selected_requisites,
                              'comission': comission, 'status': 'IN_PROCESS',
                              'requisites': requisites,
                              "fix": fix, "type": "PAYMENT_REQUEST",
                              "transaction_id": transaction_id
                          }))
        except:
            sum_pay = 0
            requests.patch(f'{DOMAIN_API}/payouts/{transaction_id}/',
                           json.dumps({'sum': sum_pay, 'partner_id': partner,
                            'selected_requisites': selected_requisites,
                            'comission': comission, 'status': 'IN_PROCESS',
                            'requisites': requisites,
                            'fix': fix, 'type': 'PAYMENT_REQUEST'}))


def session_none(func):
    def wrapper(request, *args, **kwargs):
        request.session['user'] = None
        request.session['id'] = None
        if request.session.get('ban_web'):
            request.session['ban_web'] = None
        if request.session.get('manager'):
            request.session['manager'] = None
        if request.session.get('contest'):
            request.session['contest'] = None
        if request.session.get('telegram_id'):
            request.session['telegram_id'] = None
        if request.session.get('profile_info'):
            request.session['profile_info'] = None
        if request.session.get('stream_id'):
            request.session['stream_id'] = None
        return redirect('login')
    return wrapper


def rebill_calculate(data: dict) -> None:
    '''Функция для определения даты след ребилла'''
    if data.get('unsub'):
        data['next_rebill'] = None
    else:
        data['next_rebill'] = str(
            datetime.strptime(
                data.get('subscribe_date'),
                '%Y-%m-%d %H:%M:%S.%f'
            ) + timedelta(days=int(data.get('freeday')))
        )
        if data.get('pay_date'):
            if datetime.strptime(data.get('pay_date'), '%Y-%m-%d %H:%M:%S.%f') > datetime.now():
                data['next_rebill'] = data.get('pay_date')
        if data.get('try_date'):
            data['next_rebill'] = str(
                datetime.strptime(
                    data.get('try_date'),
                    '%Y-%m-%d %H:%M:%S.%f'
                ) + timedelta(days=int(data.get('period')))
            )
            if data.get('try_interval_days'):
                data['next_rebill'] = str(
                    datetime.strptime(
                        data.get('try_date'),
                        '%Y-%m-%d %H:%M:%S.%f'
                    ) + timedelta(days=int(data.get('try_interval_days')))
                )


def rebill_calculate_api1(data: dict) -> None:
    '''Функция для определения даты след ребилла'''
    if data.get('unsub'):
        data['next_rebill'] = None
    else:
        data['next_rebill'] = str(
            datetime.strptime(
                data.get('subscribe_date'),
                '%Y-%m-%dT%H:%M:%S.%f'
            ) + timedelta(days=int(data.get('freeday')))
        )
        if data.get('pay_date'):
            if datetime.strptime(data.get('pay_date'), '%Y-%m-%dT%H:%M:%S.%f') > datetime.now():
                data['next_rebill'] = data.get('pay_date')
        if data.get('try_date'):
            if len(data.get('try_date')) > 20:
                concat = ''
            else:
                concat = '.000000'
            data['next_rebill'] = str(
                datetime.strptime(
                    data.get('try_date')+concat,
                    '%Y-%m-%dT%H:%M:%S.%f'
                ) + timedelta(days=int(data.get('period')))
            )
            if data.get('try_interval_days'):
                data['next_rebill'] = str(
                    datetime.strptime(
                        data.get('try_date')+concat,
                        '%Y-%m-%dT%H:%M:%S.%f'
                    ) + timedelta(days=int(data.get('try_interval_days')))
                )
