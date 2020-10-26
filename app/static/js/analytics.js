$(document).ready(function(){

  const create_campaign_link = document.getElementById('create_campaign');
  create_campaign_link.addEventListener('click', drop_down_input_create_campaign);
  const send_gr_button = document.getElementById('sendGR');
  send_gr_button.addEventListener('click', send_to_gr_handler);
  const send_gr_ftp_button = document.getElementById('sendGRFtp');
  send_gr_ftp_button.addEventListener('click', send_ftp_gr_handler);
  const filter_choices_menu = document.querySelector('#filters_form ul');
  filter_choices_menu.addEventListener('change', show_filter_menu);

  // this function makes filter menu dynamic
  // user see only that filters that he choose
  function show_filter_menu(event){
    divs_display_config = []
    $('#filters_form li').each(function(){
      $checkbox = $(this)
      filter_name = $checkbox.find( "input" ).attr( "value" )
      if (  $checkbox.hasClass( 'multiselect-all' ) ){
        return;
      } else if (  $checkbox.hasClass( 'grmax-multiselect-selected' ) ){
        divs_display_config.push({filter_name:filter_name, settings:'show'});
      } else {
        divs_display_config.push({filter_name:filter_name, settings:'hide'});
      }
    });
    divs_display_config.map(  function (filter_name_setting){
      selector = `label[for=${filter_name_setting.filter_name}]`;
      target_div = $($(selector)[0].parentElement);
      target_div[filter_name_setting.settings]();
      if (filter_name_setting.settings == 'hide'){
        // diselect all on hidden element
        target_div.find( "li" ).each(function () {
          $(this).removeClass('grmax-multiselect-selected');
        })
        target_div.find( "option" ).each(function () {
          $(this).prop("selected", false);
        })
        target_div.find( "input" ).each(function () {
          $(this).prop("checked", false);
        })
        target_div.find( "button" ).each(function () {
          $(this).attr('title', 'None selected');
          $($(this).find('span')[0]).text('Не выбрано...');
        })
      }
   });
  }


  function send_ftp_gr_handler(event){
    event.preventDefault()
    $noformsuccess = $('<p id="newexternal" style="color:green;">Загрузка внешнего сегмента в GetResponse<p>')
    $noformfail = $('<p id="newexternal" style="color:red;">Что-то пошло не так.. Проверьте имя для сегмента. Допускаются только латинские буквы, цифры и нижнее подчеркивание<p>')
    // get search contacts
    var contactsList = [];
    $('#react-table-mount table tbody tr td:nth-child(2)').each(function() {
        contactsList.push($( this ).text());
    });
    if(contactsList.length == 0){
      $('#newexternal').replaceWith('<p id="newexternal" style="color:red">Сперва отфильтруйте контакты для импорта</p>')
      return -1
    };
    // get external segment name id
    external_name = $('#external_name_input').val()
    //send it to backend
    integration_id = window.location.href.split('/').pop()
    $.post('/analytics/ftp_search_contacts/' + integration_id, {
        external_name : external_name,
        contactsList : contactsList.join(),
      }).done(function(response) {
          $('#newexternal').replaceWith($noformsuccess);
      }).fail(function() {
          $('#newexternal').replaceWith($noformfail);
      });
  }
  
  // http API GR interface
  function send_to_gr_handler(event){
    event.preventDefault()
    $noformsuccess = $('<p id="newcampaingform" style="color:green;">Загрузка контактов в GetResponse<p>')
    $noformfail = $('<p id="newcampaingform" style="color:red;">Что-то пошло не так..<p>')
    // get search contacts
    var contactsList = [];
    $('#react-table-mount table tbody tr td:nth-child(2)').each(function() {
        contactsList.push($( this ).text());
    });
    if(contactsList.length == 0){
      $('#newcampaingform').replaceWith('<p id="newcampaingform" style="color:red">Сперва отфильтруйте контакты для импорта</p>')
      return -1
    };
    // get campaign id
    campaingId = $('#gr_campaigns').val()
    //send it to backend
    integration_id = window.location.href.split('/').pop()
    $.post('/analytics/send_search_contacts/' + integration_id, {
        campaignId : campaingId,
        contactsList : contactsList.join(),
      }).done(function(response) {
          $('#newcampaingform').replaceWith($noformsuccess);
      }).fail(function() {
          $('#newcampaingform').replaceWith($noformfail);
      });
  }

  $('#submit').click(function(event){

      event.preventDefault()
      // Prevent redirection with AJAX for contact form
      var form = $('#analyticsform');
      var form_id = 'analyticsform';
      var url = '/analytics/getdata';
      var type = 'post';
      var formData = getContactFormData(form_id);

      _paq.push(['trackEvent', 'Analytics', 'Submit']);
      // submit form via AJAX
      send_form(form, form_id, url, type, modular_ajax, formData);



  });

  function getContactFormData(form) {
      // creates a FormData object and adds chips text
      var formData = new FormData(document.getElementById(form));
      formData.append('integration_id', document.URL.split('/').pop());
      // for (var [key, value] of formData.entries()) { console.log('formData', key, value);}
      return formData
  }

  function send_form(form, form_id, url, type, modular_ajax, formData) {
      // form validation and sending of form items

      if ( form[0].checkValidity() && isFormDataEmpty(formData) == false ) { // checks if form is empty
          event.preventDefault();

          // inner AJAX call
          modular_ajax(url, type, formData);

      }
      else {
        console.log('hui')
      }
  }


  function isFormDataEmpty(formData) {
      // checks for all values in formData object if they are empty
      for (var [key, value] of formData.entries()) {
          if (key != 'csrf_token') {
              if (value != '' && value != []) {
                  return false;
              }
          }
      }
      return true;
  }

  function modular_ajax(url, type, formData) {
      // Most simple modular AJAX building block
      $.ajax({
          url: url,
          type: type,
          data: formData,
          processData: false,
          contentType: false,
          beforeSend: function() {
              // show the preloader (progress bar)
              $('#form-response').html("<div class='progress'><div class='indeterminate'></div></div>");
          },
          complete: function () {
              // hide the preloader (progress bar)
              $('#form-response').html("");
          },
          success: function ( data ){
              document.getElementById('search_count').innerHTML = ` ${data.data.length} контактов`;
              drawAnalyticsTable(data);
          },
          error: function(xhr) {console.log("error. see details below.");
              console.log(xhr.status + ": " + xhr.responseText);
          },
      }).done(function() {
        console.log('Done! Search table ready.');
      });
  };

  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrf_token);
          }
      }
  });

  function drop_down_input_create_campaign(event){
      event.preventDefault();
      $form = $("<form id='create_campaign_form'></form>");
      $noformsuccess = $('<p id="newcampaingform" style="color:green;">Успех! Перезагрузите страницу, чтобы выбрать новый список.<p>')
      $noformfail = $('<p id="newcampaingform" style="color:red;">Не удалось создать список. Попробуйте другое имя<p>')
      inputs = '<input class="form-control analytics-create-campaign" type="text" placeholder="Название">\
                <input class="grmax-btn-white" type="submit" value="Создать">';
      $form.append(inputs);
      $('#newcampaingform').replaceWith($form);
      $("#create_campaign_form").submit(function( event ) {
        event.preventDefault();
        create_gr_campaign($('#create_campaign_form :input').first().val());
      });

    }

  function create_gr_campaign(campaign_name){
    integration_id = window.location.href.split('/').pop()
    $.post('/analytics/create_gr_campaign/'+integration_id, {
        gr_campaign_name : campaign_name,
    }).done(function(response) {
        $('#create_campaign_form').replaceWith($noformsuccess);
    }).fail(function() {
        $('#create_campaign_form').replaceWith($noformfail);
    });
  }

});
