import React, { Component } from 'react';
import './EndNode.scss';

class EndNode extends Component {

  render() {
    return (
      <div className={"EndNode"}>
        <span className="horizontal-line"></span>
        <p className="date">{this.props.date}</p>
      </div>
    );
  }
}

export default EndNode;
