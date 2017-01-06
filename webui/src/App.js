import React, { Component } from 'react';
import './App.scss';
import Timeline from './Timeline';
import Navigation from './Navigation';

class App extends Component {
  render() {

    if(window.location.protocol !== "https:" && process.env.NODE_ENV !== 'development') {
      return (
        <div className="App">
          <div className="insecure-scheme">The Web UI is not available over HTTP. To use it; enable SSL, restart GAD and browse to this page using HTTPS.</div>
        </div>
      );
    }

    return (
      <div className="App">
        <Navigation />
        <Timeline />
      </div>
    );
  }
}

export default App;
