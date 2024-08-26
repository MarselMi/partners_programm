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

var navPillsEl = document.querySelector('.nav-pills');
var buttonShowEl = navPillsEl.querySelectorAll('.nav-link');
var chatConteinerEl = document.querySelector('.chat-container');
var chatListEl = chatConteinerEl.querySelectorAll('.chat-list');
var presentTitle = document.querySelector('.header-unticket');
var ticketMessagesEl = document.getElementsByName('hideShowMessage');
var chatListItemEl = document.querySelectorAll('.chat-list-item');
var chatContainerEl = $('.messages-chat-container');
var chatBodyEl = $('#chat-msg');

function closeModalTicket() {
	var newTicketModal = $('#newTicketModal');
	var background = $('.modal-backdrop');
	newTicketModal.removeClass('show');
	newTicketModal.removeAttr('role');
	newTicketModal.removeAttr('style');
	newTicketModal.removeAttr('aria-modal');
	newTicketModal.prop('aria-hidden', true);
	background.remove();
};

function createNewTicket() {
	var newTicketTitle = $('#newTicketTitle');
	var newTicketCats = $('#newTicketCats');
	var newTicketText = $('#newTicketText');
	var formSendTicketEl = $('#formSendTicketElem');
	$.ajax(
		{
			url: url,
			method: 'POST',
			data: {
				csrfmiddlewaretoken: token,
				type: 'create_ticket',
				theme: newTicketTitle.val(),
				cat: newTicketCats.val(),
				text: newTicketText.val()
			}
		}
	).then(function(result) {
		var response = JSON.parse(result);
		var errorseDivEl = $('.errorse_mesage');
		if (errorseDivEl){
			errorseDivEl.remove();
		}
		if (response.error_message){
			var errMessageEl = `
								<div class="alert alert-info small mb-3 errorse_mesage" style="display: block;">
									${response.error_message}
								</div>
								`
			formSendTicketEl.prepend(errMessageEl);
		}else{
			var text = response.text;
			var ticket = response.ticket;
			var new_theme = ticket.theme;
			var new_status = ticket.status;
			var new_category = ticket.category;
			var new_type = ticket.type;	
			var user = response.user;
			var ticket_id = ticket.id;
			var message_time = response.time_message;

			if (new_category == "TECHNICAL"){
				new_category = "Технический отдел"
			}else if (new_category == "FINANCIAL"){
				new_category = "Финансовый отдел"
			}else if(new_category == "DIRECTOR"){
				new_category = "Обращение к директору"
			}else{
				new_category = "Сотрудничество"
			}
			
			addTicketToDOM(new_theme, new_status, new_category, user, new_type, ticket_id, text, message_time);
			closeModalTicket();
		}
	}).catch(function(err) {
		x = 0;
	});
};

