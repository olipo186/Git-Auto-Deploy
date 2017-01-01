import React, { Component } from 'react';
import './EventNode.scss';
import moment from 'moment';

class EventNode extends Component {
  constructor(props) {
    super(props);

    this.state = {
        event: props.event,
        alignment: props.alignment
    };
  }

  getColorClass() {

      if(this.state.event.type === "StartupEvent")
        return "green";

      if(this.state.event.type === "WebhookAction")
        return "blue";

      return "purple";
  }

  getTitle() {

      if(this.state.event.type === "StartupEvent")
        return "Startup";

      if(this.state.event.type === "WebhookAction")
        return "Webhook";

      return this.state.event.type;
  }

  getSubtitle() {

      if(this.state.event.type === "StartupEvent") {

        if(this.state.event.address)
          return "Listening on " + this.state.event.address + " port " + this.state.event.port;

        return "Starting up.."
      }

      if(this.state.event.type === "WebhookAction")
        return "Incoming request from " + this.state.event['client-address'];

      return this.state.event.type;
  }

  getDate() {
      return moment.unix(this.state.event.timestamp).format("YYYY-MM-DD");
  }

  getTime() {
      return moment.unix(this.state.event.timestamp).format("HH:mm");
  }

  getIconName() {

    if(this.state.event.success === false)
      return "alert"

    if(this.state.event.type === "StartupEvent")
      return "alert-circle";

    return "check";
  }

  getIconElement() {

    if(this.state.event.waiting === true) {
      return (
        <div className="icon spinner"></div>
      );
    }

    return (
      <i className={"icon mdi mdi-" + this.getIconName()} />
    );
  }

  render() {
    return (
      <div className={"EventNode " + this.state.alignment + " " + this.getColorClass()}>
        <span className="horizontal-line"></span>
        <span className="timeline-icon"></span>
        <div className="inner">
          <div className="header">
              {this.getIconElement()}
              <p className="title">{this.getTitle()}</p>
              <p className="subtitle">{this.getSubtitle()}</p>
          </div>
          <div className="body">
          {this.props.children}
          </div>
          <svg className="vertical-arrow" viewBox="0 0 10 30">
              <path d="M0,0 c0,5,0,5,5,10 c6,6,6,4,0,10 c-5,5,-5,5,-5,10" />
          </svg>
        </div>
      </div>
    );
  }
}

export default EventNode;
