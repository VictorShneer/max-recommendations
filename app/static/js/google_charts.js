google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart(graph_1_no_email,graph_1,conv_no_email_sum, conv_email_sum) {
  //первый график  - зависимость конверсии от общего количества визитов (с email, без email)
  const emailDots = [];
  const noEmailDots = [];
  const graph_1_no_email_array = eval(graph_1_no_email);
  const graph_1_array = eval(graph_1);
  let arrayToLoad = [['Count', 'Без email', 'с email']];

  graph_1_array.forEach((pairOfDots) => {
    noEmailDots.push(
      [parseFloat(pairOfDots[0]), parseFloat(pairOfDots[1]), null]
    );
  });
  graph_1_no_email_array.forEach((pairOfDots) => {
    emailDots.push(
      [parseFloat(pairOfDots[0]), null, parseFloat(pairOfDots[1])]
    );
  });
  arrayToLoad = arrayToLoad.concat(emailDots,noEmailDots);

  var data = google.visualization.arrayToDataTable(
      arrayToLoad
  );
  var options = {
    title: 'Зависимость конверсии от общего количества визитов (с) - с email, без email',
    hAxis: {title: 'Общее количество визитов', minValue: 0, maxValue: 10},
    vAxis: {title: 'Конверсия', minValue: 0, maxValue: 1000},
    legend: 'right',
    colors: ['#ff0000', '#0000ff']
  };

  var chart = new google.visualization.ScatterChart(document.getElementById('chart_div1'));

  chart.draw(data, options);

  /* второй график - зависимость конверсии от доли визитов с email в общем количестве визитов
  var data2 = google.visualization.arrayToDataTable([
    ['Count', ''],
    {% for line in graph_2 %}
      [{{line[0]}}, {{line[1]}}],
    {% endfor %}
  ]);

var options2 = {
    title: 'Зависимость конверсии от доли визитов с email (d/c)',
    hAxis: {title: '% количество визитов с email / общее количество визитов', minValue: 0, maxValue: 100},
    vAxis: {title: 'Конверсия', minValue: 0, maxValue: 1000},
    legend: 'none',
    colors: ['#3caa3c']
  };

  var chart2 = new google.visualization.ScatterChart(document.getElementById('chart_div2'));

  chart2.draw(data2, options2);

  третий график - зависимость конверсии от количества визитов с email

  var data3 = google.visualization.arrayToDataTable([
    ['Count', ''],
    {% for line in graph_3 %}
      [{{line[0]}}, {{line[1]}}],
    {% endfor %}
  ]);

var options3 = {
    title: 'Зависимость конверсии от количества визитов с email (d)',
    hAxis: {title: 'Количество визитов с email', minValue: 0, maxValue: 10},
    vAxis: {title: 'Конверсия', minValue: 0, maxValue: 1000},
    legend: 'none',
    colors: ['#3caa3c']
  };

  var chart3 = new google.visualization.ScatterChart(document.getElementById('chart_div3'));

  // chart3.draw(data3, options3); */

  //диаграмма
  var data_diag = google.visualization.arrayToDataTable([
    ['Источник', 'Доля в конверсии'],
    ['С email',     parseInt(conv_email_sum)],
    ['Без email',      parseInt(conv_no_email_sum)]
  ]);

  var options_diag = {
    title: 'Участие в конверсии источников с email и без email',
    is3D: true,
  };

  var chart_diag = new google.visualization.PieChart(document.getElementById('piechart_3d'));
  chart_diag.draw(data_diag, options_diag);

}