function addTicketToDOM(theme, status, category, user, type, id, text, message_time) {
	var chatListEl = $('.chat-list-user');
	var chatListItemEl = document.querySelectorAll('.chat-list-item');
	for (let i = 0; i < chatListItemEl.length; i++) {
		chatListItemEl[i].classList.remove('active');
	}
	type = `${user} / ${category}`;
	var temp_status = `<div id="status=${id}" class="badge bg-success ms-auto ticket-status-${id}">
							Открыт
						</div>`;
	var status_button = `<div class="ms-auto">
							<button class="btn btn btn-light" type="button" name="closeTicket" data-bs-toggle="tooltip" data-bs-title="Закрыть обращение">
								<i class="fa-regular fa-circle-xmark"></i>
							</button>
						</div> <!-- /nav -->`;
	var el = `<div class="chat-list-item d-flex align-items-center pt-3 pb-3 ps-3 pe-3 border-bottom active" id="${id}" onclick="selectEl(event)">
					<div class="position-relative me-3">
						<span class="d-flex align-items-center justify-content-center text-bg-outline-secondary rounded-circle" style="width: 40px; height: 40px;">
							<i class="fa-regular fa-circle-user"></i>
						</span>
					</div> <!-- /avatar -->
					<div class="small flex-grow-1">
						<div class="d-flex align-items-start">
							<div class="me-2">
								${theme}
							</div>
							${temp_status}
						</div>
						<div class="text-muted">
							${type}
						</div>
					</div> <!-- /info -->
				</div> <!-- /item -->`;
	if (presentTitle){
		presentTitle.remove(); // удаляю шапку окна сообщения "Необходимо выбрать тикет"
	};
	$('#chat-msg').empty();
	$('.formCloseTicket').remove();
	$('.formSendMessage').remove();
	chatListEl.prepend(el);
	var chatContanerEl = $('.messages-chat-container');
	var chatHeaderElement = `
		<form action="" class="formCloseTicket" name="hideShowMessage" ticket-id="${id}">
			<!-- Шапка - указана тема подписки, партнер и отдел -->
			<div class="chat-header d-flex align-items-center border-bottom p-3">
				<input hidden value="${id}" name="ticketId">
				<div class="me-2">
					<div class="fw-bold">
						${theme}
					</div>
					<div class="small text-muted">
					${user} / ${category}
					</div>
				</div> <!-- /main-chat-msg-name -->
				<div id="button-${id}" class="ms-auto">
					<button id="inner-button-${id}" onclick="closeCurrentTicket(${id})" class="btn btn btn-light" type="button" name="closeTicket" data-bs-toggle="tooltip" data-bs-title="Закрыть обращение">
						<i class="fa-regular fa-circle-xmark"></i>
					</button>
				</div> <!-- /nav -->

			</div> <!-- /chat-header -->
		</form>`;
	
	var chatBody = `
		<div class="text-center small">
			<div class="badge text-bg-outline-secondary" name="date-messages">
				Сегодня
			</div> <!-- /badge -->
		</div> <!-- /date --> 

		<!-- Сообщения партнера  -->
		<div class="chat-body-item d-flex align-items-start flex-row-reverse mt-3 mb-3">
			<span class="d-flex align-items-center justify-content-center text-bg-outline-secondary rounded-circle" style="width: 40px; height: 40px;">
				<i class="fa-regular fa-circle-user"></i>
			</span>
			<div class="chat-body-item-content d-flex flex-column">
				<div class="chat-body-item-msg rounded-3 p-3 mb-1 right">
					${text}
				</div>
				<div class="small">
					<div class="small">${message_time}</div>
				</div>
			</div> <!-- /chat-body-item-content -->
		</div> <!-- /chat-body-item -->`;
	var messageSendEl = `
		<form action="" class="formSendMessage" name="hideShowMessage" ticket-id="${id}">
			<div id="message-ticket" class="chat-footer d-flex border-top p-3">	
				<input id="message-text-${id}" class="form-control me-3" placeholder="Введите сообщение здесь..." type="text" name="textTicket">
				
				<button onclick="sendMessageTicket(${id})" class="btn btn-primary" type="button" data-bs-toggle="tooltip" data-bs-title="Отправить Enter">
					<i class="fa-regular fa-paper-plane" style="margin-right: 2px;"></i>
				</button>

			</div> <!-- /chat-footer -->
		</form>`;
	chatBodyEl.append(chatBody);
	chatContanerEl.append(chatHeaderElement, chatBodyEl, messageSendEl);
};

function closeCurrentTicket(ticket_id) {
	var closeButton = $(`#button-${ticket_id}`);
	var innerButton = $(`#inner-button-${ticket_id}`);
	$.ajax(
		{
			url: url,
			method: 'POST',
			data: {
				csrfmiddlewaretoken: token,
				type: 'close',
				ticket_id: ticket_id
			}
		}
	).then(function(result) {
		var response = JSON.parse(result);
		var send_message = $(`.formSendMessage`);
		var ticket_status = $(`.ticket-status-${ticket_id}`);
		var ticket_status_my = $(`#status-${ticket_id}-my`);
		var ticket_status_sys = $(`#status-${ticket_id}-sys`);

		var tooltip_inner = $('.tooltip-inner');
		var tooltip_arrow = $('.tooltip-arrow');
		var new_ticket_status = `
			<div id="status-${ticket_id}" class="badge text-bg-outline-secondary ms-auto ticket-status-${ticket_id}">
				Закрыт
			</div>`;
		closeButton.remove();
		send_message.remove();
		tooltip_inner.remove();
		tooltip_arrow.remove();
		ticket_status.replaceWith(new_ticket_status);
		ticket_status_my.replaceWith(new_ticket_status);
		ticket_status_sys.replaceWith(new_ticket_status);

	}).catch(function(err) {
		x=0;
	});
};

