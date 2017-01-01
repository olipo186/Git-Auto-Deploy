import React, { Component } from 'react';
import './Navigation.scss';

class Navigation extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="Navigation">
        <p className="title">Git-Auto-Deploy</p>
      </div>
    );
  }
}

export default Navigation;
