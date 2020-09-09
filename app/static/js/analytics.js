$(document).ready(function(){


  $('#submit').click(function(event){

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
              if (data) {
                const unparsed_data = JSON.parse(data);
                unparsed_data.data.forEach(item => {
                output = `
                <div class="container">
                    <div class="row">
                        <div class="col">
                            ${item.Email}
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

  // $('#sendGR').click(function(event){
  //
  //     event.preventDefault()
  //     // Prevent redirection with AJAX for contact form
  //     var form = $('#analyticsform');
  //     var form_id = 'analyticsform';
  //     var url = '/analytics/getdata123';
  //     var type = 'post';
  //     var formData = 'hui';
  //
  //     // submit form via AJAX
  //     send_form1(form, form_id, url, type, modular_ajax1, formData);
  // });
  //
  // function modular_ajax1(url, type, formData) {
  //     // Most simple modular AJAX building block
  //     $.ajax({
  //         url: url,
  //         type: type,
  //         data: formData,
  //         processData: false,
  //         contentType: false,
  //         beforeSend: function() {
  //             // show the preloader (progress bar)
  //             $('#form-response').html("<div class='progress'><div class='indeterminate'></div></div>");
  //         },
  //         complete: function () {
  //             // hide the preloader (progress bar)
  //             $('#form-response').html("");
  //         },
  //         success: function ( data ){
  //             if (data) {
  //               const unparsed_data = JSON.parse(data);
  //               unparsed_data.data.forEach(item => {
  //               output = `
  //               <div class="container">
  //                   <div class="row">
  //                       <div class="col">
  //                           ${item.Email}
  //                       </div>
  //                   </div>
  //               </div>
  //               `;
  //               target.innerHTML += output
  //               });
  //               }
  //           else {
  //               console.log('NO DATAAAA');
  //             }
  //         },
  //         error: function(xhr) {console.log("error. see details below.");
  //             console.log(xhr.status + ": " + xhr.responseText);
  //         },
  //     }).done(function() {
  //       console.log('Hello world!');
  //     });
  // };
  //
  // function send_form1(form, form_id, url, type, modular_ajax, formData) {
  //     // form validation and sending of form items
  //
  //     if ( form[0].checkValidity() && isFormDataEmpty(formData) == false ) { // checks if form is empty
  //         event.preventDefault();
  //
  //         // inner AJAX call
  //         modular_ajax1(url, type, formData);
  //
  //     }
  //     else {
  //       console.log('hui')
  //     }
  // }
});
