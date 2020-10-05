/** @jsx React.DOM */

function drawAnalyticsTable(data){
	
	React.render(<VisitsTable visits = {data} />,
  	document.getElementById('react-table-mount'));

}
