const apiKeyForm = document.getElementById('apikeyform').getElementsByClassName('form')[0];
apiKeyForm.addEventListener('submit', handleApiKeyForm);
const availableNewslettersForm = document.getElementById('availablenewslettersform').getElementsByClassName('form')[0];
availableNewslettersForm.addEventListener('submit', handleAvailableNewslettersForm);
const availableLinksForm = document.getElementById('availablelinksform').getElementsByClassName('form')[0];
availableLinksForm.addEventListener('submit', handleAvailableLinksForm);
//"?utm_campaign=&utm_content=&utm_medium=&utm_source={{CONTACT `subscriber_email`}}&utm_term="

function handleAvailableLinksForm(event){
  event.preventDefault();
  const availableLinks = document.getElementById("available_links").value;
  console.log(availableLinks.split('\n'))
  availableLinks.split('\n').forEach((url) => {
    trimed_url = url.trim();
    $("#converted_links").append(trimed_url +
        "?utm_campaign=&utm_content=&utm_medium=&utm_source={{CONTACT `subscriber_email`}}&utm_term=\n");
  });
}
function handleAvailableNewslettersForm(event){
  event.preventDefault();
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
    if (response.ok) {
      return response.json();
    } else {
      alert('Что-то пошло не так. Скорее всего неверный ключ')
    }
  })
  .then((data) => {
    $("#available_links").empty();
    $("#available_links").val(data['links']);
  }).catch((error) => console.log(error));
}


function handleApiKeyForm(event){
  event.preventDefault();
  const key = document.getElementById("key").value;
  let response = fetch('/get_newsletters', {
    headers: {
      'Content-Type': 'application/json'
    },
    method : 'POST',
    body: JSON.stringify(key)
  }).then((response) => {
    if (response.ok) {
      return response.json();
    } else {
      alert('Что-то пошло не так. Скорее всего неверный ключ')
    }
  })
  .then((data) => {
    // console.log(data);
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
