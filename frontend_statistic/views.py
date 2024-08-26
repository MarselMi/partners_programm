import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from datetime import date
from frontend.functions import *
import math


@get_error
@check_profile
def empty_page(request):
    '''страничка для вывода общей статистики по основным параметрам'''
    try:
        profile_info = json.loads(requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/').content)
    except:
        profile_info = json.loads(requests.get(f'{domain_api1}/partners/{request.session["id"]}/').content)

    '''Участие в конкурсе'''
    request.session['contest'] = profile_info.get('contest_check')
    request.session['telegram_id'] = profile_info.get('telegram_id')

    if profile_info.get('user_is_active'):
        request.session["user_is_active"] = False
        request.session['ban_web'] = False
    else:
        request.session["user_is_active"] = True
        request.session['ban_web'] = True

    date_before_eight_day_datetime = date.today() - timedelta(days=7)
    date_before_eight_day = date_before_eight_day_datetime.strftime("%d.%m.%Y")

    api2_date = date_for_api2.sub(r'\3-\2-\1', date_before_eight_day)
    '''запрос для статистики по дням, для получения инф за 7 дней'''
    try:
        response_seven_days_api2 = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/', json.dumps({"stat": "Days"}))
        gen_seven_days_stat_api2 = json.loads(response_seven_days_api2.text).get('days')[::-1]
        gen_seven_days_stat = dict()
        general_day_stat(gen_seven_days_stat, gen_seven_days_stat_api2)
        '''Для вывода последней строки информации по процентам в стате по дням'''
        response_for_percent_api2 = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
                                                  json.dumps({"stat": "Days", "start": api2_date, "end": api2_date}))
        info_for_percent_statistic_api2 = json.loads(response_for_percent_api2.text).get('days')
        info_for_percent_statistic = dict()
        general_last_day_stat(info_for_percent_statistic, info_for_percent_statistic_api2)
    except:
        response_seven_days = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/', {'stat': 'Days'})
        gen_seven_days_stat = json.loads(response_seven_days.content).get('days')
        '''Для вывода последней строки процентов'''
        response_for_percent = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/',
                                             {"stat": "Days", "start": date_before_eight_day,
                                              "end": date_before_eight_day})
        info_for_percent_statistic = json.loads(response_for_percent.content).get('days')

    '''Почасовая статистика'''
    try:
        date_today = datetime.today().strftime('%Y-%m-%d')
        date_yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        '''сегодня'''
        response_by_hours_today_api2 = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
            json.dumps({'stat': 'Hours', "end": date_today, "start": date_today})
        )
        gen_hours_stat_today_api2 = json.loads(response_by_hours_today_api2.text).get('hours')
        '''вчера'''
        response_by_hours_yesterday_api2 = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
            json.dumps({'stat': 'Hours', "start": date_yesterday, "end": date_yesterday})
        )
        gen_hours_stat_yesterday_api2 = json.loads(response_by_hours_yesterday_api2.text).get('hours')
        '''список для часов сегодня/вчера'''
        hour_now = datetime.now().hour
        hours_stat_today = []
        hours_stat_yesterday = []
        '''сегодня'''
        get_hour_general_stat(gen_hours_stat_today_api2, hour=hour_now, date=date_today,  list_result=hours_stat_today)
        '''вчера'''
        get_hour_general_stat(gen_hours_stat_yesterday_api2, hour=23, date=date_yesterday, list_result=hours_stat_yesterday)
    except:
        response_by_hours = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/', {'stat': 'Hours'})
        gen_hours_stat = json.loads(response_by_hours.content).get('hours')
        '''Данные Сегодняшней (текущей) статистики по часам ДЛЯ ПОЧАСОВОЙ СТАТИСТИКИ'''
        hours_stat_today = []
        if gen_hours_stat.get(list(gen_seven_days_stat.keys())[0]):
            for hours, activate in gen_hours_stat.get(list(gen_seven_days_stat.keys())[0]).items():
                hours_stat_today.insert(0, activate.get('activations'))
        while len(hours_stat_today) != 24:
            '''Заполняю список до len=24 для корректного отображения'''
            hours_stat_today.append(0)
        '''Данные вчерашней статистики по часам ДЛЯ ПОЧАСОВОЙ СТАТИСТИКИ'''
        hours_stat_yesterday = []
        if gen_hours_stat.get(list(gen_seven_days_stat.keys())[1]):
            for hours, activate in gen_hours_stat.get(list(gen_seven_days_stat.keys())[1]).items():
                hours_stat_yesterday.insert(0, activate.get('activations'))

    '''Данные для отображения Потоков'''
    try:
        request_streams = requests.get(f'{DOMAIN_API}/streams/?partner_id={request.session["id"]}')
        response_streams = json.loads(request_streams.content).get('streams')[::-1]
    except:
        '''Данные для отображения Потоков'''
        request_streams = requests.get(f'{domain_api1}/streams/?partner_id={request.session["id"]}')
        response_streams = json.loads(request_streams.content).get('results')[::-1]

    '''Данные для отображения транзакции'''
    try:
        response_transactions = requests.get(f'{DOMAIN_API}/partners/{request.session["id"]}/transactions/')
        transactions = json.loads(response_transactions.content)
    except:
        response_transactions = requests.get(f'{domain_api1}/partners/{request.session["id"]}/transactions/')
        transactions = json.loads(response_transactions.content)

    '''Ошибки транзакций'''
    error_dict = json.loads(requests.get(f'{domain_api1}/transactionerrors/?limit=1000').content).get('results')

    '''По транзакциям'''
    if transactions:
        for transaction in transactions:
            if transaction.get('card'):
                transaction['card'] = transaction.get('card').replace('xxxxx', '*')
            for key, value in BANKS.items():
                if transaction['bank'] == key:
                    transaction['bank'] = value
            if transaction.get('status') == 'Declined':
                try:
                    d = list(filter(lambda a: a.get('code') == int(transaction.get('error')), error_dict))
                    try:
                        transaction['error'] = d[0].get('name')
                    except IndexError:
                        transaction['error'] = 'Неизвестная ошибка'
                except ValueError:
                    pass

    '''Постбеки клиента'''
    try:
        request_postbacks = requests.get(f'{DOMAIN_API}/postbacks/?partner_id={request.session["id"]}')
        postbacks = json.loads(request_postbacks.content).get('postbacks')
        if len(postbacks) > 7:
            '''вывод 7 записей'''
            postbacks = postbacks[:7]
        get_postback(postbacks)
    except:
        request_postbacks = requests.get(f'{domain_api1}/postbacks/?partner_id={request.session["id"]}')
        response_postbacks = json.loads(request_postbacks.content).get('results')
        postbacks = response_postbacks[::-1]

    '''Списки для хранения инф за 7 дней '''
    hosts = []
    registrations = []
    activations = []
    subscribes = []
    rebills = []
    unsubscribes = []
    profit = []
    bad_rebills = []

    '''цикл для заполнения соответствующих списков данными по статистики'''
    for key, val in gen_seven_days_stat.items():
        hosts.append(val.get('hosts'))
        registrations.append(val.get('registrations'))
        activations.append(val.get('activations'))
        subscribes.append(val.get('subscribes'))
        rebills.append(val.get('rebills'))
        unsubscribes.append(val.get('unsubscribes'))
        profit.append(val.get('profit'))
        bad_rebills.append((val.get('bad_rebills')))

    ''' Списки для вывода процентов за 7 дней'''
    hosts_for_perc = hosts.copy()
    registrations_for_perc = registrations.copy()
    activations_for_perc = activations.copy()
    subscribes_for_perc = subscribes.copy()
    rebills_for_perc = rebills.copy()
    unsubscribes_for_perc = unsubscribes.copy()
    profit_for_perc = profit.copy()
    bad_rebills_for_perc = bad_rebills.copy()

    '''Добавляю данные для подсчета крайней строки вывода процентов'''
    for keys, val in info_for_percent_statistic.items():
        hosts_for_perc.append(val.get('hosts'))
        registrations_for_perc.append(val.get('registrations'))
        activations_for_perc.append(val.get('activations'))
        subscribes_for_perc.append(val.get('subscribes'))
        rebills_for_perc.append(val.get('rebills'))
        unsubscribes_for_perc.append(val.get('unsubscribes'))
        profit_for_perc.append(val.get('profit'))
        bad_rebills_for_perc.append(val.get('bad_rebills'))

    '''подсчет процентов для таблицы Статистики за 7 дней'''
    hosts_proc = get_percents_list(hosts_for_perc)
    registr_proc = get_percents_list(registrations_for_perc)
    activ_proc = get_percents_list(activations_for_perc)
    subsc_proc = get_percents_list(subscribes_for_perc)
    rebills_proc = get_percents_list(rebills_for_perc)
    unsub_proc = get_percents_list(unsubscribes_for_perc)
    prof_proc = get_percents_list(profit_for_perc)
    bad_reb_proc = get_percents_list(bad_rebills_for_perc)

    '''данные для вывода значения ВСЕГО за 7 дней'''
    sum_stat = {
        'sum_hosts': sum(hosts), 'sum_registrations': sum(registrations), 'sum_activations': sum(activations),
        'sum_subscribes': sum(subscribes), 'sum_rebills': sum(rebills), 'sum_unsubscribes': sum(unsubscribes),
        'sum_profit': sum(profit), 'sum_bad_rebills': sum(bad_rebills)
    }

    '''ОБЩАЯ СТАТИСТИКА сверху странички за день'''
    today = datetime.today().strftime("%d.%m.%Y")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%d.%m.%Y")

    try:
        stat_rebills = (gen_seven_days_stat.get(today)).get('rebills')
        stat_subscribes = (gen_seven_days_stat.get(today)).get('subscribes')
        stat_activations = (gen_seven_days_stat.get(today)).get('activations')
        stat_registrations = (gen_seven_days_stat.get(today)).get('registrations')
    except AttributeError:
        stat_rebills = 0
        stat_subscribes = 0
        stat_activations = 0
        stat_registrations = 0

    '''Вчерашняя статистика для подсчета флажков по процентам ОБЩАЯ СТАТИСТИКА сверху странички'''
    try:
        yestarday_reb_stat = gen_seven_days_stat.get(yesterday).get('rebills')
        yestarday_sub_stat = gen_seven_days_stat.get(yesterday).get('subscribes')
        yestarday_act_stat = gen_seven_days_stat.get(yesterday).get('activations')
        yestarday_reg_stat = gen_seven_days_stat.get(yesterday).get('registrations')
    except AttributeError:
        yestarday_reb_stat = 0
        yestarday_sub_stat = 0
        yestarday_act_stat = 0
        yestarday_reg_stat = 0

    general_stat = {
        'stat_rebills': stat_rebills, 'stat_registrations': stat_registrations,
        'stat_activations': stat_activations, 'stat_subscribes': stat_subscribes
    }

    '''подсчет процентов для ОБЩЕЙ СТАТИСТИКИ сверху странички '''
    dif_reb_stat = getting_percent(stat_rebills, yestarday_reb_stat)
    dif_sub_stat = getting_percent(stat_subscribes, yestarday_sub_stat)
    dif_act_stat = getting_percent(stat_activations, yestarday_act_stat)
    dif_reg_stat = getting_percent(stat_registrations, yestarday_reg_stat)

    i = 0
    '''Цикл для добавления полученных данных в основной словарь со статистикой'''
    for key, val in gen_seven_days_stat.items():
        if i < len(hosts_proc):
            gen_seven_days_stat[key].setdefault('hosts_proc', hosts_proc[i])
            gen_seven_days_stat[key].setdefault('registr_proc', registr_proc[i])
            gen_seven_days_stat[key].setdefault('activ_proc', activ_proc[i])
            gen_seven_days_stat[key].setdefault('subsc_proc', subsc_proc[i])
            gen_seven_days_stat[key].setdefault('rebills_proc', rebills_proc[i])
            gen_seven_days_stat[key].setdefault('unsub_proc', unsub_proc[i])
            gen_seven_days_stat[key].setdefault('prof_proc', prof_proc[i])
            gen_seven_days_stat[key].setdefault('bad_rebills_proc', bad_reb_proc[i])
        i += 1

    '''вывод подсчитанных процентов для Верхней Статистики'''
    dif = {
        'dif_reb_stat': dif_reb_stat, 'dif_sub_stat': dif_sub_stat,
        'dif_act_stat': dif_act_stat, 'dif_reg_stat': dif_reg_stat
    }

    '''сокращаю и вывожу крайние 7 записей'''
    streams = response_streams[::-1]
    if len(streams) > 7:
        '''вывод 7 записей'''
        streams = streams[:7]
    for stream in streams:
        stream['uid'] = encode(int(stream['uid']), BASE62)

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    '''Общие данные для вывода в шаблон'''
    data = {
        'title': 'Главная страница', 'page_name': 'Общая', 'sum_stat': sum_stat, 'dif': dif,
        'gen_seven_days_stat': gen_seven_days_stat, 'general_stat': general_stat,
        'transactions': transactions, 'hours_stat_today': hours_stat_today,
        'hours_stat_yesterday': hours_stat_yesterday,'postbacks': postbacks, 'streams': streams,
    }
    return render(request, 'stats-general.html', data)