function sendMessageTicket(ticket_id) {
	var ticket_message = $(`#message-text-${ticket_id}`);
	var chatWindowEl = $('#chat-msg');
	$.ajax(
		{
			url: url,
			method: 'POST',
			data: {
				csrfmiddlewaretoken: token,
				type: 'send',
				ticket_id: ticket_id,
				message: ticket_message.val()
			}
		}
	).then(function(result) {
		var response = JSON.parse(result);
		var errorseDivEl = $('.errorse_mesage');
		if (errorseDivEl){
			errorseDivEl.remove();
		}
		if (response.error_send){
			var errorseDivEl = `
				<div class="alert alert-info small mb-3 errorse_mesage" style="display: block;">
					${response.error_send}
				</div>`;
			chatWindowEl.prepend(errorseDivEl);
		}else{
			var text = response.text;
			var time = response.time;
			var date = response.date;
			var dateEl = `
				<div class="text-center small">
					<div class="badge text-bg-outline-secondary" name="date-messages">
						Сегодня
					</div> <!-- /badge -->
				</div> <!-- /date -->`;

			var message_el = `
				<div class="chat-body-item d-flex align-items-start flex-row-reverse mt-3 mb-3">
					<span class="d-flex align-items-center justify-content-center text-bg-outline-secondary rounded-circle" style="width: 40px; height: 40px;">
						<i class="fa-regular fa-circle-user"></i>
					</span>

					<div class="chat-body-item-content d-flex flex-column">
						<div class="chat-body-item-msg rounded-3 p-3 mb-1 right">
							${text}
						</div>

						<div class="small">
							<div class="small">${time}</div>
						</div>
					</div> <!-- /chat-body-item-content -->
				</div> <!-- /chat-body-item -->`;
			function checkDdate(chatBodyEl, dateEl){
				var b = chatBodyEl.children('.text-center');
				for (let i = 0; i < b.length; i++) {
					if (b[i].innerText == 'Сегодня') {
						return true;
					}
				}
				chatBodyEl.append(dateEl);
			};
	
			checkDdate(chatBodyEl, dateEl);
	
			chatBodyEl.append(message_el);
			var tooltip_inner = $('.tooltip-inner');
			var tooltip_arrow = $('.tooltip-arrow');
			tooltip_inner.remove();
			tooltip_arrow.remove();

			ticket_message.val('');
		}
	}).catch(function(err) {
		x = 0;
	});
};

function changeEl(event) {
	for (let i = 0; i < 3; i++) {
		if (buttonShowEl[i].classList.contains('active')) {
			chatListEl[i].removeAttribute('hidden');
		} else {
			chatListEl[i].setAttribute('hidden', 'true');
		}
	}
};

