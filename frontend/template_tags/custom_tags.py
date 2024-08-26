from django.template.defaulttags import register
import datetime as dt
from datetime import datetime
import re


@register.filter
def offer_not_id(offer):
    return f'{offer[2:]}'


@register.filter
def simple_numbers(numb):
    if numb:
        return '{0:,}'.format(int(numb)).replace(',', ' ')
    else:
        return 0


@register.filter
def card_check(obj):
    if obj.lower().find('карта') > -1:
        return True
    else:
        return False


@register.filter
def card_numb(obj):
    return re.sub('([^ ]{4})', r'\1 ', str(obj))


@register.filter
def time_from_int(time_format):
    if '1970' in datetime.fromtimestamp(time_format).strftime('%d.%m.%Y в %H:%M:%S'):
        return '&ndash;'
    else:
        return datetime.fromtimestamp(time_format).strftime('%d.%m.%Y в %H:%M:%S')


@register.filter
def post_event(event):
    if event == 'register':
        return 'Регистрация'
    if event == 'activate':
        return 'Активация'
    if event == 'subscribe':
        return 'Подписка'
    if event == 'rebill':
        return 'Ребилл'
    if event == 'unsub':
        return 'Отписка'


@register.filter
def truncate(_list, ind):
    return _list[ind]


@register.filter
def act_format(activations):
    if activations:
        return '{0:,}'.format(int(activations)).replace(',', '&nbsp;')
    else:
        return 0


@register.filter
def numb_format(balance):
    try:
        if round(balance, 2) % 1 == 0:
            return '{0:,}'.format(int(balance)).replace(',', ' ')
        else:
            balance = round(balance, 2)
            return '{0:,}'.format(balance).replace(',', ' ').replace('.', ',')
    except TypeError:
        return 0


@register.filter
def date_change(create_date):
    return dt.datetime.fromisoformat(create_date).strftime('%d.%m.%Y в %H:%M:%S')


@register.filter
def postback_event(event_id):
    if 1 == event_id or '1' == event_id:
        return 'Регистрация'
    if 2 == event_id or '2' == event_id:
        return 'Активация'
    if 3 == event_id or '3' == event_id:
        return 'Подписка'
    if 4 == event_id or '4' == event_id:
        return 'Ребилл'
    if 5 == event_id or '5' == event_id:
        return 'Отписка'


@register.filter
def response_status(str):
    return str[:3]


@register.filter
def color_status(str_obj):
    return str_obj[0]


@register.filter
def response_data(str):
    return str[3:]


@register.filter
def split_name(id_and_name: str):
    return id_and_name.split('^')[1]


@register.filter
def increment_page(num):
    return num + 1


@register.filter
def decrement_page(num):
    return num - 1


@register.filter
def create_range(num):
    return list(range(num))


@register.filter
def count_elements_first(num):
    return (num - 1) * 25 + 1


@register.filter
def count_elements_sec(num):
    return (num - 1) * 25 + 25


@register.filter
def multiply(num1, num2):
    return num1 * num2


@register.filter
def enu_list(list_element):
    return enumerate(list_element)


@register.filter
def next_rebill(arr):
    if arr.get('unsub'):
        return None
    elif arr.get('pay_date'):
        pay_date = dt.datetime.strptime(arr.get('pay_date'), '%Y-%m-%d %H:%M:%S.%f')
        if pay_date > dt.datetime.now():
            return pay_date.strftime('%d.%m.%Y в %H:%M:%S')
        else:
            if arr.get('try_date'):
                try_date = dt.datetime.strptime(arr.get('pay_date'), '%Y-%m-%d %H:%M:%S.%f')
                return (try_date + dt.timedelta(days=arr.get('period'))).strftime('%d.%m.%Y в %H:%M:%S')
            else:
                subscription = dt.datetime.strptime(arr.get('start_date'), '%Y-%m-%d %H:%M:%S.%f')
                return (subscription + dt.timedelta(days=arr.get('period'))).strftime('%d.%m.%Y в %H:%M:%S')
    return None

