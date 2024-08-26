import math
from django.http import HttpResponse
from django.shortcuts import redirect, render
import json
import requests
from random import randint
from urllib.parse import urlparse, parse_qs
import re
from hashlib import md5
from django.contrib.auth.hashers import check_password
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import datetime as dt
from django.views.decorators.csrf import csrf_exempt
from frontend.functions import *
import socket
import time


def redirect_from_outside(request):
    response = redirect('profile')
    request.session.flush()
    if request.GET:
        request.session.set_expiry(value=3600)
        request.session['manager'] = request.GET['manager']
        request.session['id'] = request.GET['partner']
        try:
            request_partner = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)
        except:
            request_partner = json.loads(requests.get(f'{domain_api1}/partners/{request.session["id"]}/').content)
        request.session['user'] = request_partner.get('email')
        request.session['profile_info'] = request_partner
        if request_partner.get('user_is_active'):
            request.session['ban_web'] = False
        else:
            request.session['ban_web'] = True
    return response


def referal_incomming(request, uid):
    request.session['id'] = None
    request.session['user'] = None
    response = redirect('register')
    response.set_cookie('uid', uid, max_age=2592000, path='/')
    return response


def reg_user(request):
    if request.session.get('user'):
        return redirect('profile')

    request.recaptcha_is_valid = None

    if request.method == "POST":
        '''отправка POST запроса для внесения данных на стороне API'''
        email = request.POST.get('email')
        password = request.POST.get('password')

        recaptcha_response = request.POST.get('g-recaptcha-response')

        data = {
            'secret': '6LeEB-kjAAAAALVFVha4Fx659_CukfZvKK8wHffs',
            'response': recaptcha_response
        }

        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)

        result = r.json()

        if result['success']:
            request.recaptcha_is_valid = True
        else:
            request.recaptcha_is_valid = False
            message = 'АнтиСПАМ проверка не пройдена'
            return render(request, 'sign-up.html', {'message': message})

        '''ip-адрес при регистрации'''
        ip = get_client_ip(request)

        '''Если партнер регистрируется по реф ссылке'''
        if request.COOKIES.get('uid'):
            referal_partner_id = decode(request.COOKIES.get('uid'), BASE62) - 1000000

            response = requests.post(f'{DOMAIN_API}/partners/',
                json.dumps({
                    'email': email, 'password': password, 'percent': 50, 'referal_fees': 5,
                    'referal': referal_partner_id, "two_factor_auth": 0, 'ip_reg': ip, 'ip_auth': ip
                })
            )
            '''Обнуляю COOKIE, чтоб не было повторных реф регистраций без нового перехода по реф ссылке'''
            request.COOKIES['uid'] = None
        else:
            response = requests.post(f'{DOMAIN_API}/partners/',
                json.dumps({
                    'email': email, 'password': password, 'percent': 50, 'referal_fees': 5,
                    "two_factor_auth": 0, 'ip_reg': ip, 'ip_auth': ip
                })
            )

        if json.loads(response.content).get('detail'):
            '''Проверка прохождения регистрация и вывод сообщений об ошибках на стороне пользователя'''
            message = json.loads(response.content).get('detail')
            return render(request, 'sign-up.html', {'message': message})

        request.session['profile_info'] = json.loads(response.content)
        request.session['id'] = json.loads(response.content).get('id')
        request.session['user'] = email
        request.session['contest'] = json.loads(response.content).get('contest_check')
        request.session['telegram_id'] = json.loads(response.content).get('telegram_id')

        return redirect('profile')

    return render(request, 'sign-up.html')


@csrf_exempt
def signin(request):
    if request.session.get('user'):
        return redirect('profile')

    if request.method == 'POST':

        if request.POST.get('type') == 'check_auth':
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember = request.POST.get('remember_me')

            request_auth = requests.post(f'{DOMAIN_API}/partners/authenticate/',
                                         json.dumps({"email": email, "password": password}))
            response_auth = json.loads(request_auth.content)

            if response_auth.get('user_is_active') == 0:
                request.session["ban_web"] = True
                return redirect('ban_web')
            else:
                request.session["ban_web"] = False

            if response_auth.get('id'):
                '''ip-адрес авторизации'''
                ip = get_client_ip(request)

                if response_auth.get('two_factor_auth') == 1:
                    two_factor_auth = requests.post(
                        f'{domain_api1}/tfauth/{response_auth.get("id")}/',
                        {
                            "type": "auth",
                            "action": "get_code"
                        }
                    )
                    check_message = json.loads(two_factor_auth.content).get('auth_code')
                    request.session['check_tow_factor_auth'] = check_message
                else:
                    if remember:
                        request.session.set_expiry(value=3888000)
                    request.session['profile_info'] = response_auth
                    request.session['telegram_id'] = response_auth.get('telegram_id')
                    request.session["id"] = response_auth.get('id')
                    requests.patch(f'{DOMAIN_API}/partners/{request.session["id"]}/', json.dumps({'ip_auth': ip}))
                    request.session['user'] = email
                    request.session['contest'] = response_auth.get('contest_check')
                return HttpResponse(request_auth)
            return HttpResponse(request_auth)

        if request.POST.get('type') == 'check_tlg_mess':
            '''ip-адрес авторизации'''
            ip = get_client_ip(request)

            message_user = request.POST.get('message_code')
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember = request.POST.get('remember_me')

            request_auth = requests.post(f'{DOMAIN_API}/partners/authenticate/',
                                         json.dumps({"email": email, "password": password}))
            response_auth = json.loads(request_auth.content)

            if int(request.session.get('check_tow_factor_auth')) == int(message_user):
                if remember:
                    request.session.set_expiry(value=3888000)
                request.session['profile_info'] = response_auth
                request.session['telegram_id'] = response_auth.get('telegram_id')
                request.session["id"] = response_auth.get('id')
                requests.patch(f'{DOMAIN_API}/partners/{request.session["id"]}/', {'ip_auth': ip})
                request.session['user'] = email
                request.session['contest'] = response_auth.get('contest_check')
                return HttpResponse(json.dumps({'status': 'OK'}))
            else:
                return HttpResponse(json.dumps({'status': 'ERR'}))

    data = {'title': 'Авторизация пользователя'}
    return render(request, 'sign-in.html', {'data': data})


