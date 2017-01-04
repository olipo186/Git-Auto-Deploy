import React, { Component } from 'react';
import './EventNode.scss';
import moment from 'moment';

class EventNode extends Component {

  getColorClass() {

      if(this.props.event.type === "StartupEvent")
        return "green";

      if(this.props.event.type === "WebhookAction")
        return "blue";

      return "purple";
  }

  getTitle() {

      if(this.props.event.type === "StartupEvent")
        return "Startup";

      if(this.props.event.type === "WebhookAction")
        return "Webhook";

      return this.props.event.type;
  }

  getSubtitle() {

      if(this.props.event.type === "StartupEvent") {

        if(this.isWaiting())
          return "Starting up.."

        return "Listening for incoming connections";
      }

      if(this.props.event.type === "WebhookAction") {
        if(this.props.event.messages.length)
          return this.props.event.messages[this.props.event.messages.length - 1]
        return "Incoming request from " + this.props.event['client-address'];
      }

      return this.props.event.type;
  }

  getDate() {
      return moment.unix(this.props.event.timestamp).format("YYYY-MM-DD");
  }

  getTime() {
      return moment.unix(this.props.event.timestamp).format("HH:mm");
  }

  getIconName() {

    if(this.props.event.success === false)
      return "alert"

    if(this.props.event.type === "StartupEvent")
      return "alert-circle";

    return "check";
  }

  isWaiting() {
    if(this.props.event.type === "StartupEvent") {
      if(this.props.event['ws-started'] !== true || this.props.event['http-started'] !== true) {
        return true;
      }
    } else if(this.props.event.waiting === true) {
        return true;
    }
    return false;
  }

  getIconElement() {

    if(this.isWaiting()) {
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
      <div className={"EventNode " + this.props.alignment + " " + this.getColorClass()}>
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