@get_error
@check_profile
def stat_days(request):
    col = request.session.get('collapsed_days')
    if not col:
        request.session['collapsed_days'] = 2

    date_nows = date.today()
    date_before_seven_days = date_nows - timedelta(days=6)
    if request.GET.get("start") == None:
        date_for_api2_perc = (date_before_seven_days - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        date_for_api2_perc = (
                    datetime.strptime(request.GET.get("start"), "%d.%m.%Y") - timedelta(days=1)).strftime(
            "%Y-%m-%d")

    date_before_seven_day = date_before_seven_days.strftime("%d.%m.%Y")
    date_now = date_nows.strftime("%d.%m.%Y")

    collapse(request, 'collapsed_days')

    filter_get = dict(request.GET)
    filter_dict = {}

    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict(filter_dict, filter_get)

    if filter_dict.get('stream_id'):
        check_and_request_filter(request, filter_dict, 'stream_id', "Stream")
    if filter_dict.get('offer_id'):
        check_and_request_filter(request, filter_dict, 'offer_id', "Offer")
    if filter_dict.get('landing_id'):
        check_and_request_filter(request, filter_dict, 'landing_id', "Landing")
    if filter_dict.get('country'):
        check_and_request_filter(request, filter_dict, 'country', "Country")
    if filter_dict.get('os'):
        check_and_request_filter(request, filter_dict, 'os', "OS")
    if filter_dict.get('browser'):
        check_and_request_filter(request, filter_dict, 'browser', "Browser")
    if filter_dict.get('ref_domain'):
        check_and_request_filter(request, filter_dict, 'ref_domain', "RefDomain")

    if request.method == 'POST':
        if request.POST.get('type') == 'stream_id':
            return HttpResponse(post_filter(request.session, "Stream", 'stream_id'))
        if request.POST.get('type') == 'landing_id':
            return HttpResponse(post_filter(request.session, "Landing", 'landing_id'))
        if request.POST.get('type') == 'offer_id':
            return HttpResponse(post_filter(request.session, "Offer", 'offer_id'))
        if request.POST.get('type') == 'country':
            return HttpResponse(post_filter(request.session, "Country", 'country'))
        if request.POST.get('type') == 'os':
            return HttpResponse(post_filter(request.session, "OS", 'os'))
        if request.POST.get('type') == 'browser':
            return HttpResponse(post_filter(request.session, "Browser", 'browser'))
        if request.POST.get('type') == 'ref_domain':
            return HttpResponse(post_filter(request.session, "RefDomain", 'ref_domain'))

    filter_dict['stat'] = 'Days'

    '''Для подсчета крайней строки процентов создаю копию основного словаря запроса по фильтрам'''
    filter_last_day = filter_dict.copy()

    '''Задаю параметры минус один от основного запроса'''
    filter_last_day["start"] = date_for_api2_perc
    filter_last_day["end"] = date_for_api2_perc
    start_for_pesc = datetime.strptime(date_for_api2_perc, '%Y-%m-%d')
    start_day = datetime.today() - timedelta(days=7)
    end_day = datetime.today()
    if filter_dict.get('start'):
        start_day = datetime.strptime(filter_dict['start'], '%d.%m.%Y') - timedelta(days=1)
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
    if filter_dict.get('end'):
        end_day = datetime.strptime(filter_dict.get('end'), '%d.%m.%Y')
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%d.%m.%Y').strftime('%Y-%m-%d')

    try:
        response_by_days = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
            json.dumps(filter_dict))
        '''Данные для вывода статистики в таблицу'''
        days_stat_request = json.loads(response_by_days.text).get('days')
        days_stat = dict()
        general_day_stat(days_stat, days_stat_request, daystart=start_day, end_day=end_day)
    except:
        if filter_dict.get('start'):
            filter_dict['start'] = date_for_api1.sub(r'\3.\2.\1', filter_dict.get('start'))
        if filter_dict.get('end'):
            filter_dict['end'] = date_for_api1.sub(r'\3.\2.\1', filter_dict.get('end'))
        response_by_days = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/',
                                         filter_dict)
        days_stat = json.loads(response_by_days.content).get('days')

    '''параметры для выбора фильтра'''
    data_params = json.loads(response_by_days.content).get('used_filters')

    try:
        request_last_day = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
            json.dumps(filter_last_day))
        response_last_days = json.loads(request_last_day.text).get("days")
        response_last_day = dict()
        days_general_stat(response_last_day, response_last_days, date_for_api2_perc)
    except:
        if filter_last_day.get('start'):
            filter_last_day['start'] = date_for_api1.sub(r'\3.\2.\1', filter_last_day.get('start'))
        if filter_last_day.get('end'):
            filter_last_day['end'] = date_for_api1.sub(r'\3.\2.\1', filter_last_day.get('end'))
        request_last_day = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/',
                                         filter_last_day)
        response_last_day = json.loads(request_last_day.text).get("days")

    if filter_dict.get('start'):
        try:
            filter_dict['start'] = date_for_api2.sub(r'\3-\2-\1', filter_dict['start'])
        except:
            filter_dict['start'] = filter_dict.get('start')
    if filter_dict.get('end'):
        try:
            filter_dict['end'] = date_for_api2.sub(r'\3-\2-\1', filter_dict['end'])
        except:
            filter_dict['end'] = filter_dict.get('end')

    '''списки с данными по статистики для вывода на таблице'''
    hosts = []
    registrations = []
    activations = []
    subscribes = []
    rebills = []
    unsubscribes = []
    profit = []
    convert_host_reg = []
    convert_reg_act = []

    '''подсчет ВСЕГО для таблицы статуса'''
    for key, item in days_stat.items():
        host = item.get('hosts')
        registr = item.get('registrations')
        activ = item.get('activations')
        hosts.append(host)
        registrations.append(registr)
        activations.append(item.get('activations'))
        subscribes.append(item.get('subscribes'))
        rebills.append(item.get('rebills'))
        unsubscribes.append(item.get('unsubscribes'))
        profit.append(item.get('profit'))
        convert_host_reg.append(convert_calculate(host, registr))
        convert_reg_act.append(convert_calculate(registr, activ))

    '''списки для вывода процентов'''
    hosts_for_perc = hosts.copy()
    registrations_for_perc = registrations.copy()
    activations_for_perc = activations.copy()
    subscribes_for_perc = subscribes.copy()
    rebills_for_perc = rebills.copy()
    unsubscribes_for_perc = unsubscribes.copy()
    profit_for_perc = profit.copy()
    convert_host_reg_for_perc = convert_host_reg.copy()
    convert_reg_act_for_perc = convert_reg_act.copy()

    '''Добавляю данные для подсчета процентов крайнего дня'''
    for key, item in response_last_day.items():
        host = item.get('hosts')
        registr = item.get('registrations')
        activ = item.get('activations')
        hosts_for_perc.append(host)
        registrations_for_perc.append(registr)
        activations_for_perc.append(item.get('activations'))
        subscribes_for_perc.append(item.get('subscribes'))
        rebills_for_perc.append(item.get('rebills'))
        unsubscribes_for_perc.append(item.get('unsubscribes'))
        profit_for_perc.append(item.get('profit'))
        convert_host_reg_for_perc.append(convert_calculate(host, registr))
        convert_reg_act_for_perc.append(convert_calculate(registr, activ))

    '''итоговая сумма полученных статистикой'''
    sum_hosts = sum(hosts)
    sum_registrations = sum(registrations)
    sum_activations = sum(activations)
    sum_subscribes = sum(subscribes)
    sum_rebills = sum(rebills)
    sum_unsubscribes = sum(unsubscribes)
    sum_profit = sum(profit)
    sum_convert_reg_act = convert_calculate(sum_registrations, sum_activations)
    sum_convert_host_reg = convert_calculate(sum_hosts, sum_registrations)

    '''Статистика подсчета процентов за выбранный период'''
    hosts_proc = get_percents_list(hosts_for_perc)
    registr_proc = get_percents_list(registrations_for_perc)
    activ_proc = get_percents_list(activations_for_perc)
    subsc_proc = get_percents_list(subscribes_for_perc)
    rebills_proc = get_percents_list(rebills_for_perc)
    unsub_proc = get_percents_list(unsubscribes_for_perc)
    prof_proc = get_percents_list(profit_for_perc)
    convert_host_reg_proc = get_percents_list(convert_host_reg_for_perc)
    convert_reg_act_proc = get_percents_list(convert_reg_act_for_perc)

    k = 0
    '''Добавляю конверт в словарь, для отображения в статистике'''
    for key, val in days_stat.items():
        if k < len(convert_reg_act):
            days_stat[key].setdefault('convert_reg_act', convert_reg_act[k])
            days_stat[key].setdefault('convert_host_reg', convert_host_reg[k])
            k += 1

    i = 0
    '''Цикл для добавления полученных данных в основной словарь со статистикой'''
    for key, val in days_stat.items():
        if i < len(hosts_proc):
            days_stat[key].setdefault('hosts_proc', hosts_proc[i])
            days_stat[key].setdefault('registr_proc', registr_proc[i])
            days_stat[key].setdefault('conv_proc', registr_proc[i])
            days_stat[key].setdefault('activ_proc', activ_proc[i])
            days_stat[key].setdefault('subsc_proc', subsc_proc[i])
            days_stat[key].setdefault('rebills_proc', rebills_proc[i])
            days_stat[key].setdefault('unsub_proc', unsub_proc[i])
            days_stat[key].setdefault('prof_proc', prof_proc[i])
            days_stat[key].setdefault('convert_host_reg_proc', convert_host_reg_proc[i])
            days_stat[key].setdefault('convert_reg_act_proc', convert_reg_act_proc[i])
        i += 1

    '''для вывода итогового значения ВСЕГО'''
    sum_stat = {
        'sum_hosts': sum_hosts, 'sum_registrations': sum_registrations, 'sum_convert_host_reg': sum_convert_host_reg,
        'sum_subscribes': sum_subscribes, 'sum_rebills': sum_rebills, 'sum_unsubscribes': sum_unsubscribes,
        'sum_profit': sum_profit, 'sum_convert_reg_act': sum_convert_reg_act, 'sum_activations': sum_activations
    }

    show_button = False
    if request.GET:
        show_button = True

    collapsed = request.session.get('collapsed_days')
    session_request_subs_offers_balance(request)  # Доп данные для сессии
    try:
        filter_dict['start'] = date_for_api1.sub(r'\1.\2.\3', filter_dict['start'])
        filter_dict['end'] = date_for_api1.sub(r'\1.\2.\3', filter_dict['end'])
    except:
        pass
    data = {
        'title': 'Статистика по дням', 'page_name': 'Статистика по дням', "show_button": show_button,
        'sum_stat': sum_stat, 'days_stat': days_stat, 'start_seven': date_before_seven_day,
        'date_now': date_now, 'req_data': filter_dict, 'data_params': data_params,
        'collapsed': collapsed, 'data_filter': filter_get
    }
    return render(request, 'stats-days.html', data)