@get_error
@auth_block
def profile(request):
    title = 'Страница Профиля'
    time_for_h = str(dt.datetime.now().timestamp()).split('.')[0][:-3]
    md5_hash = md5(f'{request.session["id"]}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d_{time_for_h}'.encode()).hexdigest()

    try:
        profile_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)
    except:
        profile_info = json.loads(requests.get(f'{domain_api1}/partners/{request.session["id"]}/').content)

    try:
        request_by_req = json.loads(requests.get(f'{DOMAIN_API}/payoutrequisites/?partner_id={request.session["id"]}').content)[0]
    except:
        request_by_req = json.loads(requests.get(f'{domain_api1}/payoutrequisites/?partner_id={request.session["id"]}').content).get('results')[0]

    response_by_req = request_by_req
    message_new_check = ''  # переменные для вывода сообщ об ошибке при наличии
    message_cur_new_check = ''  # переменные для вывода сообщ об ошибке при наличии

    if request.method == 'POST':

        '''Смена телеграм'''
        if request.POST.get('type') == 'request_change_telegram':
            requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/',
                {
                    "type": "auth",
                    "action": "get_code"
                }
            )
            return HttpResponse(json.dumps({'status': 'OK'}))
        if request.POST.get('type') == 'check_telegram_code':
            data = {
                "type": "auth",
                "action": "verify_code",
                "auth_code": int(request.POST.get('message_code'))
            }
            two_factor_verify = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/', json=data
            )
            if json.loads(two_factor_verify.content).get('detail').lower() == 'ok':
                md5_hash = md5(f'{request.session["id"]}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d_{time_for_h}'.encode()).hexdigest()
                href = f"tg://resolve?domain=offeringpartnersbot&start=st-{md5_hash}-{request.session['id']}"

                '''Логирование действия пользователя'''
                requests.post(
                    f'{domain_api1}/partneractions/',
                    data={
                        'act_type': 'Профиль',
                        'manager': request.session.get('manager') if request.session.get('manager') else 0,
                        'partner': request.session['id'],
                        'ip': str(get_client_ip(request)),
                        'action': f'Смена Telegram',
                    }
                )
                return HttpResponse(json.dumps({'href': href}))
            else:
                return HttpResponse(json.dumps({'href': 'error'}))
        '''Запрос для получения кода на отмену 2х аутентификации'''
        if request.POST.get('type') == 'request_change_tfa':
            requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/',
                {
                    "type": "totfa",
                    "action": "get_code"
                }
            )
            return HttpResponse(json.dumps({'status': 'OK'}))
        '''Повторный запрос на проверку кода пользователя для отмены 2х аут'''
        if request.POST.get('type') == 'check_tlg_mess_totfa':
            verify_code_message = int(request.POST.get('message_code'))
            data = {
                "type": "totfa",
                "action": "verify_code",
                "totfa_code": verify_code_message
            }
            two_factor_verify = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/', json=data
            )
            return HttpResponse(two_factor_verify)
        '''Смена данных пользователя по 2х аутентификации'''
        if request.POST.get('type') == 'want_two_fack':
            value_two_fack = request.POST.get('value_two_fack_post')
            requests.patch(
                f'{DOMAIN_API}/partners/{request.session["id"]}/',
                json.dumps({'two_factor_auth': value_two_fack})
            )
            return HttpResponse(json.dumps({'status': 'OK'}))

        '''Полученик кода 2х факторной аутентификации для смены реквизитов'''
        if request.POST.get('type') == 'check_auth_for_req':
            requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/',
                {
                    "type": "req",
                    "action": "get_code"
                }
            )
            return HttpResponse(json.dumps({'status': 'OK'}))
        '''Поддверждение 2х факторной аутентификации для смены реквкзитов'''
        if request.POST.get('type') == 'check_tlg_mess_req':
            verify_code_message_req = int(request.POST.get('message_code'))
            data = {
                "type": "req",
                "action": "verify_code",
                "req_code": verify_code_message_req
            }
            two_factor_verify = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/', json=data
            )
            return HttpResponse(two_factor_verify)

        '''Скрипт для смены реквизитов партнера'''
        if request.POST.get('type') == 'payment_details':
            '''Отправка данных со второй вкладки реквизиты партнера'''
            capitalist = request.POST.get('capitalist')
            webmoney = request.POST.get('webmoney')
            qiwi = request.POST.get('qiwi')
            umoney = request.POST.get('umoney')

            rucard_card_data = request.POST.get('rucard_card_data')
            rucard_card_data = ''.join(re.findall('\d', str(rucard_card_data)))  # оставляю только цифры
            rucard_firstname = request.POST.get('rucard_firstname').upper()
            rucard_lastname = request.POST.get('rucard_lastname').upper()
            # '''UA'''
            # data_ua = request.POST.get('data_ua')
            # data_ua = ''.join(re.findall('\d', str(data_ua)))  # оставляю только цифры
            # ua_firstname = request.POST.get('data_ua_name').upper()
            # ua_lastname = request.POST.get('data_ua_surname').upper()
            '''KZ'''
            data_kz = request.POST.get('data_kz')
            data_kz = ''.join(re.findall('\d', str(data_kz)))  # оставляю только цифры
            kz_firstname = request.POST.get('data_kz_name').upper()
            kz_lastname = request.POST.get('data_kz_surname').upper()

            data_card_to_card = request.POST.get('data_card_to_card')
            data_card_to_card = ''.join(re.findall('\d', str(data_card_to_card)))  # оставляю только цифры

            data_mastercard_worldwide = request.POST.get('data_mastercard_worldwide')
            data_mastercard_worldwide = ''.join(re.findall('\d', str(data_mastercard_worldwide)))  # оставляю только цифры
            month_mc = request.POST.get('month_mc')
            year_mc = request.POST.get('year_mc')
            name_mc = request.POST.get('name_mc').upper()
            surname_mc = request.POST.get('surname_mc').upper()
            birth_date_mc = request.POST.get('birth_date_mc')
            country_code_mc = request.POST.get('country_code_mc')
            city_mc = request.POST.get('city_mc')
            address_mc = request.POST.get('address_mc')

            usdt_erc_20 = request.POST.get('usdt_erc_20')
            usdt_trc_20 = request.POST.get('usdt_trc_20')

            '''Для Ип'''
            ipru_name = request.POST.get('ipru_name')
            ipru_address = request.POST.get('ipru_address')
            ipru_inn = request.POST.get('ipru_inn')
            ipru_ogrn = request.POST.get('ipru_ogrn')
            ipru_rs = request.POST.get('ipru_rs')
            ipru_bank = request.POST.get('ipru_bank')
            ipru_inn_bank = request.POST.get('ipru_inn_bank')
            ipru_bik_bank = request.POST.get('ipru_bik_bank')
            ipru_ks_bank = request.POST.get('ipru_ks_bank')

            '''Для Юр. лиц РФ'''
            oooru_name = request.POST.get('oooru_name')
            oooru_address = request.POST.get('oooru_address')
            oooru_inn = request.POST.get('oooru_inn')
            oooru_kpp = request.POST.get('oooru_kpp')
            oooru_ogrn = request.POST.get('oooru_ogrn')
            oooru_rs = request.POST.get('oooru_rs')
            oooru_bank = request.POST.get('oooru_bank')
            oooru_inn_bank = request.POST.get('oooru_inn_bank')
            oooru_bik_bank = request.POST.get('oooru_bik_bank')
            oooru_ks_bank = request.POST.get('oooru_ks_bank')

            errors = []

            '''KZ check'''
            kz = [data_kz, kz_firstname, kz_lastname]
            if any(kz):
                if all(kz) == False:
                    errors.append('Необходиомо заполнить все данные по карте KZ')

            '''UA check'''
            # ua = [data_ua, ua_firstname, ua_lastname]
            # if any(ua):
            #     if all(ua) == False:
            #         errors.append('Необходиомо заполнить все данные по карте UA')

            '''Проверка заполнения данных ИП'''
            ip_data = [ipru_name, ipru_address, ipru_inn, ipru_ogrn, ipru_rs, ipru_bank, ipru_inn_bank, ipru_bik_bank,
                       ipru_ks_bank]
            if any(ip_data):
                if all(ip_data) == False:
                    errors.append('Необходиомо заполнить все данные по реквизитам ИП РФ')

            '''Проверка заполнения данных Юр. лиц РФ'''
            oooru_data = [oooru_name, oooru_address, oooru_inn, oooru_kpp, oooru_ogrn, oooru_rs, oooru_bank,
                          oooru_inn_bank, oooru_bik_bank, oooru_ks_bank]
            if any(oooru_data):
                if all(oooru_data) == False:
                    errors.append('Необходиомо заполнить все данные по реквизитам Юр. лица РФ')

            '''Проверка полного заполнения реквизитов карты РФ'''
            rucard_check = [rucard_card_data, rucard_firstname, rucard_lastname]
            if any(rucard_check):
                if all(rucard_check) == False:
                    errors.append('Необходиомо заполнить все поля для карты РФ, RUS')
                if len(rucard_card_data) != 16:
                    errors.append('Некорректно заполнено поле номера карты РФ, RUS')
                if rucard_firstname.replace('-', '').replace(' ', '').isalpha() == False:
                    errors.append('Некорректно заполнено поле Имени в данных карты РФ, RUS')
                if rucard_lastname.replace('-', '').replace(' ', '').isalpha() == False:
                    errors.append('Некорректно заполнено поле Фамилии в данных карты РФ, RUS')

            '''Проверка полного заполнения реквизитов карты MasterCard'''
            master_card_check = [data_mastercard_worldwide, month_mc, year_mc, name_mc, surname_mc, birth_date_mc,
                                 country_code_mc, city_mc, address_mc]
            if any(master_card_check):
                if all(master_card_check) == False:
                    errors.append('Не заполнены все поля для MasterCard')
                if len(data_mastercard_worldwide) != 16:
                    errors.append('Неправильно заполнен номер карты MasterCard')
                if len(month_mc) > 2:
                    errors.append('Неправильно заполнен месяц рождения в MasterCard ')
                if len(year_mc) != 4:
                    errors.append('Неправильно заполнен года рождения в MasterCard')
                if name_mc.replace('-', '').replace(' ', '').isalpha() == False:
                    errors.append('Неправильно заполнено Имя в MasterCard')
                if surname_mc.replace('-', '').replace(' ', '').isalpha() == False:
                    errors.append('Неправильно заполнена Фамилия в MasterCard')
                if len(birth_date_mc) == 0:
                    errors.append('Не заполнена дата рождения в MasterCard')
                if country_code_mc:
                    if (len(country_code_mc) != 2) or (country_code_mc.isalpha() == False):
                        errors.append('Код страны в MasterCard должен содержать 2 латиских символа')

            '''Проверка заполнения карты Card2Card'''
            if data_card_to_card:
                if len(data_card_to_card) != 16:
                    errors.append('Неверно заполнено поле Card2Card')

            data = {
                'capitalist': capitalist, 'webmoney': webmoney, 'qiwi': qiwi, 'umoney': umoney,
                'data': rucard_card_data, 'name_data': rucard_firstname, 'surname_data': rucard_lastname,
                'data_card_to_card': data_card_to_card, 'data_mastercard_worldwide': data_mastercard_worldwide,
                'month_mc': month_mc, 'year_mc': year_mc, 'name_mc': name_mc, 'surname_mc': surname_mc,
                'birth_date_mc': birth_date_mc, 'country_code_mc': country_code_mc, 'city_mc': city_mc,
                'address_mc': address_mc, 'usdt_erc_20': usdt_erc_20, 'usdt_trc_20': usdt_trc_20,
                'ip_name': ipru_name, 'ip_address': ipru_address, 'ip_inn': ipru_inn, 'ip_ogrn': ipru_ogrn,
                'ip_rs': ipru_rs, 'ip_bank': ipru_bank, 'ip_bank_inn': ipru_inn_bank, 'ip_bank_bik': ipru_bik_bank,
                'ip_bank_ks': ipru_ks_bank, 'oooru_name': oooru_name, 'oooru_address': oooru_address,
                'oooru_inn': oooru_inn, 'oooru_kpp': oooru_kpp, 'oooru_ogrn': oooru_ogrn, 'oooru_rs': oooru_rs,
                'oooru_bank': oooru_bank, 'oooru_bank_inn': oooru_inn_bank, 'oooru_bank_bik': oooru_bik_bank,
                'oooru_bank_ks': oooru_ks_bank, 'data_kz': data_kz, 'name_data_kz': kz_firstname,
                'surname_data_kz': kz_lastname,
                # 'data_ua': data_ua, 'name_data_ua': ua_firstname,
                # 'surname_data_ua': ua_lastname,
            }

            '''Проверка на ошибки'''
            if len(errors):
                return HttpResponse(json.dumps({'errors': errors}))
            else:
                requests.patch(
                    f'{DOMAIN_API}/payoutrequisites/{response_by_req["id"]}/',
                    json.dumps(data)
                )
                new_dict_for_logs = dict()
                for key, val in data.items():
                    if val != '':
                        new_dict_for_logs.setdefault(key, val)

                '''Логирование действия пользователя'''
                requests.post(
                    f'{domain_api1}/partneractions/',
                    data={
                        'act_type': 'Реквкизиты',
                        'manager': request.session.get('manager') if request.session.get('manager') else 0,
                        'partner': request.session['id'],
                        'ip': str(get_client_ip(request)),
                        'action': f'Добавление/Удаление {str(new_dict_for_logs)}',
                    }
                )
                return HttpResponse(json.dumps({'data': data}))

        '''Получение кода для 2х факторной ауатентификации для смены пароля'''
        if request.POST.get('type') == 'check_auth_for_pwd':
            requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/',
                {
                    "type": "password",
                    "action": "get_code"
                }
            )
            return HttpResponse(json.dumps({'status': 'OK'}))
        '''Проверка Кода 2х факторной аутентификации для смены пароля'''
        if request.POST.get('type') == 'totfa_password_check_code':
            data = {
                "type": "password",
                "action": "verify_code",
                "password_code": int(request.POST.get('message_code'))
            }
            passwd_request_verify = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/', json=data
            )
            return HttpResponse(passwd_request_verify)
        '''Проверка старого пароля перед сменой'''
        if request.POST.get('type') == 'check_pwd':
            current_password = request.POST.get('current_pwd_post')
            '''Захешированный пароль хранящийся в БД'''
            pwd_from_api = json.loads(
                requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content).get('password')
            '''Проверка нового и старого пароля'''
            if check_password(current_password, pwd_from_api):
                return HttpResponse(json.dumps({'status': 'OK'}))
            else:
                return HttpResponse(json.dumps({'status': 'ERR'}))
        '''PATCH-запрос на API-2 для отправки смены пароля'''
        if request.POST.get('type') == 'change_pwd':
            new_password = request.POST.get('new_pwd_post')
            '''Отправка нового пароля для смены текущего'''
            requests.patch(
                f'{DOMAIN_API}/partners/{request.session["id"]}/',
                json.dumps({'password': new_password})
            )

            '''Логирование действия пользователя'''
            requests.post(
                f'{domain_api1}/partneractions/',
                data={
                    'act_type': 'Профиль',
                    'manager': request.session.get('manager') if request.session.get('manager') else 0,
                    'partner': request.session['id'],
                    'ip': str(get_client_ip(request)),
                    'action': f'Смена пароля'
                }
            )
            return HttpResponse(json.dumps({'status': 'OK'}))

        '''Запрос на смену номера телефона и НИКа для ТОПа'''
        if request.POST.get('type') == 'contacts_edit':
            phone = request.POST.get('telephone_post')

            want_to_get_notifications = ''
            if request.POST.get('checkNews'):
                want_to_get_notifications = 1
            else:
                want_to_get_notifications = 0

            top_nickname = request.POST.get('nick_top_post')

            requests.patch(
                f'{DOMAIN_API}/partners/{request.session["id"]}/',
                json.dumps(
                    {
                        'phone': phone,
                        'want_to_get_notifications': want_to_get_notifications,
                        'contest_nick': top_nickname
                    }
                )
            )
            data_change_prof = ''
            data_change_prof += f'Смена номера телефона: {phone} ' if phone != profile_info.get('phone') else ''
            data_change_prof += f'Смена ТОПника - {top_nickname} ' if top_nickname != profile_info.get('contest_nick') else ''
            '''Логирование действия пользователя'''
            if data_change_prof:
                requests.post(
                    f'{domain_api1}/partneractions/',
                    data={
                        'act_type': 'Профиль',
                        'manager': request.session.get('manager') if request.session.get('manager') else 0,
                        'partner': request.session['id'],
                        'ip': str(get_client_ip(request)),
                        'action': data_change_prof
                    }
                )
            return HttpResponse(json.dumps({'status': 'ok'}))

    '''Информация о партнере с его реф ссылкой и реф отчислениями'''
    request.session['telegram_id'] = profile_info.get('telegram_id')
    two_factor_auth = profile_info.get('two_factor_auth')
    if profile_info.get('user_is_active') == 1:
        request.session["user_is_active"] = True
        request.session['ban_web'] = False
    else:
        request.session["user_is_active"] = False
        request.session['ban_web'] = True

    '''Информация о партнере с его реф ссылкой и реф отчислениями'''
    request.session['contest'] = profile_info.get('contest_check')
    profile_info['ref_link'] = encode(int(request.session["id"]) + 1000000, BASE62)

    '''Вывод информации о том кто пригласил пользователя'''
    try:
        referal_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{profile_info["referal_id"]}/').content)
        if referal_info.get('detail'):
            referal_info = 0
    except BaseException:
        referal_info = 0

    '''Информация по рефералам партнера'''
    profit_from_referals = 0
    refer_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/referals/').content)
    for ref in refer_info:
        '''для правильного отображения суммы отчислений с реферала'''
        if ref.get('amount'):
            profit_from_referals += ref['amount']
        else:
            ref['amount'] = 0
        '''Скрываю рефералов'''
        ref['email'] = f'{ref["email"][:3]}****{ref["email"][ref["email"].find("@"):]}'

    opened = 'contacts_edit'

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': title, 'page_name': 'Профиль', 'profile_info': profile_info, 'req_partner': response_by_req,
        'md5_hash': md5_hash, 'refer_info': refer_info, 'profit_from_referals': profit_from_referals,
        'message_new_check': message_new_check, 'message_cur_new_check': message_cur_new_check,
        'referal_info': referal_info, 'open': opened, 'two_factor_auth': two_factor_auth, 'time_for_h': time_for_h
    }
    return render(request, 'profile.html', data)


