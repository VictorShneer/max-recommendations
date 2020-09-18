$(document).ready(function(){

  const create_campaign_link = document.getElementById('create_campaign');
  create_campaign_link.addEventListener('click', drop_down_input_create_campaign);
  const send_gr_button = document.getElementById('sendGR');
  send_gr_button.addEventListener('click', send_to_gr_handler)

  function send_to_gr_handler(event){
    event.preventDefault()
    $noformsuccess = $('<p id="newcampaingform" style="color:green;">Начат процесс по загрузке контактов в GetResponse<p>')
    $noformfail = $('<p id="newcampaingform" style="color:red;">Что-то пошло не так..<p>')
    // get search contacts
    var contactsList = [];
    $('#target').children('div').each(function() {
        contactsList.push($( this ).context.innerText);
    });
    if(contactsList[0]==""){
      $('#newcampaingform').replaceWith('<p id="newcampaingform" style="color:red">Невозможно экспортировать 0 контактов</p>')
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
      _paq.push(['trackEvent', 'Documentary', 'Play', 'Thrive']);
      event.preventDefault()
      // Prevent redirection with AJAX for contact form
      var form = $('#analyticsform');
      var form_id = 'analyticsform';
      var url = '/analytics/getdata';
      var type = 'post';
      var formData = getContactFormData(form_id);

      // submit form via AJAX
      send_form(form, form_id, url, type, modular_ajax, formData);



  });

  function getContactFormData(form) {
      // creates a FormData object and adds chips text
      var formData = new FormData(document.getElementById(form));
      formData.append('integration_id', document.URL.split('/').pop());
      for (var [key, value] of formData.entries()) { console.log('formData', key, value);}
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
              target.innerHTML = ''
              if (data) {
                const unparsed_data = JSON.parse(data);
                unparsed_data.data.forEach(item => {
                output = `
                <div class="container">
                    <div class="row">
                        <div class="col">
                            ${item.Hash}
                        </div>
                    </div>
                </div>
                `;
                target.innerHTML += output
                });
                }
            else {
                console.log('NO DATAAAA');
              }
          },
          error: function(xhr) {console.log("error. see details below.");
              console.log(xhr.status + ": " + xhr.responseText);
          },
      }).done(function() {
        console.log('Hello world!');
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
      inputs = '<input type="text" placeholder="Название">\
                <input type="submit" value="Создать">';
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
