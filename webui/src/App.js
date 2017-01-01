import React, { Component } from 'react';
import './App.scss';
import Timeline from './Timeline';
import Navigation from './Navigation';

class App extends Component {
  constructor(props) {
    super(props);

    this.state = {
      events: []
    };
  }

  render() {
    return (
      <div className="App">
        <Navigation />
        <Timeline />
      </div>
    );
  }
}

export default App;
