// Load the Visualization API and the controls package.
google.charts.load('current', {'packages':['corechart', 'controls']});

function drawTimeSeriesChart(timeSeriesData){
  // data prepare Sting dates to new Date obj
  timeSeriesData.data.forEach((item, i) => {
    item[0] = new Date(item[0]);
  });
  var data = new google.visualization.DataTable();
  data.addColumn('date', 'Date'); // Implicit domain label col.
  data.addColumn('number', 'goals_with_email');
  data.addColumn('number', 'goals_just_after_email');
  data.addRows(timeSeriesData.data);
  // Create a dashboard.
  var dashboard = new google.visualization.Dashboard(
      document.getElementById('dashboard_div'));

  var options = {
    title: 'Email эффект',
    legend: { position: 'top' },
  };


  var controlOptions = {
    filterColumnLabel: 'Date',
  }


  var chart = new google.visualization.ChartWrapper({
    'chartType': 'LineChart',
    'containerId': 'curve_chart',
    'options': options
  });

  var goalsTypeCategory = new google.visualization.ControlWrapper({
    'controlType': 'ChartRangeFilter',
    'containerId': 'filter_div',
    'options': controlOptions
  });

  goalsTypeCategory.setOption('ui.chartOptions',{
                        width: 1200,
                        height: 100})
  console.log(goalsTypeCategory.getOptions())
  dashboard.bind(goalsTypeCategory,chart);

  // Draw the dashboard.
  dashboard.draw(data);
}

function drawChart(conv_no_email_sum, conv_email_sum, goals_email_sum, goals_no_email_sum, visits_email_sum, visits_no_email_sum) {
  //первый график  - зависимость конверсии от общего количества визитов (с email, без email)
  const emailDots = [];
  const noEmailDots = [];
//  const graph_1_no_email_array = eval(graph_1_no_email);
//  const graph_1_array = eval(graph_1);
  let arrayToLoad = [['Count', 'Без email', 'с email']];

  console.log('goals_email_sum = '+goals_email_sum)
/*  graph_1_array.forEach((pairOfDots) => {
    noEmailDots.push(
      [parseFloat(pairOfDots[0]), parseFloat(pairOfDots[1]), null]
    );
  });
  graph_1_no_email_array.forEach((pairOfDots) => {
    emailDots.push(
      [parseFloat(pairOfDots[0]), null, parseFloat(pairOfDots[1])]
    );
  });
  arrayToLoad = arrayToLoad.concat(emailDots,noEmailDots);*/

  /*var data = google.visualization.arrayToDataTable(
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

  chart.draw(data, options);*/

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

  //вторая диаграмма - участие в количестве выполненных целей

  var data_diag2 = google.visualization.arrayToDataTable([
    ['Источник', 'Выполненные цели'],
    ['С email',     parseInt(goals_email_sum)],
    ['Без email',      parseInt(goals_no_email_sum)]
  ]);

  var options_diag2 = {
    title: 'Доля выполненных целей в визитах из email',
    is3D: true,
  };

  var chart_diag2 = new google.visualization.PieChart(document.getElementById('piechart_3d_goals'));
  chart_diag2.draw(data_diag2, options_diag2);

  var data_diag3 = google.visualization.arrayToDataTable([
    ['Источник', 'Выполненные цели'],
    ['С email',     parseInt(visits_email_sum)],
    ['Без email',      parseInt(visits_no_email_sum)]
  ]);

  var options_diag3 = {
    title: 'Доля визитов из email',
    is3D: true,
  };

  var chart_diag3 = new google.visualization.PieChart(document.getElementById('piechart_3d_visits'));
  chart_diag3.draw(data_diag3, options_diag3);

}