@get_error
@check_profile
def offer(request, offer_id):
    session_request_subs_offers_balance(request)  # Доп данные для сессии
    offer_tarif_info_dict = json.loads(json.loads(requests.get(f'{domain_api1}/offers/{offer_id}/get_offer').content))

    if offer_tarif_info_dict.get('tarif'):
        tarif_info = offer_tarif_info_dict.get('tarif')
    else:
        tarif_info = False

    info_by_offer_from_api = list(filter(lambda a: int(a.get('id')) == int(offer_id), request.session.get('offers_list')))

    if info_by_offer_from_api:
        info_by_offer_from_api = info_by_offer_from_api[0]
    else:
        return render(request, '404.html')

    info_by_offer_from_api["unexepted_traffic"] = info_by_offer_from_api["unexepted_traffic"].split(';')  #  для вывода запрещенного трафика
    info_by_offer_from_api["description"] = info_by_offer_from_api["description"].split(';')  # для вывода описания оффера

    try:
        landings = json.loads(requests.get(f'{DOMAIN_API}/landings/?limit=1000').content)
        landings_list = get_privat_landings(landings, offer_id, request.session['id'])
    except:
        landings = json.loads(requests.get(f'{domain_api1}/landings/?limit=1000').content).get('results')
        landings_list = get_privat_landings_api1(landings, offer_id, request.session['id'])

    data = {
        'title': 'Страница Оффера', 'page_name': info_by_offer_from_api.get('name'), 'tarif_info': tarif_info,
        'offer_info': info_by_offer_from_api, 'landings_list': landings_list, 'offer_id': offer_id,
    }
    return render(request, 'offer.html', data)


