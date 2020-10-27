function make_a_call() {

  const data = { username: 'example' };

  fetch('https://dev.getresponseservices.ru/tracking/dev', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  .then(response => response.json())
  .then(data => {
    console.log('Success:', data);
  })
  .catch((error) => {
    console.error('Error:', error);
  });

};