function selectEl(event) {
	var chatListItemEl = document.querySelectorAll('.chat-list-item');
	for (let i = 0; i < chatListItemEl.length; i++) {
		// отлавливаю всплытие события на элементе DIV контейнера тикета
		if (event.currentTarget == chatListItemEl[i]) {
			chatListItemEl[i].classList.add('active');
			// обьявляю переменную для получения идентификатора тикета
			let jsTicketId = event.currentTarget['id'];
			if (presentTitle){
				// удаляю шапку окна сообщения "Необходимо выбрать тикет"
				presentTitle.remove(); 
			};
			if (chatListItemEl[i].querySelector('span.badge')){
				// обновляю количество непрочитанных сообщ на главной странице
				var all_unread_messages = +$('.ticket_un_msgs').text();
				var ticket_unread = +chatListItemEl[i].querySelector('span.badge').textContent;
				$('.ticket_un_msgs').text(all_unread_messages - ticket_unread);
				// если количество непрочитанных сообщений совпадает, удаляю шапку непрочитанных соощений на главной странице
				$('.ticket_un_msgs').each(function(index, element){
					if(element.textContent == 'NaN'){
					    $('.ticket_un_msgs').remove();
					}
				});
				// удаляю указатель непрочитанных сообщений
				chatListItemEl[i].querySelector('span.badge').remove();
				$.ajax(
					{
						url: url,
						method: 'POST',
						data: {
							csrfmiddlewaretoken: token,
							type: 'readMsg',
							ticket_id: jsTicketId
						}
					}
				).then(function(result){
					var x = 1;
				}).catch(function(err) {
					var x = 0;
				});
			};
			chatBodyEl.empty();
			$('.formCloseTicket').remove();
			$('.formSendMessage').remove();
			$.ajax(
                {
                    url: url,
                    method: 'POST',
                    data: {
                        csrfmiddlewaretoken: token,
                        type: 'get_messages',
                        ticket_id: jsTicketId
                    }
                }
            ).then(function(result){
                var response = JSON.parse(result);
				var messages = response.messages;
				var ticket = response.ticket;
				var user = response.user;
				var openFormOutTicketElement = `
					<form action="" name="hideShowMessage" class="formCloseTicket" ticket-id="${jsTicketId}">
						<!-- Шапка - указана тема подписки, партнер и отдел -->
						<div class="chat-header d-flex align-items-center border-bottom p-3">
							<input hidden value="${jsTicketId}" name="ticketId">
							<div class="me-2">
								<div class="fw-bold">
									${ticket.theme}
								</div>
								<div class="small text-muted">
									${user}/${ticket.category}
								</div>
							</div> <!-- /main-chat-msg-name -->
							<div id="button-${jsTicketId}" class="ms-auto">
								<button id="inner-button-${jsTicketId}" onclick="closeCurrentTicket(${jsTicketId})" class="btn btn btn-light" type="button" name="closeTicket" data-bs-toggle="tooltip" data-bs-title="Закрыть обращение">
									<i class="fa-regular fa-circle-xmark"></i>
								</button>
							</div> <!-- /nav -->
						</div> <!-- /chat-header -->
					</form>`;
				var opendFormInTicketElement = `
					<form action="" name="hideShowMessage" class="formCloseTicket" ticket-id="${jsTicketId}">
						<!-- Шапка - указана тема подписки, партнер и отдел -->
						<div class="chat-header d-flex align-items-center border-bottom p-3">
							<input hidden value="${jsTicketId}" name="ticketId">
							<div class="me-2">
								<div class="fw-bold">
									${ticket.theme}
								</div>
								<div class="small text-muted">
								${ticket.category}/${user}  
								</div>
							</div> <!-- /main-chat-msg-name -->
							<div id="button-${jsTicketId}" class="ms-auto">
								<button id="inner-button-${jsTicketId}" onclick="closeCurrentTicket(${jsTicketId})" class="btn btn btn-light" type="button" name="closeTicket" data-bs-toggle="tooltip" data-bs-title="Закрыть обращение">
									<i class="fa-regular fa-circle-xmark"></i>
								</button>
							</div> <!-- /nav -->
						</div> <!-- /chat-header -->
					</form>`;
				var closedFormOutTicketElement = `
					<form action="" name="hideShowMessage" class="formCloseTicket" ticket-id="${jsTicketId}">
						<!-- Шапка - указана тема подписки, партнер и отдел -->
						<div class="chat-header d-flex align-items-center border-bottom p-3">
							<input hidden value="${jsTicketId}" name="ticketId">
							<div class="me-2">
								<div class="fw-bold">
									${ticket.theme}
								</div>
								<div class="small text-muted">
									${user}/${ticket.category}
								</div>
							</div> <!-- /main-chat-msg-name -->
						</div> <!-- /chat-header -->
					</form>`;
				var closedFormInTicketElement = `
					<form action="" name="hideShowMessage" class="formCloseTicket" ticket-id="${jsTicketId}">
						<!-- Шапка - указана тема подписки, партнер и отдел -->
						<div class="chat-header d-flex align-items-center border-bottom p-3">
							<input hidden value="${jsTicketId}" name="ticketId">
							<div class="me-2">
								<div class="fw-bold">
									${ticket.theme}
								</div>
								<div class="small text-muted">
								${ticket.category}/${user}  
								</div>
							</div> <!-- /main-chat-msg-name -->
						</div> <!-- /chat-header -->
					</form>`;
				
				messages.forEach((message) => {
					if (message.date_day){
						var dateEl = `
							<div class="text-center small">
								<div class="badge text-bg-outline-secondary" name="date-messages">
									${message.date_day}
								</div> <!-- /badge -->
							</div> <!-- /date -->`;
						chatBodyEl.append(dateEl);
					}
					if (message.author_id) {
						var userMessageEl = `
							<div class="chat-body-item d-flex align-items-start flex-row-reverse mt-3 mb-3">
								<span class="d-flex align-items-center justify-content-center text-bg-outline-secondary rounded-circle" style="width: 40px; height: 40px;">
									<i class="fa-regular fa-circle-user"></i>
								</span>

								<div class="chat-body-item-content d-flex flex-column">
									<div class="chat-body-item-msg rounded-3 p-3 mb-1 right">
										${message.text.replace(/\n/g,'<br/>')}
									</div>

									<div class="small">
										<div class="small">${message.date_hour}</div>
									</div>
								</div> <!-- /chat-body-item-content -->
							</div> <!-- /chat-body-item -->`;
						chatBodyEl.append(userMessageEl);
					}else{
						var images = '';
						if(message.image_1){
							images += `<div class="chat-body-item-msg rounded-3 p-3 mb-1">
											<img class="img-fluid" src="https://cdn-offers.offering.pro/media/${message.image_1}">
										</div>`;
						};
						if(message.image_2){
							images += `<div class="chat-body-item-msg rounded-3 p-3 mb-1">
											<img class="img-fluid" src="https://cdn-offers.offering.pro/media/${message.image_2}">
										</div>`;
						};
						if(message.image_3){
							images += `<div class="chat-body-item-msg rounded-3 p-3 mb-1">
											<img class="img-fluid" src="https://cdn-offers.offering.pro/media/${message.image_3}">
										</div>`;
						};
						if(message.image_4){
							images += `<div class="chat-body-item-msg rounded-3 p-3 mb-1">
											<img class="img-fluid" src="https://cdn-offers.offering.pro/media/${message.image_4}">
										</div>`;
						};
						if(message.image_5){
							images += `<div class="chat-body-item-msg rounded-3 p-3 mb-1">
											<img class="img-fluid" src="https://cdn-offers.offering.pro/media/${message.image_5}">
										</div>`;
						};
						
						var managerMessageEl = `
							<div class="chat-body-item d-flex align-items-start mt-3 mb-3">
								<span class="d-flex align-items-center justify-content-center bg-info text-white rounded-circle" style="width: 40px; height: 40px;">
									<i class="fa-regular fa-circle-info"></i>
								</span>

								<div class="chat-body-item-content d-flex flex-column">
									${images}
									<div class="chat-body-item-msg rounded-3 p-3 mb-1">
										${message.text.replace(/\n/g,'<br/>')}
									</div>

									<div class="small">
										<div class="small">${message.date_hour}</div>
									</div>
								</div> <!-- /chat-body-item-content -->
							</div> <!-- /chat-body-item -->`;
						chatBodyEl.append(managerMessageEl);
					}
				});

				var sendOpenMessageEl = `
					<form action="" name="hideShowMessage" class="formSendMessage" ticket-id="${jsTicketId}">
						<div id="message-ticket-${jsTicketId}" class="chat-footer d-flex border-top p-3">
							<input id="message-text-${jsTicketId}" class="form-control me-3" placeholder="Введите сообщение здесь..." type="text" name="textTicket">
							<button onclick="sendMessageTicket(${jsTicketId})" class="btn btn-primary" type="button" data-bs-toggle="tooltip" data-bs-title="Отправить Enter">
								<i class="fa-regular fa-paper-plane" style="margin-right: 2px;"></i>
							</button>
						</div> <!-- /chat-footer -->
					</form>`;
										
				if (ticket.status == "OPEN" && ticket.type == "OUT"){
					$('.messages-chat-container').append(openFormOutTicketElement, chatBodyEl, sendOpenMessageEl);	
				}else if(ticket.status == "OPEN" && ticket.type == "IN"){
					$('.messages-chat-container').append(opendFormInTicketElement, chatBodyEl, sendOpenMessageEl);
				}else if(ticket.status == "CLOSE" && ticket.type == "OUT"){
					$('.messages-chat-container').append(closedFormOutTicketElement, chatBodyEl);
				}else if(ticket.status == "CLOSE" && ticket.type == "IN"){
					$('.messages-chat-container').append(closedFormInTicketElement, chatBodyEl);
				};

				$('.formCloseTicket').on('keyup keypress', function(e) {
					var keyCode = e.keyCode || e.which;
					if (keyCode === 13) {
						e.preventDefault();
						return false;
					}
				});

				var formSendMessage = $('.formSendMessage');
				for (let i = 0; i < formSendMessage.length; i++){
					formSendMessage.on('keyup keypress', function(e) {
						var keyCode = e.keyCode || e.which;
						if (keyCode === 13) {
							e.preventDefault();
							return false;
						}
					});
				};
				function scrolling() {
					$('#chat-msg').animate({scrollTop: $('#chat-msg').get(0).scrollHeight}, 1000);
				};
				scrolling();
            }).catch(function(err) {
                x = 0;
            });
		}else {
			chatListItemEl[i].classList.remove('active');
		}
	}
};

$('#formSendTicket').on('keyup keypress', function(e) {
	var keyCode = e.keyCode || e.which;
	if (keyCode === 13) {
		e.preventDefault();
		return false;
	}
});
