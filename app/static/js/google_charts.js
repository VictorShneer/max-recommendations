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
  data.addColumn({'type': 'string', 'role': 'style' , 'opt_label':'send_on'});
  data.addColumn({'type': 'string', 'role': 'tooltip'});

  data.addRows(timeSeriesData.data);
  // Create a dashboard.
  var dashboard = new google.visualization.Dashboard(
      document.getElementById('dashboard_div'));

      /*  define the series object
       *  follows the standard 'series' option parameters, except it has two additonal parameters:
       *    hidden: true if the column is currently hidden
       *    altColor: changes the color of the legend entry (used to grey out hidden entries)
       */
      var series = {
          goals_with_email: {
              hidden: false,
              visibleInLegend: true,
              color: 'red'
          },
          goals_just_after_email: {
              hidden: false,
              visibleInLegend: true,
              color: 'green',
          },
      };


  var options = {
    series : series,
    title: 'Email эффект',
    legend: { position: 'top' },
    curveType: 'function',
    pointSize: 0.1,
    tooltip: { trigger: 'selection' },
  }

  var controlOptions = {
    filterColumnLabel: 'Date',
  }


  var chart = new google.visualization.ChartWrapper({
    'chartType': 'LineChart',
    'containerId': 'curve_chart',
    'options': options
  });

  var view = new google.visualization.DataView(data);
  var goalsTypeCategory = new google.visualization.ControlWrapper({
    'controlType': 'ChartRangeFilter',
    'containerId': 'filter_div',
    'options': controlOptions
  });

  goalsTypeCategory.setOption('ui.chartOptions',{
                        width: 1200,
                        height: 100})

  dashboard.bind(goalsTypeCategory,chart);
  // Draw the dashboard.
  dashboard.draw(data);

}

function drawChart(goals_hasnt_email, goals_has_email, goals_from_email) {

  //диаграмма
  var data_diag = google.visualization.arrayToDataTable([
    ['Источник', 'Количество выполненных целей'],
    ['email известен',     parseInt(goals_has_email)],
    ['email неизвестен',      parseInt(goals_hasnt_email)]
  ]);

  var options_diag = {
    title: 'Доля целей с известным и неизвестным email',
    is3D: true,
  };

  var chart_diag = new google.visualization.PieChart(document.getElementById('piechart_3d'));
  chart_diag.draw(data_diag, options_diag);

  //вторая диаграмма - доля целей непосредственно с email у тех, у кого он вообще известен
   var goals_emailknown_notfromemail = goals_has_email - goals_from_email
   var data_diag2 = google.visualization.arrayToDataTable([
    ['Источник', 'Выполненные цели'],
    ['Цели непосредственно после переходов с email',      parseInt(goals_from_email)],
    ['Цели пользователей с известным email не с переходов с email',     parseInt(goals_emailknown_notfromemail)]
  ]);

  var options_diag2 = {
    title: 'Доля целей с перехода из email',
    is3D: true,
  };

  var chart_diag2 = new google.visualization.PieChart(document.getElementById('piechart_3d_goals'));
  chart_diag2.draw(data_diag2, options_diag2);
}
