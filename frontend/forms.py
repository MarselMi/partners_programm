import requests
from django import forms
from .mixins import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate


class RegisterUserForm(ContextMixin, forms.Form):
    name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': 'Enter your firstname and lastname'}))
    email = forms.CharField(label='Email', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                         'placeholder': 'Enter your email'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                                  'placeholder': 'Enter your password'}))
    title = 'Регистрация'
    field_order = {'title': title, 'name': name, 'email': email, 'password': password}


class LoginUserForm(AuthenticationForm):
    title = 'Добро пожаловать'
    username = forms.CharField(label='Email', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                            'placeholder': 'Enter your email'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                             'placeholder': 'Enter your password'}))


class StreamForm(forms.Form):
    class Meta:
        fields = ['name', 'yandex_metric', 'google_analytics', 'top_mail_ru', 'facebook_pixel', 'vk_counter',
                  'tiktok_pixel']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamName', 'placeholder': 'Поток 1'}),
            'yandex_metric': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerYaMetrika', 'placeholder': 'XXXXXXXX'}),
            'google_analytics': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerGoogleAn', 'placeholder': 'XXXXXXXX'}),
            'top_mail_ru': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerTopMailRu', 'placeholder': 'XXXXXXXX'}),
            'facebook_pixel': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerFBpixel', 'placeholder': 'XXXXXXXX'}),
            'vk_counter': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerVKcounter', 'placeholder': 'XXXXXXXX'}),
            'tiktok_pixel': forms.TextInput(
                attrs={'class': 'form-control', 'id': 'streamTrackerVKcounter', 'placeholder': 'XXXXXXXX'}),
        }


class PostbackForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['method'].widget.choices[0] = ('', 'Выберите метод')

    class Meta:
        url_postback = 'https://api.spaff.ru/api/v1/postbacks/1/'
        model = requests.get(url_postback).json()
        fields = ['name', 'method', 'link', 'event_id']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'id': 'postbackName', 'placeholder': 'PostBack 1'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'link': forms.Textarea(attrs={'class': 'form-control', 'cols': 5}),
            'event_id': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input', 'id': 'cbPostBacksReg'})
        }


class ProfileContactsEditeForm(forms.Form):
    telegram = forms.CharField(label='Telegram', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': '@telegram'}))
    phone = forms.CharField(label='Телефон', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                         'placeholder': '+79998888777'}))

class ProfileCardEditForm(forms.Form):
    recvisite = forms.CharField(label='Карта РФ', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': '0000 0000 0000 0000'}))


class ProfilePasswordChangeForm(forms.Form):
    current_password = forms.CharField(label='Текущий пароль', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': '********'}))
    new_password = forms.CharField(label='Новый пароль', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': '********'}))
    repeat_new_password = forms.CharField(label='Повторите новый пароль', widget=forms.TextInput(attrs={'class': 'form-control',
                                                                      'placeholder': '********'}))
    field_order = ['current_password', 'new_password', 'repeat_new_password']