@get_error
@check_profile
def add_streams(request):
    inside = {'page_title': 'Потоки', 'page_url': "/streams/"}

    try:
        domain = json.loads(
            requests.get(f'{DOMAIN_API}/domain/').content
        ).get('domain')
    except:
        domain = json.loads(
            requests.get(f'{domain_api1}/domain/').content
        ).get('domain')

    offers_list = request.session['offers_list']
    id_offer_public = []
    for offers in offers_list:
        id_offer_public.append(int(offers['id']))

    all_landings_list = json.loads(requests.get(f'{domain_api1}/landings/?limit=1000').content).get('results')
    landings_list = get_all_access_land_api1(all_landings_list, id_offer_public, request.session['id'])

    '''данные по Postbacks '''
    response_postbacks = json.loads(
        requests.get(
            f'{DOMAIN_API}/postbacks/?partner_id={request.session["id"]}'
        ).content
    )
    postbacks_partner = response_postbacks.get('postbacks')
    get_postback(postbacks_partner)

    if request.method == 'POST':

        if request.POST.get('type') == 'land_select':
            land_id = request.POST.get('land_id')
            land_request = requests.get(f'{domain_api1}/landings/{land_id}')
            land_response = json.loads(land_request.content)[0]
            try:
                request.session['land_additional_create'] = json.loads(land_response.get('elements'))
            except:
                request.session['land_additional_create'] = ''
            return HttpResponse(json.dumps(land_response))

        land_add_data = request.session.get('land_additional_create')
        post_add_land = dict()
        if land_add_data:
            for i in land_add_data.get('elements'):
                post_add_land.setdefault(i.get('name'), request.POST.get(f"{i.get('name')}"))

        name = request.POST.get('streamName')
        offer_id = request.POST.get('offer')
        landing_id = request.POST.get('land')

        yandex_metric = request.POST.get('streamTrackerYaMetrika')
        google_analytics = request.POST.get('streamTrackerGoogleAn')
        top_mail_ru = request.POST.get('streamTrackerTopMailRu')
        facebook_pixel = request.POST.get('streamTrackerFBpixel')
        vk_counter = request.POST.get('streamTrackerVKcounter')
        tiktok_pixel = request.POST.get('streamTrackerTTpixel')

        uid = randint(0, 1000000000)
        link = f'https://{domain}/{encode(uid, BASE62)}'

        postback_id = request.POST.getlist('postbacks')

        if post_add_land:
            add_streams = {
                'name': name, 'partner_id': request.session['id'], "uid": uid, 'yandex_metric': yandex_metric,
                'google_analytics': google_analytics, 'top_mail_ru': top_mail_ru,
                'facebook_pixel': facebook_pixel, 'vk_counter': vk_counter, 'link': link,
                'tiktok_pixel': tiktok_pixel, 'offer_id': offer_id, 'landing_id': landing_id,
                'postback_id': postback_id, 'landingelement_data': json.dumps(post_add_land)
            }
        else:
            add_streams = {
                'name': name, 'partner_id': request.session['id'], "uid": uid, 'offer_id': offer_id, 'link': link,
                'facebook_pixel': facebook_pixel, 'yandex_metric': yandex_metric, 'tiktok_pixel': tiktok_pixel,
                'google_analytics': google_analytics, 'top_mail_ru': top_mail_ru, 'postback_id': postback_id,
                'vk_counter': vk_counter, 'landing_id': landing_id,
            }

        '''POST-запрос на API для создания нового потока'''
        try:
            requests.post(
                f'{DOMAIN_API}/streams/',
                json.dumps(add_streams)
            )
        except:
            requests.post(
                f'{domain_api1}/streams/',
                data=add_streams
            )

        '''Логирование действия пользователя'''
        del add_streams['partner_id']
        requests.post(
            f'{domain_api1}/partneractions/',
            data={
                'act_type': 'Потоки',
                'manager': request.session.get('manager') if request.session.get('manager') else 0,
                'partner': request.session['id'],
                'ip': str(get_client_ip(request)),
                'action': f'Создание потока {str(add_streams)}',
            }
        )

        requests.get(f'https://{domain}/update_cron_streams.php')
        return redirect('streams')

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    data = {
        'title': 'Добавление потока', 'page_name': 'Добавление потока', 'postbacks_partner': postbacks_partner,
        'landings_list': landings_list, 'inside': inside
    }
    return render(request, 'streams-add.html', data)


@get_error
@check_profile
def streams(request):
    limit = request.session.get("limit_streams")
    if not limit:
        request.session["limit_streams"] = 25

    page = set_page(request.GET)

    try:
        domain = json.loads(requests.get(f'{DOMAIN_API}/domain/').content).get('domain')
    except:
        domain = json.loads(requests.get(f'{domain_api1}/domain/').content).get('domain')

    if request.method == "POST":
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_streams"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    limit = request.session["limit_streams"]
    offset = set_offset(page, limit)
    request.session['offset_stream'] = offset

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    response_offers = request.session.get('offers_list')
    try:
        response_landings = json.loads(requests.get(f'{DOMAIN_API}/landings/?limit=1000').content)
    except:
        response_landings = json.loads(requests.get(f'{domain_api1}/landings/?limit=1000').content).get('results')

    '''Данные для отображения Потоков'''
    try:
        response_streams = json.loads(requests.get(f'{DOMAIN_API}/streams/?partner_id={request.session["id"]}&limit={limit}&offset={offset}').content)

        original_count = response_streams.get('count')
        streams = response_streams.get('streams')
        count = math.ceil(int(response_streams.get('count')) / limit)

        counts = 1
        for stream in streams:
            if stream.get('landingelement_data'):
                stream['landingelement_data'] = json.loads(stream.get('landingelement_data'))
            for offer in response_offers:
                if int(stream.get('offer_id_id')) == int(offer['id']):
                    stream['offer_name'] = offer['name']
            for land in response_landings:
                if int(stream.get('landing_id_id')) == int(land['id']):
                    stream['land_name'] = land['name']
            stream['uid'] = encode(int(stream['uid']), BASE62)
            if stream.get('link'):
                new_list = stream.get('link').split('/')
                stream['link'] = f'{new_list[0]}//{domain}/{new_list[3]}'
            else:
                stream['link'] = f'https://{domain}/{stream["uid"]}'
            stream.setdefault('count', str(counts))
            counts += 1
    except:
        response_streams = json.loads(requests.get(f'{domain_api1}/streams/?partner_id={request.session["id"]}&limit={limit}&offset={offset}').content)

        original_count = response_streams.get('count')
        streams = response_streams.get('results')
        count = math.ceil(int(response_streams.get('count')) / limit)

        counts = 1
        for stream in streams:
            if stream.get('landingelement_data'):
                stream['landingelement_data'] = json.loads(stream.get('landingelement_data'))
            for offer in response_offers:
                if int(stream.get('offer_id')) == int(offer['id']):
                    stream['offer_name'] = offer['name']
            for land in response_landings:
                if int(stream.get('landing_id')) == int(land['id']):
                    stream['land_name'] = land['name']
            stream['uid'] = encode(int(stream['uid']), BASE62)
            if stream.get('link'):
                new_list = stream.get('link').split('/')
                stream['link'] = f'{new_list[0]}//{domain}/{new_list[3]}'
            else:
                stream['link'] = f'https://{domain}/{stream["uid"]}'
            stream.setdefault('count', str(counts))
            counts += 1

    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]

    data = {
        'title': 'Потоки', 'page_name': 'Потоки', 'original_count': original_count, 'user_id': request.session['id'],
        'streams': streams, 'limit': limit, 'url_params': url_params, 'count': count, 'page': page
    }
    return render(request, 'streams.html', data)


