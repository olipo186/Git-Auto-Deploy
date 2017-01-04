import React, { Component } from 'react';
import './Timeline.scss';
import axios from 'axios';
import EventNode from './Components/Timeline/EventNode';
import DateNode from './Components/Timeline/DateNode';
import EndNode from './Components/Timeline/EndNode';
import EventMessages from './Components/Timeline/EventMessages';
import moment from 'moment';

class Timeline extends Component {
  constructor(props) {
    super(props);

    this.state = {
      events: [],
      loaded: false
    };

    this.wsSocket = null;
    this.wsIsOpen = false;
  }

  componentDidMount() {
    this.fetchEventList();
    this.initWebsocketConnection();
  }

  fetchEventList() {

    var url = '/api/status';

    if (process.env.NODE_ENV === 'development') {
      url = 'http://10.0.0.1:8001/api/status';
    }

    axios.get(url)
      .then(res => {

        //const posts = res.data.data.children.map(obj => obj.data);
        const events = res.data.map(obj =>
          {
            //obj.key = obj.id;
            //console.log(obj);
            return obj;
          }
        );
        this.setState({ events: events, loaded: true });
      })
      .catch(err => {
        this.setState({loaded: false});
      });
      
  }

  handleJSONMessage(data) {

    if(data.type === "event-update") {

      this.setState((prevState, props) => {

        var newEvents = [];
        var inserted = false;

        for(var key in prevState.events) {
          if(prevState.hasOwnProperty(key))
            continue;
          var event = prevState.events[key];

          if(event.id === data.event.id) {
            newEvents.push(data.event);
            inserted = true;
          } else {
            newEvents.push(event);
          }
        }

        if(!inserted) {
          newEvents.push(data.event);
        }

        return {
          events: newEvents
        }
      
      });

    } else {
      console.log("Unknown event");
      console.log(data);
    }
  }

  initWebsocketConnection() {
    var self = this;

    var scheme = window.location.protocol == "https" ? "wss" : "ws";
    var uri = scheme + "://" + window.location.hostname + ":9000";

    if (process.env.NODE_ENV === "development") {
      uri = "ws://10.0.0.1:9000";
    }

    this.wsSocket = new WebSocket(uri);
    this.wsSocket.binaryType = "arraybuffer";

    this.wsSocket.onopen = function() {
      console.log("Connected!");
      this.wsIsOpen = true;
    }

    this.wsSocket.onmessage = function(e) {
      if (typeof e.data === "string") {
          try {
            var data = JSON.parse(e.data);
            self.handleJSONMessage(data);
          } catch(e) {
            console.error(e);
          }
      } else {
          var arr = new Uint8Array(e.data);
          var hex = '';
          for (var i = 0; i < arr.length; i++) {
            hex += ('00' + arr[i].toString(16)).substr(-2);
          }
          console.log("Binary message received: " + hex);
      }
    }

    this.wsSocket.onclose = function(e) {
      console.log("Connection closed.");
      this.wsSocket = null;
      this.wsIsOpen = false;
    }
  }

  /*
  function sendText() {
    if (isopen) {
        socket.send("Hello, world!");
        console.log("Text message sent.");               
    } else {
        console.log("Connection not opened.")
    }
  };
  function sendBinary() {
    if (isopen) {
        var buf = new ArrayBuffer(32);
        var arr = new Uint8Array(buf);
        for (i = 0; i < arr.length; ++i) arr[i] = i;
        socket.send(buf);
        console.log("Binary message sent.");
    } else {
        console.log("Connection not opened.")
    }
  };
  */

  getDate(timestamp) {
      return moment.unix(timestamp).format("YYYY-MM-DD");
  }

  getTimelineObjects() {
    var rows = [];
    var last_date = '';
    var events = this.state.events;

    rows.push(<EndNode key="now" />);  

    for (var i=events.length-1; i >= 0; i--) {
        var event = events[i];

        rows.push(<EventNode event={event} key={i} alignment={i%2===0 ? 'left' : 'right'} >
          <EventMessages event={event} />
        </EventNode>);

        var cur_date = this.getDate(event.timestamp);
        var next_date = "";
        if(i > 0)
          next_date = this.getDate(events[i-1].timestamp);

        if(next_date === cur_date)
          continue;

        if(cur_date !== last_date) {
          rows.push(<DateNode date={cur_date} key={cur_date} first={i===0} />);  
          last_date = cur_date;
        }
    }

    return rows;
  }

  render() {

    if(!this.state.loaded) {
      return (
        <div className="Timeline">
          <div className="status-message">Unable to connect</div>
        </div>
      );
    }

    return (
      <div className="Timeline">
        <div className="primary-view">
            {this.getTimelineObjects()}
        </div>
      </div>
    );
  }
}

export default Timeline;
