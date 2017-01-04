import React, { Component } from 'react';
import './EventNode.scss';

class EventNode extends Component {

  getIconElement() {

    if(this.props.event.isWaiting()) {
      return (
        <div className="icon spinner"></div>
      );
    }

    return (
      <i className={"icon mdi mdi-" + this.props.event.getIconName()} />
    );
  }

  render() {
    return (
      <div className={"EventNode " + this.props.alignment + " " + this.props.event.getColorClass()}>
        <span className="horizontal-line"></span>
        <span className="timeline-icon"></span>
        <div className="inner">
          <div className="header">
              {this.getIconElement()}
              <p className="title">{this.props.event.getTitle()}</p>
              <p className="subtitle">{this.props.event.getSubtitle()}</p>
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