@get_error
@check_profile
def edit_stream(request, stream_uid):
    try:
        domain = json.loads(
            requests.get(f'{DOMAIN_API}/domain/').content
        ).get('domain')
    except:
        domain = json.loads(
            requests.get(f'{domain_api1}/domain/').content
        ).get('domain')

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    inside = {'page_title': 'Потоки', 'page_url': "/streams/"}

    '''Декодирую UID в десятичную систему'''
    uid = decode(stream_uid, BASE62)

    '''для заполнения полей НАЗВАНИЕ, ТРЕКЕРЫ и ПИКСЕЛИ существующими данными с API'''
    requests_streams = requests.get(f'{domain_api1}/streams/?partner_id={request.session["id"]}&limit={request.session["limit_streams"]}&offset={request.session["offset_stream"]}')
    streams_get_requests = json.loads(requests_streams.content).get('results')

    try:
        streams_get_request = list(filter(lambda a: int(a.get('uid')) == int(uid), streams_get_requests))[0]
    except IndexError:
        return render(request, '404.html')

    not_access = 0
    if streams_get_request.get('link'):
        new_list = streams_get_request.get('link').split('/')
        streams_get_request['link'] = f'{new_list[0]}//{domain}/{new_list[3]}'
    else:
        streams_get_request['link'] = f'https://{domain}/{stream_uid}'

    try:
        streams_get_request['partner_id_id'] = int(streams_get_request.get('partner_id_id'))
        streams_get_request['landing_id_id'] = int(streams_get_request.get('landing_id_id'))
        streams_get_request['offer_id_id'] = int(streams_get_request.get('offer_id_id'))
    except:
        streams_get_request['partner_id_id'] = int(streams_get_request.get('partner_id'))
        streams_get_request['landing_id_id'] = int(streams_get_request.get('landing_id'))
        streams_get_request['offer_id_id'] = int(streams_get_request.get('offer_id'))
        streams_get_request['postback_id'] = str(streams_get_request.get('postback_id'))[1:-1]

    try:
        stream_id = streams_get_request.get('id')
    except AttributeError:
        stream_id = 0
        not_access = 1

    ''' данные для добавления "дополнительных параметров" в поля для заполнения '''
    sub_default = {'cid': '', 'sub1': '', 'sub2': '', 'sub3': '',
                  'sub4': '', 'sub5': '', 'utm_source': '', 'utm_medium': '',
                  'utm_campaign': '', 'utm_content': '', 'utm_term': ''}
    try:
        url_link = streams_get_request.get('link')
    except AttributeError:
        url_link = ''
        not_access = 1

    parsed_url = urlparse(url_link)
    sub_params = dict(list(sub_default.items()) + list(parse_qs(parsed_url.query).items()))

    for key, items in sub_params.items():
        sub_params[key] = ''.join(items)

    ''' наличие Postbacks партнера и вывод всех на экран '''
    try:
        response_postbacks = requests.get(f'{DOMAIN_API}/postbacks/?partner_id={request.session["id"]}')
        postbacks_list = json.loads(response_postbacks.content).get('postbacks')
        get_postback(postbacks_list)
    except:
        response_postbacks = requests.get(f'{domain_api1}/postbacks/?partner_id={request.session["id"]}')
        postbacks_list = json.loads(response_postbacks.content).get('results')

    ''' Список Офферов '''
    offers_list = request.session['offers_list']
    id_offer_public = []

    for offer in offers_list:
        id_offer_public.append(int(offer['id']))

    all_landings_list = json.loads(requests.get(f'{domain_api1}/landings/?limit=1000').content).get('results')
    landings_list = get_all_access_land_api1(all_landings_list, id_offer_public, request.session['id'])

    if request.method == 'POST':

        if request.POST.get('type') == 'land_select':
            land_id = request.POST.get('land_id')
            land_request = requests.get(f'{domain_api1}/landings/{land_id}/')
            land_response = json.loads(land_request.content)[0]
            request.session['edit_stream_elements'] = json.loads(land_response.get('elements'))
            return HttpResponse(json.dumps(land_response))

        ''' Для отправки изменений в сущность streams '''
        additional_data = request.session.get('edit_stream_elements')

        name = request.POST.get('streamName')
        yandex_metric = request.POST.get('streamTrackerYaMetrika')
        google_analytics = request.POST.get('streamTrackerGoogleAn')
        top_mail_ru = request.POST.get('streamTrackerTopMailRu')
        facebook_pixel = request.POST.get('streamTrackerFBpixel')
        vk_counter = request.POST.get('streamTrackerVKcounter')
        tiktok_pixel = request.POST.get('streamTrackerTTpixel')
        offer_id = request.POST.get('offer')
        landing_id = request.POST.get('land')
        link = request.POST.get('url')
        postback_id = request.POST.getlist('postbacks')

        data_patch = {
            'name': name, 'yandex_metric': yandex_metric,
            'google_analytics': google_analytics, 'top_mail_ru': top_mail_ru,
            'facebook_pixel': facebook_pixel, 'vk_counter': vk_counter,
            'tiktok_pixel': tiktok_pixel, 'postback_id': postback_id,
            'offer_id': offer_id, 'landing_id': landing_id, 'link': link
        }

        post_add_land = dict()
        if additional_data is not None:
            try:
                for i in additional_data.get('elements'):
                    if request.POST.get(f"{i.get('name')}"):
                        post_add_land.setdefault(i.get('name'), request.POST.get(f"{i.get('name')}"))
            except AttributeError:
                for i in additional_data:
                    if request.POST.get(f"{i.get('name')}"):
                        post_add_land.setdefault(i.get('name'), request.POST.get(f"{i.get('name')}"))

        if post_add_land:
            '''внесение изменений в Streams'''
            data_patch['landingelement_data'] = json.dumps(post_add_land)
            requests.patch(f'{domain_api1}/streams/{stream_id}/', data=data_patch)
        else:
            requests.patch(f'{domain_api1}/streams/{stream_id}/', data=data_patch)

        '''Логирование действия пользователя'''
        requests.post(
            f'{domain_api1}/partneractions/',
            data={
                'act_type': 'Потоки',
                'manager': request.session.get('manager') if request.session.get('manager') else 0,
                'partner': request.session['id'],
                'ip': str(get_client_ip(request)),
                'action': f'Редактирование - {str(data_patch)}'
            }
        )

        requests.get(f'https://{domain}/update_cron_streams.php')
        return redirect('streams')

    if streams_get_request.get('landingelement_data') and (streams_get_request.get('landingelement_data') != '0'):
        streams_get_request['landingelement_data'] = json.loads(streams_get_request.get('landingelement_data'))
        for i in streams_get_request.get('landingelement_data'):
            if streams_get_request['landingelement_data'][i] is None:
                streams_get_request['landingelement_data'][i] = ''
    else:
        streams_get_request['landingelement_data'] = "0"

    land_request = requests.get(f'{domain_api1}/landings/{streams_get_request.get("landing_id")}/')
    try:
        land_response = json.loads(land_request.content)[0]
        land_additional_data = json.loads(land_response.get('elements')).get('elements')
        request.session['edit_stream_elements'] = land_additional_data
    except:
        land_additional_data = ''
        request.session['edit_stream_elements'] = None

    streams_get_request['offer_id_id'] = int(streams_get_request.get('offer_id_id'))
    streams_get_request['landing_id_id'] = int(streams_get_request.get('landing_id_id'))
    data = {
        'title': 'Редактирование потока', 'inside': inside, 'page_name': 'Редактирование потока',
        'landings': landings_list, 'sub_params': sub_params, 'url_link': url_link,
        'stream_get': streams_get_request, 'postbacks_partner': postbacks_list, 'uid': stream_uid,
        'user_id': int(request.session["id"]), 'land_response_main': json.dumps(land_additional_data),
        'offers_info': offers_list, 'not_access': not_access, 'domain': domain,
    }
    return render(request, 'streams-edit.html', data)


@get_error
@check_profile
def postbacks(request):

    response_postbacks = json.loads(requests.get(f'{DOMAIN_API}/postbacks/?partner_id={request.session["id"]}').content)
    postbacks_partner = response_postbacks.get('postbacks')
    get_postback(postbacks_partner)

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': 'ПостБэки', 'page_name': 'PostBacks', 'postbacks_partner': postbacks_partner
    }
    return render(request, 'postbacks.html', data)


@get_error
@check_profile
def add_postback(request):

    inside = {'page_title': 'PostBacks', 'page_url': "/postbacks/"}

    if request.method == 'POST':
        name = request.POST.get('postbackName')
        method_select = request.POST.get('method_select')
        link = request.POST.get('link')
        postdata = request.POST.get('postdata')

        event_id = []
        if request.POST.get('cbPostBacksReg'):
            event_id.append(1)
        if request.POST.get('cbPostBacksActiv'):
            event_id.append(2)
        if request.POST.get('cbPostBacksSubs'):
            event_id.append(3)
        if request.POST.get('cbPostBacksRebill'):
            event_id.append(4)
        if request.POST.get('cbPostBacksUnSubs'):
            event_id.append(5)

        postdata = json.dumps(postdata)

        postbacks_add = {
            'name': name, 'method': method_select, 'link': link, 'partner_id': request.session['id'],
            'event_id': event_id, 'postdata': postdata
        }

        ''' POST запрос на добавление POSTBACK'a '''
        try:
            requests.post(
                f'{DOMAIN_API}/postbacks/',
                json.dumps(postbacks_add)
            )
        except:
            requests.post(
                f'{DOMAIN_API}/postbacks/',
                data=postbacks_add
            )

        '''Логирование действия пользователя'''
        del postbacks_add['partner_id']
        requests.post(
            f'{domain_api1}/partneractions/',
            data={
                'act_type': 'Постбэки',
                'manager': request.session.get('manager') if request.session.get('manager') else 0,
                'partner': request.session['id'],
                'ip': str(get_client_ip(request)),
                'action': f'Создание - {str(postbacks_add)}',
            }
        )
        return redirect('postbacks')

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': 'Добавление ПостБэка', 'inside': inside, 'page_name': 'Добавление ПостБэка'
    }
    return render(request, 'postbacks-add.html', data)


