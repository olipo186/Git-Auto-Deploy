import React, { Component } from 'react';
import './DateNode.scss';

class DateNode extends Component {

  render() {
    return (
      <div className={"DateNode " + (this.props.first ? 'first' : '')}>
        <span className="horizontal-line"></span>
        <p className="date">{this.props.date}</p>
      </div>
    );
  }
}

export default DateNode;
