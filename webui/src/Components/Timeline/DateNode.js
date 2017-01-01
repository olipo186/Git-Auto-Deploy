import React, { Component } from 'react';
import './DateNode.scss';

class DateNode extends Component {
  constructor(props) {
    super(props);

    this.state = {
        date: props.date,
        first: props.first
    };
  }

  render() {
    return (
      <div className={"DateNode " + (this.state.first ? 'first' : '')}>
        <span className="horizontal-line"></span>
        <p className="date">{this.state.date}</p>
      </div>
    );
  }
}

export default DateNode;
