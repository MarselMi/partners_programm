from django import forms


class FilterStatistic(forms.Form):
    start_day = forms.CharField(required=False, label='День', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterDay', }))
    end_day = forms.CharField(required=False, label='День', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'EndFilterDay', }))

    countries = forms.TypedChoiceField(required=False, label='Страна', widget=forms.Select(attrs={'class': 'form-select', 'id': 'StatFilterCountry',}),
                                       empty_value='',
                                       choices=(('', 'Все страны'),
                                               ('1', 'Страна 1'),
                                               ('2', 'Страна 2'),
                                               ('3', 'Страна 3')))
    type_device = forms.TypedChoiceField(required=False, label='Тип устройства', widget=forms.Select(attrs={'class': 'form-select', 'id': 'StatFilterDevice',}),
                                         empty_value='',
                                         choices=(('', 'Все устройства'),
                                                  ('1', 'DESKTOP'),
                                                  ('2', 'MOBILE')))
    os = forms.TypedChoiceField(required=False, label='ОС', widget=forms.Select(attrs={'class': 'form-select', 'id': 'StatFilterOS',}),
                                empty_value='',
                                choices=(('', 'Все ОС'),
                                         ('1', 'ОС 1'),
                                         ('2', 'ОС 2'),
                                         ('3', 'ОС 3')))
    browser = forms.TypedChoiceField(required=False, label='Браузер', widget=forms.Select(attrs={'class': 'form-select', 'id': 'StatFilterBrowser',}),
                                     empty_value='',
                                     choices=(('', 'Все браузеры'),
                                              ('1', 'Браузер 1'),
                                              ('2', 'Браузер 2'),
                                              ('3', 'Браузер 3')))
    source = forms.TypedChoiceField(required=False, label='Источники', widget=forms.Select(attrs={'class': 'form-select', 'id': 'StatFilterSource',}),
                                    empty_value='',
                                    choices=(('', 'Все источники'),
                                             ('1', 'Источник 1'),
                                             ('2', 'Источник 2'),
                                             ('3', 'Источник 3')))
    sub_1 = forms.CharField(required=False, label='Субаккаунт 1', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterSubAcс-1',}))
    sub_2 = forms.CharField(required=False, label='Субаккаунт 2', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterSubAcс-2',}))
    sub_3 = forms.CharField(required=False, label='Субаккаунт 3', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterSubAcс-3',}))
    sub_4 = forms.CharField(required=False, label='Субаккаунт 4', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterSubAcс-4',}))
    sub_5 = forms.CharField(required=False, label='Субаккаунт 5', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterSubAcс-5',}))
    utm_source = forms.CharField(required=False, label='UTM Source', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterUTMSource',}))
    utm_medium = forms.CharField(required=False, label='UTM Medium', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterUTMMedium',}))
    utm_campaign = forms.CharField(required=False, label='UTM Campaign', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterUTMCampaign',}))
    utm_content = forms.CharField(required=False, label='UTM Content', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterUTMContent',}))
    utm_term = forms.CharField(required=False, label='UTM Term', widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'StatFilterUTMTerm',}))

