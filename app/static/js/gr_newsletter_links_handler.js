const apiKeyForm = document.getElementById('apikeyform').getElementsByClassName('form')[0];
apiKeyForm.addEventListener('submit', handleApiKeyForm);
const availableNewslettersForm = document.getElementById('availablenewslettersform').getElementsByClassName('form')[0];
availableNewslettersForm.addEventListener('submit', handleAvailableNewslettersForm);
const availableLinksForm = document.getElementById('availablelinksform').getElementsByClassName('form')[0];
availableLinksForm.addEventListener('submit', handleAvailableLinksForm);
anableKeyForm  = document.getElementById('enable_key_form_button')
anableKeyForm.addEventListener('click', enableKeyFormHandler)

function enableKeyFormHandler(event){
  $('#apikeyform form input#key.form-control').removeAttr('disabled');
  $("#available_links").empty();
  $("#available_newsletters").empty();
  $("#key").val('');
}
function handleAvailableLinksForm(event){
  //
  event.preventDefault();
  const selectedLinks = $("#available_links").val();
  if(!selectedLinks){
    $('#info').replaceWith( '<p style="color:red"> Стоп! Сначала выберите ссылки для оборачивания </p>');
    return -1
  }
  const id = $('#available_links').attr('newsletter_id')
  const key = document.getElementById("key").value;
  let response = fetch('/post_wrapped_newsletter',{
    headers: {
      'Content-Type':'application/json'
    },
    method:"POST",
    body: JSON.stringify({newsletterId:id, links:selectedLinks, key:key})
  }).then((response) => {
    event.submitter.disabled=false;
    if (response.ok){
      $('#info').replaceWith( '<p style="color:green">\
            В GetResponse создано письмо с новыми ссылками\
                                    </p>' );
    } else {
      $('#info').replaceWith( '<p style="color:red">\
                 Ошибка при попытке создания письма :( \
                                          </p>' );
    }
  }).catch((error) => console.log(error));
}

function handleAvailableNewslettersForm(event){
  event.preventDefault();
  event.submitter.disabled = true;
  const e = document.getElementById("available_newsletters");
  const id = e.options[e.selectedIndex].id;
  const key = document.getElementById("key").value;
  let response = fetch('/get_newsletter_links', {
    headers: {
      'Content-Type': 'application/json'
    },
    method : 'POST',
    body: JSON.stringify({key:key,newsletterId:id})
  }).then((response) => {
    event.submitter.disabled = false;
    if (response.ok) {
      return response.json();
    } else {
      alert('Что-то пошло не так... Проверьте ключ')
    }
  })
  .then((data) => {
    $("#available_links").empty();
    $("#available_links").attr('newsletter_id',id);
    const available_links_form = document.getElementById('available_links');
    Object.keys(data).forEach(function(key, value) {
      var option = document.createElement("option");
      option.text = key;
      option.id = value;
      available_links_form.add(option);
    });
  }).catch((error) => console.log(error));
}


function handleApiKeyForm(event){
  event.preventDefault();
  event.submitter.disabled = true;

  const key = document.getElementById("key").value;
  let response = fetch('/get_newsletters', {
    headers: {
      'Content-Type': 'application/json'
    },
    method : 'POST',
    body: JSON.stringify(key)
  }).then((response) => {
    event.submitter.disabled = false;
    if (response.ok) {
      $('#apikeyform form input#key.form-control').attr('disabled', 'disabled');
      return response.json();
    } else {
      alert('Что-то пошло не так. Скорее всего неверный ключ')
    }
  })
  .then((data) => {
    $("#available_newsletters").empty();
    const availableNewslettersForm = document.getElementById('available_newsletters');
    Object.keys(data).forEach(function(key) {
      var option = document.createElement("option");
      option.text = data[key]['data'];
      option.id = data[key]['meta'];
      availableNewslettersForm.add(option);
    });

  }).catch((error) => console.log(error));

}
