import React, { Component } from 'react';
import './EndNode.scss';

class EndNode extends Component {
  constructor(props) {
    super(props);

    this.state = {
        date: props.date
    };
  }

  render() {
    return (
      <div className={"EndNode"}>
        <span className="horizontal-line"></span>
        <p className="date">{this.state.date}</p>
      </div>
    );
  }
}

export default EndNode;
