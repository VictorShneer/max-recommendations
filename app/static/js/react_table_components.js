/** @jsx React.DOM */

class VisitData extends React.Component{
  render(){
    return(
      <td>{this.props.visit_data}</td>
    )
  }
}

class VisitRow extends React.Component {

  render() {
    const visits_data = [];
    const columnsOrder = [
    "ClientID",
    "Client identities",
    "Total goals complited",
    "Total visits",
    "Total Visits Email",
    "Total goals with Email",
    "Conversion (TG/TV)",
    "Email power proportion"];

    for(let columnName of columnsOrder) {
      visits_data.push(
        <VisitData visit_data={this.props.visit[columnName]} />
      );
    }
    return (
     <tr>
      {visits_data}
     </tr>
    );
  }
}

class HeaderVisitsTable extends React.Component{
  render(){
    return(
      <th>{this.props.header_name}</th>
    )
  }
}


class VisitsTable extends React.Component {
  render() {
    const rows = [];
    const headerNames = [];
    if(this.props.visits){
      this.props.visits.data.slice(0, 5).forEach((visit) => {
        rows.push(
          <VisitRow visit={visit} />
        );
      });

      this.props.visits.schema.fields.forEach((header_name) => {
        headerNames.push(
          <HeaderVisitsTable header_name={header_name.name} />
        );
      });
    }

    return (
      <table className="table table-bordered table-striped mb-0">
        <thead className="thead-dark">
          <tr>
            {headerNames}
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    );
  }
}

class SearchBar extends React.Component {
  constructor(props) {
      super(props);
      this.state = {value: this.props.default_start_date};
      // console.log(this.state.value);
      this.handleChange = this.handleChange.bind(this);
    }

  handleChange(event) {
    this.setState({value: event.target.value});
  }

  render() {

    return (
        <div className="container form-group row">
          <form onSubmit={() => {
            this.props.onSubmit(this.state.value);
            event.preventDefault();
          }}>
                <div className='form-search-date'>
                  <label for="example-date-input" className="col-2 col-form-label">
                    Выберите дату:
                  </label>
                  <input type="date" className="form-control col-2" value={this.state.value} onChange={this.handleChange} id="datepicker"/>
                </div>
            <input type="submit" value="Загрузить данные" className="btn grmax-btn"/>
          </form>
      </div>
    );
  }
}

class FilterableVisitsTable extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      visits : null,
      isLoading: false,
      error: null,
      url: '/metrika/'+this.props.atb+'/get_data?',
      start_date:this.props.default_start_date,

    };
    // &&!7^!^^! WTF
    this.fetch_metrika_view.bind(this.state.visits);
    this.fetch_metrika_view.bind(this.state.isLoading);
    this.fetch_metrika_view.bind(this.state.error);
    this.fetch_metrika_view.bind(this.state.url);
    this.fetch_metrika_view.bind(this.state.start_date);
    this.fetch_metrika_view.bind(this.state.goals);

    // console.log('---');
    // console.log(this.state.start_date);
    // console.log(this.state.goals);
    // console.log(this.state.url);
    // console.log('---');


  }

  fetch_metrika_view(date){
    this.setState({ isLoading: true });
    const url = this.state.url+'start_date='+date+"&goals="+getSelectedGoals()
    console.log(url)
    fetch(url)
        .then(response => {
          if (response.ok) {
            return response.json();
          } else {
            throw new Error('Нет данных за указанный период');
          }
        })
        .then(data => {
          // for table
          this.setState({visits: data, isLoading: false });
          // for graph
          drawChart(
            data.max_no_email_1graph,
            data.max_email_1graph,
            data.conv_no_email_sum,
            data.conv_email_sum
          );
        })
        .catch(error => this.setState({ error, isLoading: false }));
  }

  render() {

    const { visits, isLoading, error } = this.state;

    if (error) {
      console.log(error.message)
      alert('За указанный период нет данных');
    }

    if (isLoading) {
      return <p>Loading ...</p>;
    }

    return (

      <div>
        <SearchBar
            onSubmit={(date)=>this.fetch_metrika_view(date)}
            default_start_date={this.state.start_date}
        />
        <VisitsTable visits={this.state.visits} />
      </div>
    );
  }
}

function getSelectedGoals(){
  var select = document.getElementById('goals');
  var selected_goals = [...select.selectedOptions]
                     .map(option => option.value);
  return selected_goals;
}
React.render(<FilterableVisitsTable
                atb={document.getElementById('atb').textContent}
                default_start_date={document.getElementById('start_date').textContent}
                />,
  document.getElementById('mount-visits_table'));
