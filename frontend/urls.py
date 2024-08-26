from django.urls import path, re_path
from . import views
from frontend_statistic import views as frontend_statistic


urlpatterns = [
    # Статистика
    path('', frontend_statistic.empty_page),
    path('general/', frontend_statistic.empty_page, name='general'),
    path('days/', frontend_statistic.stat_days, name='days'),
    path('hours/', frontend_statistic.stat_hours, name='hours'),
    path('stat-date-subs/', frontend_statistic.stat_days_subs, name='stat_date_subs'),
    path('stat-unsubs/', frontend_statistic.stat_unsubs, name='stat_unsubs'),
    path('stat-subs/', frontend_statistic.stat_subs, name='stat_subs'),
    path('stat-rebills/', frontend_statistic.stat_rebills, name='stat_rebills'),
    path('stat-streams/', frontend_statistic.stat_streams, name='stat_streams'),

    # Профиль Авторизация Регистрация
    path('profile/', views.profile, name='profile'),
    path('auth/', views.signin, name='login'),
    path('sign-up/', views.reg_user, name='register'),
    path('reg/<str:uid>/', views.referal_incomming, name='referal_incomming'),
    re_path(r'^authmanager/', views.redirect_from_outside, name='redirect_incomming'),
    path('logout/', views.logout, name='logout'),
    path('forgot/', views.forgot, name='forgot'),

    # Потоки, Офферы
    path('streams/', views.streams, name='streams'),
    path('stream-add/', views.add_streams, name='add_stream'),
    path('stream-edit/<str:stream_uid>/', views.edit_stream, name='stream_edit'),
    path('offer/<int:offer_id>/', views.offer, name='offer'),

    # Постбеки
    path('postbacks/', views.postbacks, name='postbacks'),
    path('postback-edit/<int:postback_id>/', views.edit_postback, name='postback_edit'),
    path('postback-add/', views.add_postback, name='add_postback'),
    path('postback-logs/<int:postback_id>/', views.logs_postback, name='logs_postback'),

    # Взаиморасчеты
    path('payments/', views.payments, name='payments'),
    path('payment-add/', views.add_payment, name='add_payment'),

    # Прочие
    path('support/', views.support, name='support'),
    path('top-webs/', views.top_webs, name='top_webs'),
    path('referrals/', views.referrals, name='referrals'),
    path('news/', views.news, name='news'),
    path('lock-page/', views.lock_page, name='lockpage'),
    path('ban-page/', views.ban_page, name='ban_web'),
]

handler404 = 'frontend.views.page_not_found'
handler500 = 'frontend.views.handler500'
handler501 = 'frontend.views.handler501'
