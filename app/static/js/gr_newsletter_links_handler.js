const apiKeyForm = document.getElementById('apikeyform').getElementsByClassName('form')[0];
apiKeyForm.addEventListener('submit', handleApiKeyForm);

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
    const availableNewslettersForm = document.getElementById('available_newsletters')
    Object.keys(data).forEach(function(key) {
      // console.log(key, dictionary[key]);
      var option = document.createElement("option");
      option.text = data[key];
      availableNewslettersForm.add(option);
    });

  }).catch((error) => console.log(error));
}