@get_error
@check_profile
def edit_postback(request, postback_id):

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    inside = {'page_title': 'PostBacks', 'page_url': "/postbacks/"}

    ''' Получение информации о редактируемом POSTBACK'e '''
    response_postbacks = requests.get(f'{DOMAIN_API}/postbacks/{postback_id}/')
    postback_get_request = json.loads(response_postbacks.content)

    if postback_get_request.get('postdata'):
        postback_get_request['postdata'] = postback_get_request.get('postdata').replace('"', '')

    if postback_get_request.get('event_id'):
        postback_get_request['event_id'] = postback_get_request.get('event_id').split(', ')

    if request.method == 'POST':
        name = request.POST.get('postbackName')
        method_select = request.POST.get('method_select')
        link = request.POST.get('link')
        postdata = json.dumps(request.POST.get('postdata'))

        event_id = []
        if request.POST.get('cbPostBacksReg'):
            event_id.append(1)
        if request.POST.get('cbPostBacksActiv'):
            event_id.append(2)
        if request.POST.get('cbPostBacksSubs'):
            event_id.append(3)
        if request.POST.get('cbPostBacksRebill'):
            event_id.append(4)
        if request.POST.get('cbPostBacksUnSubs'):
            event_id.append(5)

        postbacks_add = {
            'name': name, 'method': method_select, 'link': link, 'partner_id': request.session['id'],
            'event_id': event_id, 'postdata': postdata
        }

        old_data = {
            'name': postback_get_request.get('name'),
            'method': postback_get_request.get('method'),
            'link': postback_get_request.get('link'),
            'partner_id': int(request.session['id']),
            'event_id': postback_get_request.get('event_id'),
            'postdata': postback_get_request.get('postdata')
        }

        if name == '' or method_select is None or link == '':
            message_err = 'Название постбека и URL обязательное поле'
            data = {
                'title': 'Редактирование ПостБэка', 'inside': inside, 'page_name': 'Редактирование ПостБэка',
                'message_err': message_err, 'postback_get_data': postback_get_request
            }
            return render(request, 'postbacks-edit.html', data)
        else:
            ''' patch запрос на изменения POSTBACK'a'''
            requests.patch(
                f'{DOMAIN_API}/postbacks/{postback_id}/',
                json.dumps(postbacks_add)
            )

            if postbacks_add != old_data:
                del postbacks_add['partner_id']
                '''Логирование действия пользователя'''
                requests.post(
                    f'{domain_api1}/partneractions/',
                    data={
                        'act_type': 'Постбэки',
                        'manager': request.session.get('manager') if request.session.get('manager') else 0,
                        'partner': request.session['id'],
                        'ip': str(get_client_ip(request)),
                        'action': f'Редактирование - {str(postbacks_add)}',
                    }
                )
            return redirect('postbacks')

    '''Для ограничения вывода логов постбека других пользователей'''
    not_access = 0
    if int(postback_get_request['partner_id_id']) != int(request.session["id"]):
        not_access += 1

    data = {
        'title': 'Редактирование ПостБэка', 'inside': inside, 'page_name': 'Редактирование ПостБэка',
        'postback_get_data': postback_get_request, 'not_access': not_access
    }
    return render(request, 'postbacks-edit.html', data)


@get_error
@check_profile
def logs_postback(request, postback_id):

    limit = request.session.get("limit_postback_logs")
    if not limit:
        request.session["limit_postback_logs"] = 25
    page = set_page(request.GET)

    if request.method == "POST":
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_postback_logs"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    limit = request.session["limit_postback_logs"]
    offset = set_offset(page, limit)

    session_request_subs_offers_balance(request)
    inside = {'page_title': 'PostBacks', 'page_url': "/postbacks/"}
    postback_get_request = json.loads(requests.get(f'{DOMAIN_API}/postbacks/{postback_id}/logs/?limit={limit}&offset={offset}').content)
    postback_info = json.loads(requests.get(f'{DOMAIN_API}/postbacks/{postback_id}/').content)

    original_count = postback_get_request.get('count')
    logs_response = postback_get_request.get('logs')
    count = math.ceil(int(postback_get_request.get('count')) / limit)

    '''Для ограничения вывода логов постбека других пользователей'''
    not_access = 0
    if int(postback_info['partner_id_id']) != int(request.session["id"]):
        not_access += 1

    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]

    data = {
        'title': 'Логи ПостБэка', 'inside': inside, 'page_name': 'Логи ПостБэка', 'url_params': url_params,
        'postback_info': postback_info, 'logs_response': logs_response, 'not_access': not_access,
        'original_count': original_count, 'count': count, 'page': page,  'limit': limit
    }
    return render(request, 'postbacks-logs.html', data)


@get_error
@check_profile
def payments(request):

    limit = request.session.get("limit_payments")

    if not limit:
        request.session["limit_payments"] = 25
    page = set_page(request.GET)

    if request.method == "POST":
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_payments"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    limit = request.session["limit_payments"]
    offset = set_offset(page, limit)

    ''' Информация для заполнения формы '''
    try:
        response_all_payments = json.loads(requests.get(f'{DOMAIN_API}/payouts/?limit={limit}&offset={offset}&partner_id={request.session["id"]}').content)
        payouts_partner = response_all_payments.get('payouts')
        original_count = response_all_payments.get('count')
        count = math.ceil(int(response_all_payments.get('count')) / limit)
    except:
        response_all_payments = json.loads(requests.get(
            f'{domain_api1}/payouts/?limit={limit}&offset={offset}&partner_id={request.session["id"]}').content)
        payouts_partner = response_all_payments.get('results')
        original_count = response_all_payments.get('count')
        count = math.ceil(int(response_all_payments.get('count')) / limit)

    try:
        for pay in payouts_partner:
            if pay.get('comission') is None:
                pay['sum_realise'] = (pay.get('sum') - (pay.get('sum')) / 100) - pay.get('fix')
            else:
                pay['sum_realise'] = (pay.get('sum') - (pay.get('sum')) * (pay.get('comission')) / 100) - pay.get('fix')
    except BaseException:
        payouts_partner = []

    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]
    session_request_subs_offers_balance(request)  # Доп данные для сессии
    data = {
        'title': 'Выплаты', 'page_name': 'Выплаты', 'original_count': original_count, 'limit': limit,
        'payouts_partner': payouts_partner, 'url_params': url_params, 'count': count, 'page': page,
    }
    return render(request, 'payments.html', data)


