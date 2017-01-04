import React, { Component } from 'react';
import './EventMessages.scss';

class EventMessages extends Component {

  getMessages() {
    
    var messages = this.props.event.messages;

    if(!messages)
      return;
    
    var elements = [];

    for(var i = messages.length - 1; i >= 0; i--) {
      elements.push(<p key={i}>{messages[i]}</p>);
    }

    return elements;
  }

  render() {
    return (
      <div className={"EventMessages"}>
            {this.getMessages()}
      </div>
    );
  }
}

export default EventMessages;
