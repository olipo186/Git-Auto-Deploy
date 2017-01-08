import moment from 'moment';

class Event {

  constructor(event) {
    var self = this;
    self.event = event;

    for(var key in event) {
        if(!event.hasOwnProperty(key))
            continue;
        self[key] = event[key];
    }
  }

  getColorClass() {

      if(this.event.type === "StartupEvent")
        return "green";

      if(this.event.type === "WebhookAction")
        return "blue";

      if(this.event.type === "DeployEvent")
        return "blue";

      return "blue";
//      return "purple";
  }

  getTitle() {

      if(this.event.type === "StartupEvent")
        return "Startup";

      if(this.event.type === "WebhookAction")
        return "Webhook";

      if(this.event.type === "DeployEvent")
        return "Deploy";

      return this.event.type;
  }

  getSubtitle() {

      if(this.event.type === "StartupEvent") {

        if(this.isWaiting())
          return "Starting up.."

        return "Listening for incoming connections";
      }

      if(this.event.type === "WebhookAction") {
        if(this.event.messages.length)
          return this.event.messages[this.event.messages.length - 1]
        return "Incoming request from " + this.event['client-address'];
      }

      if(this.event.type === "DeployEvent")
        return this.event.name;

      return this.event.type;
  }

  getDate() {
      return moment.unix(this.event.timestamp).format("YYYY-MM-DD");
  }

  getTime() {
      return moment.unix(this.event.timestamp).format("HH:mm");
  }

  getIconName() {

    if(this.event.success === false)
      return "alert"

    if(this.event.type === "StartupEvent")
      return "alert-circle";

    return "check";
  }

  isWaiting() {
    return this.event.waiting;
  }
}

export default Event;