@get_error
@check_profile
def add_payment(request):
    try:
        profile_info_request = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)
    except:
        profile_info_request = json.loads(requests.get(f'{domain_api1}/partners/{request.session["id"]}/').content)

    inside = {'page_title': 'Выплаты', 'page_url': '/payments/'}

    ''' Информация по реквизитам '''
    card = requests.get(f'{DOMAIN_API}/payoutrequisites/?partner_id={request.session["id"]}')
    req_partner = json.loads(card.content)[0]

    all_req = []

    all_req.append(req_partner['capitalist'])
    all_req.append(req_partner['webmoney'])
    all_req.append(req_partner['qiwi'])
    all_req.append(req_partner['umoney'])
    all_req.append(req_partner['data'])
    all_req.append(req_partner['data_card_to_card'])
    all_req.append(req_partner['data_mastercard_worldwide'])
    # all_req.append(req_partner['data_ua'])
    all_req.append(req_partner['data_kz'])
    all_req.append(req_partner['usdt_erc_20'])
    all_req.append(req_partner['usdt_trc_20'])
    all_req.append(req_partner['ip_name'])
    all_req.append(req_partner['oooru_name'])

    if any(all_req):
        all_req = True
    else:
        all_req = False
    two_factor_auth = profile_info_request.get('two_factor_auth')

    if request.method == 'POST':

        if request.POST.get('type') == 'check_auth':
            two_factor_request = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/',
                {"type": "pay", "action": "get_code"})
            income_message = json.loads(two_factor_request.content).get('pay_code')
            request.session['check_tow_factor_pay'] = income_message
            return HttpResponse(json.dumps({'status': 'OK'}))

        if request.POST.get('type') == 'check_tlg_mess':
            try:
                message_user = request.POST.get('message_code')
                requests.post(
                    f'{domain_api1}/tfauth/{request.session["id"]}/',
                    json={
                        "type": "pay",
                        "action": "verify_code",
                        "pay_code": int(message_user)
                    }
                )
                if int(request.session.get('check_tow_factor_pay')) == int(message_user):
                    return HttpResponse(json.dumps({'status': 'OK'}))
                else:
                    return HttpResponse(json.dumps({'status': 'ERR'}))
            except ValueError:
                return HttpResponse(json.dumps({'status': 'ERR'}))

        sum_pay = request.POST.get('payAddSum')
        pay_info = request.POST.get('payAddType').split(';')
        pay_type = pay_info[0]
        pay_percent_partner = pay_info[1].replace(',', '.')
        pay_fix_partner = pay_info[2].replace(',', '.')
        pay_percent_system = pay_info[3].replace(',', '.')
        pay_fix_system = pay_info[4].replace(',', '.')
        type_requisites = pay_info[5]

        message = []

        try:
            sum_pay = sum_pay.replace(' ', '').replace(',', '.')
            sum_pay = round(float(sum_pay), 2)
        except ValueError:
            message = 'В поле ввода нужно вводить число'

            data = {
                'title': 'Заказ выплаты', 'page_name': 'Заказ выплаты', 'inside': inside,
                'req_partner': req_partner, 'message': message, 'all_req': all_req,
                'two_factor_auth': two_factor_auth
            }
            return render(request, 'payments-add.html', data)

        if sum_pay < 1000:
            message = ' Минимальная сумма для заказа: 1 000 '
            data = {
                'title': 'Заказ выплаты', 'page_name': 'Заказ выплаты', 'inside': inside, 'message': message,
                'req_partner': req_partner, 'all_req': all_req, 'two_factor_auth': two_factor_auth
            }
            return render(request, 'payments-add.html', data)
        elif sum_pay > float(str(request.session['balance']).replace(' ', '')):
            message = f'У вас на балансе нет {sum_pay}, введите сумму не превышающую ваш баланс {request.session["balance"]} руб.'
            data = {
                'title': 'Заказ выплаты', 'page_name': 'Заказ выплаты', 'two_factor_auth': two_factor_auth,
                'message': message, 'all_req': all_req, 'req_partner': req_partner, 'inside': inside,
            }
            return render(request, 'payments-add.html', data)
        else:
            add_type = pay_info[5]
            add_sum = float(request.POST.get('payAddSum').replace(' ', '').replace(',', '.'))

            if 'Umoney' in add_type or 'Карта РФ, RUR' in add_type or 'Qiwi' in add_type or 'Карта P2P' in add_type:
                if 'Umoney' in add_type:
                    check_payout_limit(summ=add_sum, limit=14500, partner=request.session['id'],
                                       comission=pay_percent_partner, requisites=type_requisites, fix=pay_fix_partner,
                                       selected_requisites=pay_type)
                if 'Карта РФ, RUR' in add_type:
                    check_payout_limit(summ=add_sum, limit=50000, partner=request.session['id'],
                                       comission=pay_percent_partner, requisites=type_requisites, fix=pay_fix_partner,
                                       selected_requisites=pay_type)
                if 'Qiwi' in add_type:
                    check_payout_limit(summ=add_sum, limit=15000, partner=request.session['id'],
                                       comission=pay_percent_partner, requisites=type_requisites, fix=pay_fix_partner,
                                       selected_requisites=pay_type)
                if 'Карта P2P' in add_type:
                    check_payout_limit(summ=add_sum, limit=100000, partner=request.session['id'],
                                       comission=pay_percent_partner, requisites=type_requisites, fix=pay_fix_partner,
                                       selected_requisites=pay_type)

                '''Логирование действия пользователя'''
                requests.post(
                    f'{domain_api1}/partneractions/',
                    data={
                        'act_type': 'Выплаты',
                        'manager': request.session.get('manager') if request.session.get('manager') else 0,
                        'partner': request.session['id'],
                        'ip': str(get_client_ip(request)),
                        'action': f'Сумма заказа: {add_sum}, к выплате {(float(add_sum) - float(add_sum) * float(pay_percent_partner)/100) - float(pay_fix_partner)}, Реквизиты {type_requisites}: {pay_type}',
                    }
                )
            else:
                ''' сделать пост запрос на транзакцию с отрицательной суммой '''
                transaction_req = requests.post(
                    f'{DOMAIN_API}/transactions/',
                    json.dumps(
                        {
                            'sum': 0 - sum_pay,
                            'partner_id': request.session["id"],
                            'direction': 2
                        }
                    )
                )
                transaction_info = json.loads(transaction_req.content)
                transaction_id = transaction_info.get("id")

                try:
                    requests.post(
                        f'{DOMAIN_API}/payouts/',
                        json.dumps(
                            {
                                'sum': sum_pay, 'partner_id': request.session['id'], 'selected_requisites': pay_type,
                                'comission': pay_percent_partner, 'status': 'IN_PROCESS', 'requisites': type_requisites,
                                'fix': pay_fix_partner, 'type': 'PAYMENT_REQUEST', 'transaction_id': transaction_id
                            }
                        )
                    )
                    '''Логирование действия пользователя'''
                    requests.post(
                        f'{domain_api1}/partneractions/',
                        data={
                            'act_type': 'Выплаты',
                            'manager': request.session.get('manager') if request.session.get('manager') else 0,
                            'partner': request.session['id'],
                            'ip': str(get_client_ip(request)),
                            'action': f'Сумма заказа: {add_sum}, к выплате {(float(add_sum) - float(add_sum) * float(pay_percent_partner)/100) - float(pay_fix_partner)}, Реквизиты {type_requisites}: {pay_type}',
                        }
                    )
                except:
                    sum_pay = 0
                    requests.patch(
                        f'{DOMAIN_API}/payouts/{transaction_id}/',
                        json.dumps(
                            {
                                'sum': sum_pay, 'partner_id': request.session['id'], 'selected_requisites': pay_type,
                                'comission': pay_percent_partner, 'status': 'IN_PROCESS', 'requisites': type_requisites,
                                'fix': pay_fix_partner, 'type': 'PAYMENT_REQUEST'
                            }
                        )
                    )
                    '''Логирование действия пользователя'''
                    requests.post(
                        f'{domain_api1}/partneractions/',
                        data={
                            'act_type': 'Выплаты',
                            'manager': request.session.get('manager') if request.session.get('manager') else 0,
                            'partner': request.session['id'],
                            'ip': str(get_client_ip(request)),
                            'action': f'Неудачный заказ выплаты: transaction_id = {transaction_id}',
                        }
                    )
            return redirect('payments')

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    data = {
        'title': 'Заказ выплаты', 'page_name': 'Заказ выплаты', 'inside': inside, 'req_partner': req_partner,
        'all_req': all_req, 'two_factor_auth': two_factor_auth
    }
    return render(request, 'payments-add.html', data)


@get_error
@check_profile
def news(request):
    response_news = requests.get(f'{DOMAIN_API}/news/')
    news_list = json.loads(response_news.content)

    posts = news_list
    page = set_page(request.GET)

    paginator = Paginator(posts, 3)
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': 'Новости', 'page_name': 'Новости', 'news_list': news_list, 'posts': posts
    }
    return render(request, 'news.html', data)