@get_error
@check_profile
def stat_hours(request):
    '''Сатистика по часам'''
    col = request.session.get('collapsed_hours')
    if not col:
        request.session['collapsed_hours'] = 2

    collapse(request, 'collapsed_hours')

    date_now = date.today().strftime("%d.%m.%Y")

    filter_get = dict(request.GET)
    filter_dict = {}
    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict(filter_dict, filter_get)

    if request.method == 'POST':
        if request.POST.get('type') == 'stream_id':
            return HttpResponse(post_filter(request.session, "Stream", 'stream_id'))
        if request.POST.get('type') == 'landing_id':
            return HttpResponse(post_filter(request.session, "Landing", 'landing_id'))
        if request.POST.get('type') == 'offer_id':
            return HttpResponse(post_filter(request.session, "Offer", 'offer_id'))
        if request.POST.get('type') == 'country':
            return HttpResponse(post_filter(request.session, "Country", 'country'))
        if request.POST.get('type') == 'os':
            return HttpResponse(post_filter(request.session, "OS", 'os'))
        if request.POST.get('type') == 'browser':
            return HttpResponse(post_filter(request.session, "Browser", 'browser'))
        if request.POST.get('type') == 'ref_domain':
            return HttpResponse(post_filter(request.session, "RefDomain", 'ref_domain'))

    if filter_dict.get('stream_id'):
        check_and_request_filter(request, filter_dict, 'stream_id', "Stream")
    if filter_dict.get('offer_id'):
        check_and_request_filter(request, filter_dict, 'offer_id', "Offer")
    if filter_dict.get('landing_id'):
        check_and_request_filter(request, filter_dict, 'landing_id', "Landing")
    if filter_dict.get('country'):
        check_and_request_filter(request, filter_dict, 'country', "Country")
    if filter_dict.get('os'):
        check_and_request_filter(request, filter_dict, 'os', "OS")
    if filter_dict.get('browser'):
        check_and_request_filter(request, filter_dict, 'browser', "Browser")
    if filter_dict.get('ref_domain'):
        check_and_request_filter(request, filter_dict, 'ref_domain', "RefDomain")

    '''Для правильного отображения при переходе на страницу задаю start и end'''
    if request.GET.get('start') is None:
        filter_dict['start'] = date_now
        filter_dict['end'] = date_now
    else:
        filter_dict['end'] = request.GET.get('start')

    filter_dict['stat'] = 'Hours'
    filter_last_line = filter_dict.copy()
    filter_last_line['start'] = (datetime.strptime(filter_dict.get('start'), "%d.%m.%Y").date() - timedelta(days=1)).strftime("%d.%m.%Y")
    filter_last_line['end'] = filter_last_line.get('start')

    '''списки с данными по статистике полчуенные с API'''
    list_hosts = []
    list_registrations = []
    list_activations = []
    list_subscribes = []
    list_rebills = []
    list_unsubscribes = []
    list_profit = []
    list_convert_host_reg = []
    list_convert_reg_act = []

    '''Запрос с на API для получения статистики согласно примененых фильтров'''
    try:
        filter_dict['start'] = date_for_api2.sub(r'\3-\2-\1', filter_dict['start'])
        filter_dict['end'] = date_for_api2.sub(r'\3-\2-\1', filter_dict['end'])
        response_by_hours = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/', json.dumps(filter_dict))

        hours_stats = json.loads(response_by_hours.text).get('hours')
        hours_stat = dict()
        data_params = json.loads(response_by_hours.text).get('used_filters')
        hour_now = datetime.now().hour

        '''Проверяю на какой день выбрана статистика'''
        if filter_dict['start'] == datetime.today().strftime('%Y-%m-%d'):
            for key in reversed(range(hour_now + 1)):
                hours_stat.setdefault(key, {
                    'hosts': 0,
                    'registrations': 0,
                    'activations': 0,
                    'subscribes': 0,
                    'unsubscribes': 0,
                    'profit': 0,
                    'income': 0,
                    'rebills': 0,
                    'bad_rebills': 0
                })
        else:
            for key in reversed(range(24)):
                hours_stat.setdefault(key, {
                    'hosts': 0,
                    'registrations': 0,
                    'activations': 0,
                    'subscribes': 0,
                    'unsubscribes': 0,
                    'profit': 0,
                    'income': 0,
                    'rebills': 0,
                    'bad_rebills': 0
                })

        for key in hours_stats:
            try:
                if key['day'] == filter_dict['start']:
                    hours_stat[key['hour']][key['model']] = key['count']
            except KeyError:
                pass

        '''Запрос для вывода данных с процентом для крайней строки'''
        filter_last_line['start'] = datetime.strptime(filter_last_line['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
        filter_last_line['end'] = datetime.strptime(filter_last_line['end'], '%d.%m.%Y').strftime('%Y-%m-%d')
        request_last_line = requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/',
                                          json.dumps(filter_last_line))
        response_last_line = json.loads(request_last_line.text).get('hours')

        last_line_info = {23: {
            'hosts': 0,
            'registrations': 0,
            'activations': 0,
            'subscribes': 0,
            'unsubscribes': 0,
            'profit': 0,
            'income': 0,
            'rebills': 0,
            'bad_rebills': 0}
        }

        for key in response_last_line:
            if key['hour'] == 23:
                last_line_info[23][key['model']] = key['count']

        '''наполнение списков по статистике'''
        for key in (range(len(hours_stat))):
            host = hours_stat[key].get('hosts')
            register = hours_stat[key].get('registrations')
            activ = hours_stat[key].get('activations')
            list_hosts.append(hours_stat[key].get('hosts'))
            list_registrations.append(hours_stat[key].get('registrations'))
            list_activations.append(hours_stat[key].get('activations'))
            list_subscribes.append(hours_stat[key].get('subscribes'))
            list_rebills.append(hours_stat[key].get('rebills'))
            list_unsubscribes.append(hours_stat[key].get('unsubscribes'))
            list_profit.append(hours_stat[key].get('profit'))
            list_convert_host_reg.append(convert_calculate(host, register))
            list_convert_reg_act.append(convert_calculate(register, activ))

        '''Списки для вывода процентов'''
        list_hosts_for_perc = list_hosts.copy()
        list_registrations_for_perc = list_registrations.copy()
        list_activations_for_perc = list_activations.copy()
        list_subscribes_for_perc = list_subscribes.copy()
        list_rebills_for_perc = list_rebills.copy()
        list_unsubscribes_for_perc = list_unsubscribes.copy()
        list_profit_for_perc = list_profit.copy()
        list_convert_host_reg_for_perc = list_convert_host_reg.copy()
        list_convert_reg_act_for_perc = list_convert_reg_act.copy()

        '''Добавляю данные для подсчета процентов крайнего часа'''
        for key, item in last_line_info.items():
            host = item.get('hosts')
            registr = item.get('registrations')
            activ = item.get('activations')
            list_hosts_for_perc.insert(0, item.get('hosts'))
            list_registrations_for_perc.insert(0, item.get('registrations'))
            list_activations_for_perc.insert(0, item.get('activations'))
            list_subscribes_for_perc.insert(0, item.get('subscribes'))
            list_rebills_for_perc.insert(0, item.get('rebills'))
            list_unsubscribes_for_perc.insert(0, item.get('unsubscribes'))
            list_profit_for_perc.insert(0, item.get('profit'))
            list_convert_host_reg_for_perc.insert(0, convert_calculate(host, registr))
            list_convert_reg_act_for_perc.insert(0, convert_calculate(registr, activ))

        '''итоговая сумма полученных статистикой'''
        sum_hosts = sum(list_hosts)
        sum_registrations = sum(list_registrations)
        sum_activations = sum(list_activations)
        sum_subscribes = sum(list_subscribes)
        sum_rebills = sum(list_rebills)
        sum_unsubscribes = sum(list_unsubscribes)
        sum_profit = sum(list_profit)
        sum_convert_reg_act = convert_calculate(sum_registrations, sum_activations)
        sum_convert_host_reg = convert_calculate(sum_hosts, sum_registrations)

        '''список с данными для флажков по процетнам соотношение вчера/сегодня'''
        hosts_proc_list = get_percents_list_hour(list_hosts_for_perc)
        registr_proc_list = get_percents_list_hour(list_registrations_for_perc)
        activ_proc_list = get_percents_list_hour(list_activations_for_perc)
        subsc_proc_list = get_percents_list_hour(list_subscribes_for_perc)
        rebills_proc_list = get_percents_list_hour(list_rebills_for_perc)
        unsub_proc_list = get_percents_list_hour(list_unsubscribes_for_perc)
        prof_proc_list = get_percents_list_hour(list_profit_for_perc)
        convert_reg_act_proc_list = get_percents_list_hour(list_convert_reg_act_for_perc)
        convert_host_reg_proc_list = get_percents_list_hour(list_convert_host_reg_for_perc)

        p = 0  # счетчик
        k = 0  # счетчик
        '''Добавляю конверт в словарь, для отображения в статистике
        Цикл для добавления полученных данных в основной словарь со статистикой'''
        for key in range(len(hours_stat)):
            if k < len(list_convert_reg_act):
                hours_stat[key].setdefault('convert_reg_act', list_convert_reg_act[k])
                hours_stat[key].setdefault('convert_host_reg', list_convert_host_reg[k])
                k += 1
            if p < len(hosts_proc_list):
                hours_stat[key].setdefault('hosts_proc', hosts_proc_list[p])
                hours_stat[key].setdefault('registr_proc', registr_proc_list[p])
                hours_stat[key].setdefault('conv_proc', registr_proc_list[p])
                hours_stat[key].setdefault('activ_proc', activ_proc_list[p])
                hours_stat[key].setdefault('subsc_proc', subsc_proc_list[p])
                hours_stat[key].setdefault('rebills_proc', rebills_proc_list[p])
                hours_stat[key].setdefault('unsub_proc', unsub_proc_list[p])
                hours_stat[key].setdefault('prof_proc', prof_proc_list[p])
                hours_stat[key].setdefault('convert_reg_act_proc', convert_reg_act_proc_list[p])
                hours_stat[key].setdefault('convert_host_reg_proc', convert_host_reg_proc_list[p])
            p += 1

        '''для вывода итогового значения ВСЕГО'''
        sum_stat = {
            'sum_hosts': sum_hosts, 'sum_registrations': sum_registrations, 'sum_activations': sum_activations,
            'sum_subscribes': sum_subscribes, 'sum_rebills': sum_rebills, 'sum_unsubscribes': sum_unsubscribes,
            'sum_profit': sum_profit, 'sum_convert_reg_act': sum_convert_reg_act,
            'sum_convert_host_reg': sum_convert_host_reg
        }
    except:
        filter_dict['start'] = date_for_api1.sub(r'\3.\2.\1', filter_dict['start'])
        filter_dict['end'] = date_for_api1.sub(r'\3.\2.\1', filter_dict['end'])
        response_by_hours = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/', data=filter_dict)
        hours_stat = json.loads(response_by_hours.text).get('hours')
        data_params = json.loads(response_by_hours.text).get('used_filters')
        '''Запрос для вывода данных с процентом для крайней строки'''
        filter_last_line['start'] = date_for_api1.sub(r'\3.\2.\1', filter_last_line.get('start'))
        filter_last_line['end'] = date_for_api1.sub(r'\3.\2.\1', filter_last_line.get('end'))
        request_last_line = requests.post(f'{domain_api1}/statistic/{request.session["id"]}/',
                                          data=filter_last_line)
        response_last_line = json.loads(request_last_line.text).get('hours')
        last_line_info = response_last_line.get(filter_last_line['end']).get('23')

        '''наполнение списков по статистике'''
        for key, item in hours_stat.items():
            for i, j in item.items():
                list_hosts.append(j.get('hosts'))
                list_registrations.append(j.get('registrations'))
                list_activations.append(j.get('activations'))
                list_subscribes.append(j.get('subscribes'))
                list_rebills.append(j.get('rebills'))
                list_unsubscribes.append(j.get('unsubscribes'))
                list_profit.append(j.get('profit'))
                list_convert_host_reg.append(convert_calculate(j.get('hosts'), j.get('registrations')))
                list_convert_reg_act.append(convert_calculate(j.get('registrations'), j.get('activations')))

        '''Для вывода процентов'''
        list_hosts_for_perc = list_hosts.copy()
        list_registrations_for_perc = list_registrations.copy()
        list_activations_for_perc = list_activations.copy()
        list_subscribes_for_perc = list_subscribes.copy()
        list_rebills_for_perc = list_rebills.copy()
        list_unsubscribes_for_perc = list_unsubscribes.copy()
        list_profit_for_perc = list_profit.copy()
        list_convert_host_reg_for_perc = list_convert_host_reg.copy()
        list_convert_reg_act_for_perc = list_convert_reg_act.copy()

        list_hosts_for_perc.append(last_line_info.get('hosts'))
        list_registrations_for_perc.append(last_line_info.get('registrations'))
        list_activations_for_perc.append(last_line_info.get('activations'))
        list_subscribes_for_perc.append(last_line_info.get('subscribes'))
        list_rebills_for_perc.append(last_line_info.get('rebills'))
        list_unsubscribes_for_perc.append(last_line_info.get('unsubscribes'))
        list_profit_for_perc.append(last_line_info.get('profit'))
        list_convert_host_reg_for_perc.append(convert_calculate(last_line_info.get('hosts'), last_line_info.get('registrations')))
        list_convert_reg_act_for_perc.append(convert_calculate(last_line_info.get('registrations'), last_line_info.get('activations')))

        '''для вывода итогового значения ВСЕГО'''
        sum_stat = {
            'sum_hosts': sum(list_hosts), 'sum_registrations': sum(list_registrations),
            'sum_activations': sum(list_activations),
            'sum_subscribes': sum(list_subscribes), 'sum_rebills': sum(list_rebills),
            'sum_unsubscribes': sum(list_unsubscribes),
            'sum_profit': sum(list_profit),
            'sum_convert_reg_act': convert_calculate(sum(list_registrations), sum(list_activations)),
            'sum_convert_host_reg': convert_calculate(sum(list_hosts), sum(list_registrations))
        }

        '''список с данными для флажков по процетнам соотношение вчера/сегодня'''
        hosts_proc_list = get_percents_list(list_hosts_for_perc)
        registr_proc_list = get_percents_list(list_registrations_for_perc)
        activ_proc_list = get_percents_list(list_activations_for_perc)
        subsc_proc_list = get_percents_list(list_subscribes_for_perc)
        rebills_proc_list = get_percents_list(list_rebills_for_perc)
        unsub_proc_list = get_percents_list(list_unsubscribes_for_perc)
        prof_proc_list = get_percents_list(list_profit_for_perc)
        convert_reg_act_proc_list = get_percents_list(list_convert_reg_act_for_perc)
        convert_host_reg_proc_list = get_percents_list(list_convert_host_reg_for_perc)

        k = 0  # счетчик
        p = 0  # счетчик
        '''Добавляю конверт в словарь, для отображения в статистике
        Цикл для добавления полученных данных в основной словарь со статистикой'''
        for key, item in hours_stat.items():
            for i, j in item.items():
                if k < len(list_convert_reg_act):
                    item[i].setdefault('convert_reg_act', list_convert_reg_act[k])
                    item[i].setdefault('convert_host_reg', list_convert_host_reg[k])
                    k += 1
                if p < len(hosts_proc_list):
                    item[i].setdefault('hosts_proc', hosts_proc_list[p])
                    item[i].setdefault('registr_proc', registr_proc_list[p])
                    item[i].setdefault('conv_proc', registr_proc_list[p])
                    item[i].setdefault('activ_proc', activ_proc_list[p])
                    item[i].setdefault('subsc_proc', subsc_proc_list[p])
                    item[i].setdefault('rebills_proc', rebills_proc_list[p])
                    item[i].setdefault('unsub_proc', unsub_proc_list[p])
                    item[i].setdefault('prof_proc', prof_proc_list[p])
                    item[i].setdefault('convert_reg_act_proc', convert_reg_act_proc_list[p])
                    item[i].setdefault('convert_host_reg_proc', convert_host_reg_proc_list[p])
                p += 1
        hours_stat = hours_stat.get(filter_dict.get('start'))

    collapsed = request.session.get('collapsed_hours')

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    try:
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%Y-%m-%d').strftime('%d.%m.%Y')
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%Y-%m-%d').strftime('%d.%m.%Y')
    except:
        filter_dict['end'] = filter_dict['end']
        filter_dict['start'] = filter_dict['start']

    data = {
        'title': 'Статистика по часам', 'page_name': 'Статистика по часам', 'sum_stat': sum_stat,
        'data_params': data_params, 'req_data': filter_dict, 'date_now': date_now,
        'hours_stat': hours_stat, 'collapsed': collapsed, 'data_filter': filter_get
    }
    return render(request, 'stats-hour.html', data)


@get_error
@check_profile
def stat_subs(request):
    '''статистика по подпискам'''
    col = request.session.get('collapsed_subs')
    if not col:
        request.session['collapsed_subs'] = 2

    limit = request.session.get("limit_subs")
    if not limit:
        request.session["limit_subs"] = 25

    date_now = date.today()
    date_before_seven_day = date_now - timedelta(days=6)
    date_before_seven_day = date_before_seven_day.strftime("%d.%m.%Y")
    date_now = date_now.strftime("%d.%m.%Y")

    collapse(request, 'collapsed_subs')

    show_button = False
    if request.GET:
        show_button = True

    filter_get = dict(request.GET)
    filter_dict = {}
    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict_other(filter_dict, filter_get)

    if request.method == 'POST':
        if request.POST.get('type') == 'stream_id':
            return HttpResponse(post_filter(request.session, "Stream", 'stream_id'))
        if request.POST.get('type') == 'landing_id':
            return HttpResponse(post_filter(request.session, "Landing", 'landing_id'))
        if request.POST.get('type') == 'offer_id':
            return HttpResponse(post_filter(request.session, "Offer", 'offer_id'))
        if request.POST.get('type') == 'country':
            return HttpResponse(post_filter(request.session, "Country", 'country'))
        if request.POST.get('type') == 'os':
            return HttpResponse(post_filter(request.session, "OS", 'os'))
        if request.POST.get('type') == 'browser':
            return HttpResponse(post_filter(request.session, "Browser", 'browser'))
        if request.POST.get('type') == 'ref_domain':
            return HttpResponse(post_filter(request.session, "RefDomain", 'ref_domain'))

        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_subs"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    if filter_dict.get('stream_id'):
        check_and_request_filter(request, filter_dict, 'stream_id', "Stream")
    if filter_dict.get('offer_id'):
        check_and_request_filter(request, filter_dict, 'offer_id', "Offer")
    if filter_dict.get('landing_id'):
        check_and_request_filter(request, filter_dict, 'landing_id', "Landing")
    if filter_dict.get('country'):
        check_and_request_filter(request, filter_dict, 'country', "Country")
    if filter_dict.get('os'):
        check_and_request_filter(request, filter_dict, 'os', "OS")
    if filter_dict.get('browser'):
        check_and_request_filter(request, filter_dict, 'browser', "Browser")
    if filter_dict.get('ref_domain'):
        check_and_request_filter(request, filter_dict, 'ref_domain', "RefDomain")

    filter_dict["stat"] = "Subscriptions"

    page = set_page(request.GET)

    if filter_dict.get('start'):
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
    if filter_dict.get('end'):
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%d.%m.%Y').strftime('%Y-%m-%d')

    limit = request.session["limit_subs"]
    offset = set_offset(page, limit)

    try:
        request_filter = json.loads(requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
            json.dumps(filter_dict)).content)
        all_table_data = request_filter.get('subscriptions')
        count = math.ceil(int(request_filter.get('count')) / limit)
        original_count = request_filter.get('count')
        rebill_func = rebill_calculate
    except:
        if filter_dict.get('start'):
            filter_dict['start'] = datetime.strptime(filter_dict.get('start'), '%Y-%m-%d').strftime('%d.%m.%Y')
        if filter_dict.get('end'):
            filter_dict['end'] = datetime.strptime(filter_dict.get('end'), '%Y-%m-%d').strftime('%d.%m.%Y')
        request_filter = json.loads(
            requests.post(f'{domain_api1}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
                          data=filter_dict).content)
        all_table_data = request_filter.get('subscriptions')
        count = math.ceil(int(request_filter.get('count')) / limit)
        original_count = request_filter.get('count')
        rebill_func = rebill_calculate_api1

    sum_rebills_good = 0
    sum_rebills_bad = 0
    sum_rebills_total = 0
    sum_profite = 0

    for data in all_table_data:
        rebill_func(data)
        sum_rebills_good += int(data['rebills_good'])
        sum_rebills_bad += int(data['rebills_bad'])
        sum_rebills_total += int(data['rebills_total'])
        sum_profite += data['profit']
        for key, value in BANKS.items():
            if data['bank'] == key:
                data['bank'] = value
        data['tarif'] = f'{isInt(data["tarif"].split("/")[0])}/{isInt(data["tarif"].split("/")[1])}'

    collapsed = request.session.get('collapsed_subs')
    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]
    session_request_subs_offers_balance(request)  # Доп данные для сессии

    if filter_dict.get('start'):
        try:
            filter_dict['start'] = datetime.strptime(filter_dict['start'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['start'] = filter_dict.get('start')
    if filter_dict.get('end'):
        try:
            filter_dict['end'] = datetime.strptime(filter_dict['end'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['end'] = filter_dict.get('end')

    data = {
        'title': 'Статистика по подпискам', 'page_name': 'Статистика по подпискам',
        'days_stat': stat_subs, 'start_seven': date_before_seven_day, 'date_now': date_now,
        'sum_rebills_good': sum_rebills_good, 'collapsed': collapsed, "show_button": show_button,
        'table_data': all_table_data, 'url_params': url_params, 'req_data': filter_dict, 'count': count,
        'page': page, 'limit': limit, 'sum_rebills_bad': sum_rebills_bad, 'sum_rebills_total': sum_rebills_total,
        'sum_profite': sum_profite, 'original_count': original_count, 'data_filter': filter_get
    }
    return render(request, 'stats-subs.html', data)


@get_error
@check_profile
def stat_rebills(request):
    '''Статистика по ребиллам'''

    col = request.session.get('collapsed_rebills')
    if not col:
        request.session['collapsed_rebills'] = 2

    date_now = date.today()
    date_before_seven_day = date_now - timedelta(days=6)
    date_before_seven_day = date_before_seven_day.strftime("%d.%m.%Y")
    date_now = date_now.strftime("%d.%m.%Y")

    collapse(request, 'collapsed_rebills')
    limit = request.session.get("limit_rebill")
    if not limit:
        request.session["limit_rebill"] = 25

    show_button = False
    if request.GET:
        show_button = True

    filter_get = dict(request.GET)
    filter_dict = {}
    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict_other(filter_dict, filter_get)

    if request.method == 'POST':
        if request.POST.get('type') == 'stream_id':
            return HttpResponse(post_filter(request.session, "Stream", 'stream_id'))
        if request.POST.get('type') == 'landing_id':
            return HttpResponse(post_filter(request.session, "Landing", 'landing_id'))
        if request.POST.get('type') == 'offer_id':
            return HttpResponse(post_filter(request.session, "Offer", 'offer_id'))
        if request.POST.get('type') == 'country':
            return HttpResponse(post_filter(request.session, "Country", 'country'))
        if request.POST.get('type') == 'os':
            return HttpResponse(post_filter(request.session, "OS", 'os'))
        if request.POST.get('type') == 'browser':
            return HttpResponse(post_filter(request.session, "Browser", 'browser'))
        if request.POST.get('type') == 'ref_domain':
            return HttpResponse(post_filter(request.session, "RefDomain", 'ref_domain'))

        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_rebill"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    if filter_dict.get('stream_id'):
        check_and_request_filter(request, filter_dict, 'stream_id', "Stream")
    if filter_dict.get('offer_id'):
        check_and_request_filter(request, filter_dict, 'offer_id', "Offer")
    if filter_dict.get('landing_id'):
        check_and_request_filter(request, filter_dict, 'landing_id', "Landing")
    if filter_dict.get('country'):
        check_and_request_filter(request, filter_dict, 'country', "Country")
    if filter_dict.get('os'):
        check_and_request_filter(request, filter_dict, 'os', "OS")
    if filter_dict.get('browser'):
        check_and_request_filter(request, filter_dict, 'browser', "Browser")
    if filter_dict.get('ref_domain'):
        check_and_request_filter(request, filter_dict, 'ref_domain', "RefDomain")

    filter_dict['stat'] = 'Rebills'

    page = set_page(request.GET)
    limit = request.session["limit_rebill"]
    offset = set_offset(page, limit)

    if filter_dict.get('start'):
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
    if filter_dict.get('end'):
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%d.%m.%Y').strftime('%Y-%m-%d')

    try:
        request_data = json.loads(requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
            json.dumps(filter_dict)).content)
        original_count = request_data.get('count')
        all_table_data = request_data.get('subscriptions')
        count = math.ceil(int(request_data.get('count')) / limit)
        rebill_func = rebill_calculate
    except:
        if filter_dict.get('start'):
            filter_dict['start'] = datetime.strptime(filter_dict.get('start'), '%Y-%m-%d').strftime('%d.%m.%Y')
        if filter_dict.get('end'):
            filter_dict['end'] = datetime.strptime(filter_dict.get('end'), '%Y-%m-%d').strftime('%d.%m.%Y')
        request_filter = json.loads(
            requests.post(f'{domain_api1}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
                          data=filter_dict).content)
        all_table_data = request_filter.get('subscriptions')
        count = math.ceil(int(request_filter.get('count')) / limit)
        original_count = request_filter.get('count')
        rebill_func = rebill_calculate_api1

    sum_rebills_good = 0
    sum_rebills_bad = 0
    sum_rebills_total = 0
    sum_profite = 0

    '''Для подсчета итогов, так же для '''
    for data in all_table_data:
        rebill_func(data)
        sum_rebills_good += int(data['rebills_good'])
        sum_rebills_bad += int(data['rebills_bad'])
        sum_rebills_total += int(data['rebills_total'])
        sum_profite += data['profit']
        data['tarif'] = f'{isInt(data["tarif"].split("/")[0])}/{isInt(data["tarif"].split("/")[1])}'
        for key, value in BANKS.items():
            if data['bank'] == str(key):
                data['bank'] = value

    collapsed = request.session.get('collapsed_rebills')
    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]
    session_request_subs_offers_balance(request)  # Доп данные для сессии

    if filter_dict.get('start'):
        try:
            filter_dict['start'] = datetime.strptime(filter_dict['start'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['start'] = filter_dict.get('start')
    if filter_dict.get('end'):
        try:
            filter_dict['end'] = datetime.strptime(filter_dict['end'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['end'] = filter_dict.get('end')

    data = {
        'title': 'Статистика по ребиллам', 'page_name': 'Статистика по ребиллам', 'data_filter': filter_get,
        'collapsed': collapsed, "show_button": show_button, 'limit': limit, 'original_count': original_count,
        'start_seven': date_before_seven_day, 'date_now': date_now, 'sum_rebills_good': sum_rebills_good,
        'table_data': all_table_data, 'sum_rebills_bad': sum_rebills_bad,  'count': count, 'page': page,
        'sum_rebills_total': sum_rebills_total, 'req_data': filter_dict, 'sum_profite': sum_profite,
        'days_stat': stat_subs, 'url_params': url_params,
    }
    return render(request, 'stats-rebills.html', data)


@get_error
@check_profile
def stat_unsubs(request):
    '''Статистика по отпискам'''
    col = request.session.get('collapsed_unsubs')
    if not col:
        request.session['collapsed_unsubs'] = 2

    limit = request.session.get("limit_unsubs")
    if not limit:
        request.session["limit_unsubs"] = 25

    date_now = date.today()
    date_before_seven_day = date_now - timedelta(days=6)
    date_before_seven_day = date_before_seven_day.strftime("%d.%m.%Y")
    date_now = date_now.strftime("%d.%m.%Y")

    collapse(request, 'collapsed_unsubs')

    filter_get = dict(request.GET)
    filter_dict = {}

    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict_other(filter_dict, filter_get)

    if request.method == 'POST':
        if request.POST.get('type') == 'stream_id':
            return HttpResponse(post_filter(request.session, "Stream", 'stream_id'))
        if request.POST.get('type') == 'landing_id':
            return HttpResponse(post_filter(request.session, "Landing", 'landing_id'))
        if request.POST.get('type') == 'offer_id':
            return HttpResponse(post_filter(request.session, "Offer", 'offer_id'))
        if request.POST.get('type') == 'country':
            return HttpResponse(post_filter(request.session, "Country", 'country'))
        if request.POST.get('type') == 'os':
            return HttpResponse(post_filter(request.session, "OS", 'os'))
        if request.POST.get('type') == 'browser':
            return HttpResponse(post_filter(request.session, "Browser", 'browser'))
        if request.POST.get('type') == 'ref_domain':
            return HttpResponse(post_filter(request.session, "RefDomain", 'ref_domain'))

        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_unsubs"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

    if filter_dict.get('stream_id'):
        check_and_request_filter(request, filter_dict, 'stream_id', "Stream")
    if filter_dict.get('offer_id'):
        check_and_request_filter(request, filter_dict, 'offer_id', "Offer")
    if filter_dict.get('landing_id'):
        check_and_request_filter(request, filter_dict, 'landing_id', "Landing")
    if filter_dict.get('country'):
        check_and_request_filter(request, filter_dict, 'country', "Country")
    if filter_dict.get('os'):
        check_and_request_filter(request, filter_dict, 'os', "OS")
    if filter_dict.get('browser'):
        check_and_request_filter(request, filter_dict, 'browser', "Browser")
    if filter_dict.get('ref_domain'):
        check_and_request_filter(request, filter_dict, 'ref_domain', "RefDomain")

    filter_dict['stat'] = 'Unsubs'

    page = set_page(request.GET)
    limit = request.session["limit_unsubs"]
    offset = set_offset(page, limit)

    if filter_dict.get('start'):
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
    if filter_dict.get('end'):
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%d.%m.%Y').strftime('%Y-%m-%d')

    try:
        requests_filter = json.loads(requests.post(f'{DOMAIN_API}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
            json.dumps(filter_dict)).content)
        original_count = requests_filter.get('count')
        count = math.ceil(int(requests_filter.get('count')) / limit)
        all_table_data = requests_filter.get('subscriptions')
        rebill_func = rebill_calculate
    except:
        if filter_dict.get('start'):
            filter_dict['start'] = datetime.strptime(filter_dict.get('start'), '%Y-%m-%d').strftime('%d.%m.%Y')
        if filter_dict.get('end'):
            filter_dict['end'] = datetime.strptime(filter_dict.get('end'), '%Y-%m-%d').strftime('%d.%m.%Y')
        request_filter = json.loads(
            requests.post(f'{domain_api1}/statistic/{request.session["id"]}/?limit={limit}&offset={offset}',
                          data=filter_dict).content)
        all_table_data = request_filter.get('subscriptions')
        count = math.ceil(int(request_filter.get('count')) / limit)
        original_count = request_filter.get('count')
        rebill_func = rebill_calculate_api1

    sum_rebills_good = 0
    sum_rebills_bad = 0
    sum_rebills_total = 0
    sum_profite = 0

    '''Преобразование и подсчет итоговых значений'''
    for data in all_table_data:
        rebill_func(data)
        sum_rebills_good += int(data['rebills_good'])
        sum_rebills_bad += int(data['rebills_bad'])
        sum_rebills_total += int(data['rebills_total'])
        sum_profite += data['profit']
        data['tarif'] = f'{isInt(data["tarif"].split("/")[0])}/{isInt(data["tarif"].split("/")[1])}'
        for key, value in BANKS.items():
            if data['bank'] == key:
                data['bank'] = value

    show_button = False
    if request.GET:
        show_button = True

    collapsed = request.session.get('collapsed_unsubs')
    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]
    session_request_subs_offers_balance(request)  # Доп данные для сессии

    if filter_dict.get('start'):
        try:
            filter_dict['start'] = datetime.strptime(filter_dict['start'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['start'] = filter_dict.get('start')
    if filter_dict.get('end'):
        try:
            filter_dict['end'] = datetime.strptime(filter_dict['end'], '%Y-%m-%d').strftime('%d.%m.%Y')
        except:
            filter_dict['end'] = filter_dict.get('end')

    data = {
        'title': 'Статистика по отпискам', 'page_name': 'Статистика по отпискам', 'limit': limit, 'page': page,
        'collapsed': collapsed, "show_button": show_button, 'sum_rebills_good': sum_rebills_good,
        'start_seven': date_before_seven_day, 'date_now': date_now, 'data_filter': filter_get,
        'table_data': all_table_data, 'sum_rebills_bad': sum_rebills_bad, 'sum_rebills_total': sum_rebills_total,
        'req_data': filter_dict, 'sum_profite': sum_profite, 'days_stat': stat_unsubs,
        'url_params': url_params, 'count': count, 'original_count': original_count,
    }
    return render(request, 'stats-unsubs.html', data)


@get_error
@check_profile
def stat_streams(request):

    limit = request.session.get("limit_streams")
    if not limit:
        request.session["limit_streams"] = 25

    page = set_page(request.GET)
    limit = request.session["limit_streams"]
    offset = set_offset(page, limit)

    order = request.session.get('order_by')
    if not order:
        request.session['order_by'] = 'profit'
    order = request.session['order_by']

    direction = request.session.get('direction')
    if not direction:
        request.session['direction'] = 0
    direction = request.session['direction']

    date_now = date.today()
    date_before_seven_days = date_now - timedelta(days=6)

    date_before_seven_day = date_before_seven_days.strftime("%d.%m.%Y")
    date_now = date_now.strftime("%d.%m.%Y")

    filter_get = dict(request.GET)
    filter_dict = {}

    '''словрь для получения данных с GET запроса и для его заполнения'''
    get_filter_dict(filter_dict, filter_get)

    filter_dict['partner_id'] = request.session['id']
    filter_dict['direction'] = direction

    if int(request.session.get('direction')) == False:
        del filter_dict['direction']

    filter_dict['order_by'] = order

    if filter_dict.get('offer_id'):
        for offer in request.session['offers_list']:
            if offer.get("name") == filter_dict.get('offer_id'):
                filter_dict['offer_id'] = offer.get("id")

    if filter_dict.get('start'):
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%d.%m.%Y').strftime('%Y-%m-%d')
    if filter_dict.get('end'):
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%d.%m.%Y').strftime('%Y-%m-%d')

    if request.method == 'POST':
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'page_limit':
            request.session["limit_streams"] = int(request.POST.get('limit'))
            return HttpResponse({'status': 'OK'})

        # смена поля сортировки
        if request.POST.get('type') == 'change_order':
            request.session['order_by'] = request.POST.get('order_by')
            filter_dict['order_by'] = request.POST.get('order_by')
            filter_dict['direction'] = request.session['direction']
            try:
                req_stream = requests.post(
                    f'{DOMAIN_API}/stream_statistic/?limit={request.session["limit_streams"]}&offset={offset}',
                    json.dumps(filter_dict))
            except:
                req_stream = requests.post(f'{domain_api1}/stream_statistic/?limit={limit}&offset={offset}',
                                               json=filter_dict)
            ajax_streams = json.loads(req_stream.content).get('streams')
            return JsonResponse({'res': ajax_streams})
        # смена направления сортировки
        if request.POST.get('type') == 'direction_order':
            request.session['direction'] = int(request.POST.get('direction_by'))
            try:
                req_stream = requests.post(
                    f'{DOMAIN_API}/stream_statistic/?limit={request.session["limit_streams"]}&offset={offset}',
                    json.dumps(filter_dict))
            except:
                req_stream = requests.post(f'{domain_api1}/stream_statistic/?limit={limit}&offset={offset}',
                                           json=filter_dict)
            ajax_streams = json.loads(req_stream.content).get('streams')
            return JsonResponse({'res': ajax_streams})

    try:
        request_stream = json.loads(requests.post(f'{DOMAIN_API}/stream_statistic/?limit={request.session["limit_streams"]}&offset={offset}',
            json.dumps(filter_dict)).content)
        '''Данные для вывода статистики в таблицу'''
        stream_stat = request_stream.get('streams')
        count = math.ceil(int(request_stream.get('count')[0].get('count')) / limit)
        original_count = int(request_stream.get('count')[0].get('count'))
    except:
        request_stream = json.loads(requests.post(f'{domain_api1}/stream_statistic/?limit={limit}&offset={offset}',
                                       json=filter_dict).content)
        '''Данные для вывода статистики в таблицу'''
        stream_stat = request_stream.get('streams')
        count = math.ceil(int(request_stream.get('count')) / limit)
        original_count = int(request_stream.get('count'))

    if filter_dict.get('start'):
        filter_dict['start'] = datetime.strptime(filter_dict['start'], '%Y-%m-%d').strftime('%d.%m.%Y')
    if filter_dict.get('end'):
        filter_dict['end'] = datetime.strptime(filter_dict['end'], '%Y-%m-%d').strftime('%d.%m.%Y')

    '''итоговая сумма полученных статистикой'''
    sum_hosts = 0
    sum_registrations = 0
    sum_activations = 0
    sum_subscribes = 0
    sum_rebills = 0
    sum_bad_rebills = 0
    sum_unsubscribes = 0
    sum_profit = 0

    '''Добавляю конверт в словарь, для отображения в статистике'''
    for key in stream_stat:
        sum_hosts += int(key.get('hosts'))
        sum_registrations += int(key.get('registrations'))
        sum_activations += int(key.get('activations'))
        sum_subscribes += int(key.get('subscribes'))
        sum_rebills += int(key.get('rebills'))
        sum_bad_rebills += int(key.get('bad_rebills'))
        sum_unsubscribes += int(key.get('unsubscribes'))
        if key.get('profit') == 'None' or key.get('profit') is None:
            sum_profit += 0
        else:
            sum_profit += key.get('profit')
        key.setdefault('convert_host_reg', convert_calculate(key.get('hosts'), key.get('registrations')))
        key.setdefault('convert_reg_act', convert_calculate(key.get('registrations'), key.get('activations')))

    sum_convert_host_reg = convert_calculate(sum_hosts, sum_registrations)
    sum_convert_reg_act = convert_calculate(sum_registrations, sum_activations)

    '''для вывода итогового значения ВСЕГО'''
    sum_stat = {
        'sum_hosts': sum_hosts, 'sum_registrations': sum_registrations, 'sum_activations': sum_activations,
        'sum_subscribes': sum_subscribes, 'sum_rebills': sum_rebills, 'sum_bad_rebills': sum_bad_rebills,
        'sum_unsubscribes': sum_unsubscribes,'sum_profit': sum_profit, 'sum_convert_reg_act': sum_convert_reg_act,
        'sum_convert_host_reg': sum_convert_host_reg,
    }

    session_request_subs_offers_balance(request)  # Доп данные для сессии
    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]
    data = {
        'title': 'Статистика по потокам', 'page_name': 'Статистика по потокам', 'sum_stat': sum_stat,
        'start_seven': date_before_seven_day, 'date_now': date_now, 'req_data': filter_dict, 'count': count,
        'stream_stat': stream_stat, 'page': page, 'limit': limit, 'data_filter': filter_get,
        'url_params': url_params, 'original_count': original_count, 'order': order, 'direction': direction
    }
    return render(request, 'stats-streams.html', data)


@get_error
@check_profile
def stat_days_subs(request):
    '''Статистика по дате подписки'''

    session_request_subs_offers_balance(request)  # Доп данные для сессии

    data = {
        'title': 'Статистика по дате подписки', 'page_name': 'Статистика по дате подписки',
    }
    return render(request, 'stats-date-subs.html', data)