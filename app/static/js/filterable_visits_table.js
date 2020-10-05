/** @jsx React.DOM */
React.render(<FilterableVisitsTable
                atb={document.getElementById('atb').textContent}
                default_start_date={document.getElementById('start_date').textContent}
                />,
  document.getElementById('mount-visits_table'));