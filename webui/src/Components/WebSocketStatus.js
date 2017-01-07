import React, { Component } from 'react';
import './WebSocketStatus.scss';

class WebSocketStatus extends Component {
  render() {

    if(this.props.wsIsOpen && !this.props.wsIsAuthenticated)
      return (
        <div className="WebSocketStatus">
          Authenticating against {this.props.wsURI}
        </div>
      );

    if(this.props.wsIsRecovering)
      return (
        <div className="WebSocketStatus">
          Reconnecting to {this.props.wsURI}
        </div>
      );

    if(this.props.wsIsOpen)
      return (
        <div className="WebSocketStatus">
          Receiving real time updates from {this.props.wsURI}
        </div>
      );

    return null;
  }
}

export default WebSocketStatus;