@get_error
@check_profile
def support(request):

    ticket_request = requests.get(f'{DOMAIN_API}/tickets/?partner_id={request.session["id"]}')
    try:
        unread_message_of_ticket = json.loads(ticket_request.content).get('messages')
        if unread_message_of_ticket is None:
            unread_message_of_ticket = []
    except:
        unread_message_of_ticket = []

    try:
        all_tickets = json.loads(ticket_request.content).get('tickets')
        if all_tickets is None:
            all_tickets = []
    except:
        all_tickets = []

    sistem_tickets = []
    partner_tickets = []

    unread_messages = {i.get('ticket_id'): i.get('count') for i in unread_message_of_ticket}
    all_tickets = all_tickets[::-1]

    for ticket in all_tickets:
        if unread_messages.get(str(ticket["id"])):
            ticket['unread_messages'] = unread_messages.get(str(ticket["id"]))
        if ticket.get('category') == 'TECHNICAL':
            ticket['category'] = 'Технический отдел'
        elif ticket.get('category') == 'FINANCIAL':
            ticket['category'] = 'Финансовый отдел'
        elif ticket.get('category') == 'PARTNERSHIP':
            ticket['category'] = 'Сотрудничество'
        else:
            ticket['category'] = 'Обращение к директору'
        if ticket.get('type') == 'IN':
            sistem_tickets.append(ticket)
        else:
            partner_tickets.append(ticket)

    if request.method == 'POST':
        if request.POST.get('type') == 'readMsg':
            ticket_id = int(request.POST.get('ticket_id'))
            requests.get(f'{DOMAIN_API}/ticketmessages/read/?ticket_id={ticket_id}')
            return HttpResponse(json.dumps({'status': 'ok'}))

        if request.POST.get('type') == 'get_messages':
            ticket_id = request.POST.get('ticket_id')
            # Запрос на АПИ1 для вывода смайликов
            requests_messages = requests.get(f'{domain_api1}/ticketmessages/?ticket_id={ticket_id}')
            response_messages = json.loads(requests_messages.content)
            requests_tickets = requests.get(f'{DOMAIN_API}/tickets/{ticket_id}')
            response_tickets = json.loads(requests_tickets.content)

            if response_tickets.get('category') == 'TECHNICAL':
                response_tickets['category'] = 'Технический отдел'
            elif response_tickets.get('category') == 'FINANCIAL':
                response_tickets['category'] = 'Финансовый отдел'
            elif response_tickets.get('category') == 'PARTNERSHIP':
                response_tickets['category'] = 'Сотрудничество'
            else:
                response_tickets['category'] = 'Обращение к директору'

            date_set = set()
            for message in response_messages:
                if dt.datetime.fromisoformat(message['date']).strftime('%d-%m-%Y') == dt.date.today().strftime(
                        '%d-%m-%Y'):
                    message['date_day'] = 'Сегодня'
                elif dt.datetime.fromisoformat(message['date']).strftime('%d-%m-%Y') == (
                        dt.date.today() - dt.timedelta(days=1)).strftime('%d-%m-%Y'):
                    message['date_day'] = 'Вчера'
                else:
                    message['date_day'] = dt.datetime.fromisoformat(message['date']).strftime('%d-%m-%Y')

                if message['date_day'] not in date_set:
                    date_set.add(message['date_day'])
                else:
                    del message['date_day']
                message['date_hour'] = dt.datetime.fromisoformat(message['date']).strftime('%H:%M:%S')

            return HttpResponse(json.dumps(
                {"messages": response_messages, "ticket": response_tickets, "user": str(request.session['user'])})
            )

        if request.POST.get('type') == 'create_ticket':
            ticket_theme = request.POST.get('theme')
            ticket_category = request.POST.get('cat')
            ticket_text = request.POST.get('text')
            ticket_type = 'OUT'
            ticket_status = 'OPEN'

            if ticket_category == '1':
                ticket_category = 'TECHNICAL'
            elif ticket_category == '2':
                ticket_category = 'FINANCIAL'
            elif ticket_category == '3':
                ticket_category = 'PARTNERSHIP'
            elif ticket_category == '4':
                ticket_category = 'DIRECTOR'

            if ticket_theme and ticket_text:
                data_ticket = {
                    "title": ticket_text[:50] + '...', "type": ticket_type, 'status': ticket_status,
                    "theme": ticket_theme, 'partner_id': request.session['id'], 'category': ticket_category
                }

                ticket = requests.post(f'{DOMAIN_API}/tickets/', json.dumps(data_ticket))

                ticket = json.loads(ticket.content)
                ticket_id = ticket.get('id')
                time_message = dt.datetime.now().strftime('%H:%M:%S')

                data_message = {
                    "text": ticket_text, "read": 0, "author_id": request.session['id'],
                    "ticket_id": ticket_id
                }

                requests.post(f'{DOMAIN_API}/ticketmessages/', json.dumps(data_message))

                return HttpResponse(
                    json.dumps({'ticket': ticket, 'user': request.session['user'], 'time_message': time_message,
                                'text': ticket_text}))
            else:
                err_msg = 'Укажите тему тикета и сообщение'
                return HttpResponse(json.dumps({'error_message': err_msg}))

        if request.POST.get('type') == 'close':
            ticket_id = request.POST.get('ticket_id')

            patch_data = {"status": "CLOSE"}

            requests.patch(f'{DOMAIN_API}/tickets/{ticket_id}/', json.dumps(patch_data))
            return HttpResponse(json.dumps({'status': 'ok'}))

        if request.POST.get('type') == 'send':
            ticket_id = request.POST.get('ticket_id')
            message = request.POST.get('message')

            message_data = {'text': message, 'read': 0, 'ticket_id': ticket_id, 'author_id': request.session['id']}
            if message == '':
                message = False
            if message == False:
                error_send = 'Перед отправкой введите сообщение'
                return HttpResponse(json.dumps({'error_send': error_send}))
            else:
                request_msg = requests.post(f'{DOMAIN_API}/ticketmessages/', json.dumps(message_data))
                response = json.loads(request_msg.content)
                new_time = dt.datetime.strptime(response.get('date'), '%Y-%m-%d %H:%M:%S')
                new_time = dt.datetime.strftime(new_time, '%H:%M:%S')
                new_date = 'Сегодня'

                return HttpResponse(json.dumps({'text': message, 'time': new_time, 'date': new_date}))

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': 'Поддержка', 'page_name': 'Поддержка', 'all_tickets': all_tickets, 'sistem_tickets': sistem_tickets,
        'partner_tickets': partner_tickets, 'user_id': str(request.session['id'])
    }
    return render(request, 'support.html', data)


@get_error
@check_profile
def referrals(request):

    profile_info_request = request.session.get('profile_info')
    session_request_subs_offers_balance(request)  # Доп данные для сессии

    '''Информация о партнере с его реф ссылкой и реф отчислениями'''
    profile_info_request['ref_link'] = encode(int(request.session["id"]) + 1000000, BASE62)

    '''Информация по рефералам партнера'''
    profit_from_referals = 0
    refer_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/referals/').content)
    for ref in refer_info:
        '''для правильного отображения суммы отчислений с реферала'''
        if ref.get('amount'):
            profit_from_referals += ref['amount']
        else:
            ref['amount'] = 0
        '''Скрываю информацию рефералов'''
        ref['email'] = f'{ref["email"][:3]}****{ref["email"][ref["email"].find("@"):]}'

    data = {
        'title': 'Реферальная система', 'page_name': 'Реферальная система', 'profit_from_referals': profit_from_referals,
        'refer_info': refer_info, 'profile_info': profile_info_request
    }
    return render(request, 'referrals.html', data)


@get_error
@check_profile
def top_webs(request):

    profile_info_request = request.session.get('profile_info')

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    try:
        contest_info = json.loads(requests.get(f'{domain_api1}/contest/').content)
    except:
        contest_info = []

    data = {
        'title': 'ТОП Конкурса', 'page_name': 'ТОП Конкурса', 'profile_info': profile_info_request,
        'user_id': int(request.session['id']), 'contest_info': contest_info
    }
    return render(request, 'top-webs.html', data)


def ban_page(request):
    data = {'title': 'Ваш аккаунт заблокирован'}
    return render(request, 'ban-web.html', data)


@get_error
@auth_block
def lock_page(request):
    try:
        profile_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)
    except:
        profile_info = json.loads(requests.get(f'{domain_api1}/partners/{request.session["id"]}/').content)

    if profile_info.get('telegram_id'):
        request.session['telegram_id'] = profile_info.get('telegram_id')

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    '''Для подтверждения Telegram_id'''
    time_for_h = str(dt.datetime.now().timestamp()).split('.')[0][:-3]
    md5_hash = md5(f'{request.session["id"]}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d_{time_for_h}'.encode()).hexdigest()

    data = {
        'title': 'Привязка Telegram аккаунта', 'profile_info': profile_info,
        'md5_hash': md5_hash, 'page_name': 'Доступ ограничен', 'lock_page': 'lock_page'
    }
    return render(request, 'lock-page.html', data)


def forgot(request):
    if request.session.get('user'):
        return redirect('profile')

    if request.method == 'POST':
        if request.POST.get('type') == 'forgot_pwd':
            email = request.POST.get('email')
            user = requests.post(f'{domain_api1}/partners/find/', json={"email": email})
            user_information = json.loads(user.content)
            if user_information.get('id'):
                request.session['id'] = user_information.get('id')
                requests.post(
                    f'{domain_api1}/tfauth/{user_information.get("id")}/',
                    {
                        "type": "password",
                        "action": "get_code"
                    }
                )
                return HttpResponse(user)
            else:
                return HttpResponse(json.dumps(user_information))

        if request.POST.get('type') == 'totfa_password_check_code':
            data = {
                "type": "password",
                "action": "verify_code",
                "password_code": int(request.POST.get('message_code'))
            }
            passwd_request_verify = requests.post(
                f'{domain_api1}/tfauth/{request.session["id"]}/', json=data
            )
            return HttpResponse(passwd_request_verify)

        if request.POST.get('type') == 'change_pwd':
            new_password = request.POST.get('new_pwd_post')
            '''Отправка нового пароля для смены текущего'''
            requests.patch(
                f'{DOMAIN_API}/partners/{request.session["id"]}/',
                json.dumps({'password': new_password})
            )
            return HttpResponse(json.dumps({'status': 'OK'}))

    data = {'title': 'Восстановление пароля'}
    return render(request, 'forgot.html', data)


def logout(request):
    request.session.flush()
    return redirect('login')


def page_not_found(request, exception):
    return render(request, '404.html')


def handler500(request, exception=None):
    return render(request, '500.html', {})


def handler501(request, exception=None):
    return render(request, '501.html', {})
