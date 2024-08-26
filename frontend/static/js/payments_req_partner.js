'use strict'

var url = document.location.href;
var a = document.cookie.split(';');
var token = '';

for (let i = 0; i < a.length; i++) {
	var b = a[i].split('=');
	b[0] = b[0].replace(/\s+/g, '');
	if (b[0] == 'csrftoken') {
		token = b[1];
	}
};

function addPayments() {
    var capitalist = $('#capitalist_req');
    var webmoney = $('#webmoney');
    var qiwi = $('#qiwi');
    var umoney = $('#umoney');
    var rucard_card_data = $('#rucard_card_data');
    var rucard_firstname = $('#rucard_firstname');
    var rucard_lastname = $('#rucard_lastname');
    var data_card_to_card = $('#data_card_to_card');
    var data_mastercard_worldwide = $('#data_mastercard_worldwide');
    var month_mc = $('#month_mc');
    var year_mc = $('#year_mc');
    var name_mc = $('#name_mc');
    var surname_mc = $('#surname_mc');
    var birth_date_mc = $('#birth_date_mc');
    var country_code_mc = $('#country_code_mc');
    var city_mc = $('#city_mc');
    var address_mc = $('#address_mc');
    var usdt_erc_20 = $('#usdt_erc_20');
    var usdt_trc_20 = $('#usdt_trc_20');
    var ipru_name = $('#ipru_name');
    var ipru_address = $('#ipru_address');
    var ipru_inn = $('#ipru_inn');
    var ipru_ogrn = $('#ipru_ogrn');
    var ipru_rs = $('#ipru_rs');
    var ipru_bank = $('#ipru_bank');
    var ipru_inn_bank = $('#ipru_inn_bank');
    var ipru_bik_bank = $('#ipru_bik_bank');
    var ipru_ks_bank = $('#ipru_ks_bank');
    var oooru_name = $('#oooru_name');
    var oooru_address = $('#oooru_address');
    var oooru_inn = $('#oooru_inn');
    var oooru_kpp = $('#oooru_kpp');
    var oooru_ogrn = $('#oooru_ogrn');
    var oooru_rs = $('#oooru_rs');
    var oooru_bank = $('#oooru_bank');
    var oooru_inn_bank = $('#oooru_inn_bank');
    var oooru_bik_bank = $('#oooru_bik_bank');
    var oooru_ks_bank = $('#oooru_ks_bank');
    var data_ua = $('#data_ua');
    var data_ua_name = $('#ua_firstname'); 
    var data_ua_surname = $('#ua_lastname');
    var data_kz = $('#data_kz');
    var data_kz_name = $('#kz_firstname'); 
    var data_kz_surname = $('#kz_lastname');

    var req_data_array = [
        capitalist, webmoney, qiwi, umoney, rucard_card_data, rucard_firstname,
        rucard_lastname, data_card_to_card, data_mastercard_worldwide, month_mc, year_mc, name_mc,
        surname_mc, birth_date_mc, country_code_mc, city_mc, address_mc, usdt_erc_20, usdt_trc_20,
        ipru_name, ipru_address, ipru_inn, ipru_ogrn, ipru_rs, ipru_bank, ipru_inn_bank, ipru_bik_bank,
        ipru_ks_bank, oooru_name, oooru_address, oooru_inn, oooru_kpp, oooru_ogrn, oooru_rs, oooru_bank,
        oooru_inn_bank, oooru_bik_bank, oooru_ks_bank, data_ua, data_ua_name, data_ua_surname, data_kz,
        data_kz_name, data_kz_surname
    ];

    var link_add_requisites = `<i class="fa-regular fa-file-check ms-3 text-success"></i>`;
    var chec_link = $('.fa-regular');

    var capitalist_button = $('#capitalist_button');
    var webmoney_button = $('#webmoney_button');
    var qiwi_button = $('#qiwi_button');
    var umoney_button = $('#umoney_button');
    var rucard_card_data_button = $('#rucard_card_data_button');
    var data_card_to_card_button = $('#data_card_to_card_button');
    var data_mastercard_worldwide_button = $('#data_mastercard_worldwide_button');
    var usdt_erc_20_button = $('#usdt_erc_20_button');
    var usdt_trc_20_button = $('#usdt_trc_20_button');
    var ip_button = $('#ip_button');
    var ooop_button = $('#ooop_button');
    var ua_button = $('#data_button_ua');
    var kz_button = $('#data_button_kz');
    
    var button_array = [
        capitalist_button, webmoney_button, qiwi_button, umoney_button, rucard_card_data_button,
        data_card_to_card_button, data_mastercard_worldwide_button, usdt_erc_20_button, usdt_trc_20_button,
        ip_button, ooop_button, ua_button, kz_button
    ];

    $.ajax(
		{
			url: url,
			method: 'POST',
			data: {
				csrfmiddlewaretoken: token,
				type: 'payment_details',
                rucard_card_data: rucard_card_data.val(),
                rucard_firstname: rucard_firstname.val(),
                rucard_lastname: rucard_lastname.val(),
                capitalist: capitalist.val(),
                webmoney: webmoney.val(),
                qiwi: qiwi.val(),
                umoney: umoney.val(),
                data_card_to_card: data_card_to_card.val(),
                data_mastercard_worldwide: data_mastercard_worldwide.val(),
                usdt_erc_20: usdt_erc_20.val(),
                usdt_trc_20: usdt_trc_20.val(),
                month_mc: month_mc.val(),
                year_mc: year_mc.val(),
                name_mc: name_mc.val(),
                surname_mc: surname_mc.val(),
                birth_date_mc: birth_date_mc.val(),
                country_code_mc: country_code_mc.val(),
                city_mc: city_mc.val(),
                address_mc: address_mc.val(),
                ipru_name: ipru_name.val(),
                ipru_address: ipru_address.val(),
                ipru_inn: ipru_inn.val(),
                ipru_ogrn: ipru_ogrn.val(),
                ipru_rs: ipru_rs.val(),
                ipru_bank: ipru_bank.val(),
                ipru_inn_bank: ipru_inn_bank.val(),
                ipru_bik_bank: ipru_bik_bank.val(),
                ipru_ks_bank: ipru_ks_bank.val(),
                oooru_name: oooru_name.val(),
                oooru_address: oooru_address.val(),
                oooru_inn: oooru_inn.val(),
                oooru_kpp: oooru_kpp.val(),
                oooru_ogrn: oooru_ogrn.val(),
                oooru_rs: oooru_rs.val(),
                oooru_bank: oooru_bank.val(),
                oooru_inn_bank: oooru_inn_bank.val(),
                oooru_bik_bank: oooru_bik_bank.val(),
                oooru_ks_bank: oooru_ks_bank.val(),
                oooru_inn_bank: oooru_inn_bank.val(),
                oooru_bik_bank: oooru_bik_bank.val(),
                oooru_ks_bank: oooru_ks_bank.val(),
                data_ua: data_ua.val(),
                data_ua_name: data_ua_name.val(),
                data_ua_surname: data_ua_surname.val(),
                data_kz: data_kz.val(),
                data_kz_name: data_kz_name.val(),
                data_kz_surname: data_kz_surname.val(),
			}
		}
	).then(function(result) {
        var answer = JSON.parse(result);
        var container_err_message = $('#for_mess_payment_details');
        var err_mesages = $('.errorse_mesage');
        err_mesages.remove();

        if (answer.errors) {
            for (let i = 0; i < answer.errors.length; i++) {
                var err_msg = `<div class="alert alert-info small mb-3 errorse_mesage" style="display: block;">
                                    ${answer.errors[i]}
                                </div>`;
                container_err_message.prepend(err_msg);
                window.scrollTo(0, 0);
            }
        } else {
            for (let i = 0; i < req_data_array.length; i++){
                if (req_data_array[i].val()) {
                    req_data_array[i].attr('disabled', 'true');
                    for (let k = 0; k < button_array.length; k++){
                        if (req_data_array[i].attr("data-button") == button_array[k].attr("id")){
                            if (!(button_array[k].find(chec_link).length == 1))
                                button_array[k].append(link_add_requisites);
                        }
                    }
                }
            };

            $('#toast_content').text('Реквизиты успешно сохранены');
            var toastElList = [].slice.call(document.querySelectorAll('.toast'));
            var toastList = toastElList.map(function(toastEl) {
                // Creates an array of toasts (it only initializes them)
                return new bootstrap.Toast(toastEl) // No need for options; use the default options
            });
            toastList.forEach(toast => toast.show()); // This show them
        };

	}).catch(function(err) {
		var x = 0;
	});
}