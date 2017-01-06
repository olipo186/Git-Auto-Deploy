import React, { Component } from 'react';
import './Timeline.scss';
import axios from 'axios';
import Event from './Event';
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
    this.wsIsRecovering = false;
    this.wsPort = undefined;
  }

  componentDidMount() {
    this.fetchEventList();
    this.initUserNotification();
  }

  initUserNotification() {
    if(!('Notification' in window))
      return;

    // Not yet approved?
    if (Notification.permission === 'default') {

      // Request permission
      return Notification.requestPermission(function() {
        //console.log("Got permission!");
      });
    }
  }

  showUserNotification(event) {

    if(!('Notification' in window))
      return;

    if(Notification.permission !== "granted")
      return;

    // define new notification
    var n = new Notification(
        event.getSubtitle(),
        {
          'body': event.getTitle(),
          'tag' : "event-" + event.id
        }
    );

    // notify when shown successfull
    n.onshow = function () {
      console.log("onshow");
    };

    // remove the notification from Notification Center when clicked.
    n.onclick = function () {
        this.close();
        console.log("onclick");
    };

    // callback function when the notification is closed.
    n.onclose = function () {
      console.log("onclose");
    };

    // notification cannot be presented to the user, this event is fired if the permission level is set to denied or default.
    n.onerror = function () {
      console.log("onerror");
    };
  }

  fetchEventList() {

    var url = '/api/status';

    if (process.env.NODE_ENV === 'development') {
      url = 'https://10.0.0.1:8001/api/status';
    }

    axios.get(url)
      .then(res => {
        const events = res.data.events.map(obj =>  new Event(obj));
        this.wsPort = res.data['web-socket-port'];
        this.setState({ events: events, loaded: true });

        // Once we get to know the web socket port, we can make the web socket connection
        this.initWebsocketConnection();
      })
      .catch(err => {
        this.setState({loaded: false});
      });
      
  }

  addOrUpdateEvent(event) {

    this.setState((prevState, props) => {

      var newEvents = [];
      var inserted = false;

      for(var key in prevState.events) {
        if(prevState.hasOwnProperty(key))
          continue;
        var curEvent = prevState.events[key];

        if(curEvent.id === event.id) {
          newEvents.push(event);
          inserted = true;
        } else {
          newEvents.push(curEvent);
        }
      }

      if(!inserted) {
        newEvents.push(event);
      }

      return {
        events: newEvents
      }
    
    });
  }

  getEventWithId(id) {
    var self = this;

    for(var key in self.state.events) {

      if(self.state.hasOwnProperty(key))
        continue;

      var event = self.state.events[key];

      if(event.id === id)
        return event;

    }

    return undefined;
  }

  handleJSONMessage(data) {
    var event;

    if(data.type === "new-event") {

      event = new Event(data.event);
      this.addOrUpdateEvent(event);

    } else if(data.type === "event-updated") {

      event = new Event(data.event);
      this.addOrUpdateEvent(event);

    } else if(data.type === "event-success") {

      event = this.getEventWithId(data.id);

      if(event && event.type === "WebhookAction") {
        this.showUserNotification(event);
      }

    } else {
      console.log("Unknown event: " + data.type);
    }
  }

  getWebsocketURI() {
    if (process.env.NODE_ENV === "development") {
      return "wss://10.0.0.1:" + this.wsPort;
    }
    var scheme = window.location.protocol === "https" ? "wss" : "ws";
    return scheme + "://" + window.location.hostname + ":" + this.wsPort;
  }

  initWebsocketConnection() {
    var self = this;
    var uri = self.getWebsocketURI();

    self.wsSocket = new WebSocket(uri);
    self.wsSocket.binaryType = "arraybuffer";
    self.wsSocket.onopen = function() {

      self.wsIsOpen = true;

      if(self.wsIsRecovering) {
        self.wsIsRecovering = false;
        self.fetchEventList();
      }
    };

    self.wsSocket.onmessage = (e) => {
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
    };

    self.wsSocket.onclose = function() {

      self.wsSocket.close();
      self.wsSocket = null;
      self.wsIsOpen = false;
      self.wsIsRecovering = true;

      if(self.wsReconnectTimeout !== undefined) {
        clearTimeout(self.wsReconnectTimeout);
      }

      // Try to reconnect again after 2 seconds
      self.wsReconnectTimeout = setTimeout(function() {

        self.initWebsocketConnection();
        self.wsReconnectTimeout = undefined;
      }, 2000);
    };

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
