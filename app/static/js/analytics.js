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
          // // first, scan the page for labels, and assign a reference to the label from the actual form element:
          // var labels = document.getElementsByTagName('LABEL');
          // for (var i = 0; i < labels.length; i++) {
          //     if (labels[i].htmlFor != '') {
          //          var elem = document.getElementById(labels[i].htmlFor);
          //          if (elem)
          //             elem.label = labels[i];
          //     }
          // }
          //
          // // then find all invalid input elements (form fields)
          // var Form = document.getElementById(form_id);
          // var invalidList = Form.querySelectorAll(':invalid');
          //
          // if ( typeof invalidList !== 'undefined' && invalidList.length > 0 ) {
          //     // errors were found in the form (required fields not filled out)
          //
          //     // for each invalid input element (form field) return error
          //     for (var item of invalidList) {
          //         M.toast({html: "Please fill the "+item.label.innerHTML+"", classes: 'bg-danger text-white'});
          //     }
          // }
          // else {
          //     M.toast({html: "Another error occured, please try again.", classes: 'bg-danger text-white'});
          // }
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
                console.log(data);

                 function GFG_FUN() {
                     var cols = [];

                     for (var i = 0; i < data.length; i++) {
                         for (var k in data[i]) {
                             console.log(j);
                           if (cols.indexOf(k) === -1) {

                                 // Push all keys to the array
                                 cols.push(k);
                             }
                         }
                     }

                     // Create a table element
                     var table = document.createElement("table");

                     // Create table row tr element of a table
                     var tr = table.insertRow(-1);

                     for (var i = 0; i < cols.length; i++) {

                         // Create the table header th element
                         var theader = document.createElement("th");
                         theader.innerHTML = cols[i];

                         // Append columnName to the table row
                         tr.appendChild(theader);
                     }

                     // Adding the data to the table
                     for (var i = 0; i < data.length; i++) {

                         // Create a new row
                         trow = table.insertRow(-1);
                         for (var j = 0; j < cols.length; j++) {
                             var cell = trow.insertCell(-1);

                             // Inserting the cell at particular place
                             cell.innerHTML = data[i][cols[j]];
                         }
                     }

                     // Add the newely created table containing json data
                     var el = document.getElementById("table");
                     el.innerHTML = "";
                     el.appendChild(table);
                 }
                 GFG_FUN()
              }
              else {
                console.log('NO DATAAAA');
              }
              // if ( !$.trim( data.feedback )) { // response from Flask is empty
              //     toast_error_msg = "An empty response was returned.";
              //     toast_category = "danger";
              // }
              // else { // response from Flask contains elements
              //     toast_error_msg = data.feedback;
              //     toast_category = data.category;
              // }
          },
          error: function(xhr) {console.log("error. see details below.");
              console.log(xhr.status + ": " + xhr.responseText);
              toast_error_msg = "An error occured";
              toast_category = "danger";
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


});
