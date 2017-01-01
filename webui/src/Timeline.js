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
  }

  componentDidMount() {

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

        /*
        events.push({
            type: "WebhookAction",
            timestamp: 1483200720
        });

        events.push({
    "request-body": "{\"ref\":\"refs/heads/master\",\"before\":\"b24b817fc553be4abf425028e33398a6cf7da5bd\",\"after\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"created\":false,\"deleted\":false,\"forced\":false,\"base_ref\":null,\"compare\":\"https://github.com/olipo186/Git-Auto-Deploy/compare/b24b817fc553...7bb2fa6d10ca\",\"commits\":[{\"id\":\"465183e17af7b33f03047f53832ceea75140c29c\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Update README.md\\n\\nUpdate pip installing command\",\"timestamp\":\"2016-12-27T11:54:19+08:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/465183e17af7b33f03047f53832ceea75140c29c\",\"author\":{\"name\":\"Sunnyyoung\",\"email\":\"Sunnyyoung@users.noreply.github.com\",\"username\":\"Sunnyyoung\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]},{\"id\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Merge pull request #157 from Sunnyyoung/master\\n\\nUpdate README.md\",\"timestamp\":\"2016-12-27T11:50:05+01:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"author\":{\"name\":\"Oliver Poignant\",\"email\":\"oliver@poignant.se\",\"username\":\"olipo186\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]}],\"head_commit\":{\"id\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Merge pull request #157 from Sunnyyoung/master\\n\\nUpdate README.md\",\"timestamp\":\"2016-12-27T11:50:05+01:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"author\":{\"name\":\"Oliver Poignant\",\"email\":\"oliver@poignant.se\",\"username\":\"olipo186\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]},\"repository\":{\"id\":10534595,\"name\":\"Git-Auto-Deploy\",\"full_name\":\"olipo186/Git-Auto-Deploy\",\"owner\":{\"name\":\"olipo186\",\"email\":\"oliver@poignant.se\"},\"private\":false,\"html_url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"description\":\"Deploy your GitHub, GitLab or Bitbucket projects automatically on Git push events or webhooks using this small HTTP server written in Python. Continuous deployment in it's most simple form.\",\"fork\":false,\"url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"forks_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/forks\",\"keys_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/teams\",\"hooks_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/hooks\",\"issue_events_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/events\",\"assignees_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/tags\",\"blobs_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/languages\",\"stargazers_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/stargazers\",\"contributors_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/contributors\",\"subscribers_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/subscribers\",\"subscription_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/subscription\",\"commits_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/contents/{+path}\",\"compare_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/merges\",\"archive_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/downloads\",\"issues_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/deployments\",\"created_at\":1370546738,\"updated_at\":\"2016-12-27T09:44:12Z\",\"pushed_at\":1482835807,\"git_url\":\"git://github.com/olipo186/Git-Auto-Deploy.git\",\"ssh_url\":\"git@github.com:olipo186/Git-Auto-Deploy.git\",\"clone_url\":\"https://github.com/olipo186/Git-Auto-Deploy.git\",\"svn_url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"homepage\":\"http://olipo186.github.io/Git-Auto-Deploy/\",\"size\":622,\"stargazers_count\":528,\"watchers_count\":528,\"language\":\"Python\",\"has_issues\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":true,\"forks_count\":115,\"mirror_url\":null,\"open_issues_count\":11,\"forks\":115,\"open_issues\":11,\"watchers\":528,\"default_branch\":\"master\",\"stargazers\":528,\"master_branch\":\"master\"},\"pusher\":{\"name\":\"olipo186\",\"email\":\"oliver@poignant.se\"},\"sender\":{\"login\":\"olipo186\",\"id\":1056476,\"avatar_url\":\"https://avatars.githubusercontent.com/u/1056476?v=3\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/olipo186\",\"html_url\":\"https://github.com/olipo186\",\"followers_url\":\"https://api.github.com/users/olipo186/followers\",\"following_url\":\"https://api.github.com/users/olipo186/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/olipo186/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/olipo186/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/olipo186/subscriptions\",\"organizations_url\":\"https://api.github.com/users/olipo186/orgs\",\"repos_url\":\"https://api.github.com/users/olipo186/repos\",\"events_url\":\"https://api.github.com/users/olipo186/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/olipo186/received_events\",\"type\":\"User\",\"site_admin\":false}}",
    "timestamp": 1483187602.554847,
    "messages": [
      "Incoming request from 192.30.252.45:61279",
      "Handling the request with GitHubRequestParser",
      "Received 'push' event from GitHub",
      "Deploying",
      "Done"
    ],
    "request-headers": {
      "content-length": "7212",
      "x-github-event": "push",
      "x-github-delivery": "3ade9980-cc22-11e6-9efe-3be1665744c8",
      "x-hub-signature": "sha1=b73756e722ba28729aac624a48591fa83163e747",
      "user-agent": "GitHub-Hookshot/7676889",
      "host": "narpau.se:8001",
      "content-type": "application/json"
    },
    "client-port": 61279,
    "client-address": "192.30.252.45",
    "type": "WebhookAction",
    "id": 1
  });

    events.push( {
      "request-body": "{\"ref\":\"refs/heads/master\",\"before\":\"b24b817fc553be4abf425028e33398a6cf7da5bd\",\"after\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"created\":false,\"deleted\":false,\"forced\":false,\"base_ref\":null,\"compare\":\"https://github.com/olipo186/Git-Auto-Deploy/compare/b24b817fc553...7bb2fa6d10ca\",\"commits\":[{\"id\":\"465183e17af7b33f03047f53832ceea75140c29c\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Update README.md\\n\\nUpdate pip installing command\",\"timestamp\":\"2016-12-27T11:54:19+08:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/465183e17af7b33f03047f53832ceea75140c29c\",\"author\":{\"name\":\"Sunnyyoung\",\"email\":\"Sunnyyoung@users.noreply.github.com\",\"username\":\"Sunnyyoung\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]},{\"id\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Merge pull request #157 from Sunnyyoung/master\\n\\nUpdate README.md\",\"timestamp\":\"2016-12-27T11:50:05+01:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"author\":{\"name\":\"Oliver Poignant\",\"email\":\"oliver@poignant.se\",\"username\":\"olipo186\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]}],\"head_commit\":{\"id\":\"7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"tree_id\":\"c5ca854add997d6e6c840ddb37b89da26d9cc380\",\"distinct\":true,\"message\":\"Merge pull request #157 from Sunnyyoung/master\\n\\nUpdate README.md\",\"timestamp\":\"2016-12-27T11:50:05+01:00\",\"url\":\"https://github.com/olipo186/Git-Auto-Deploy/commit/7bb2fa6d10ca6f7eb9a1563bf932d37a97dac5f8\",\"author\":{\"name\":\"Oliver Poignant\",\"email\":\"oliver@poignant.se\",\"username\":\"olipo186\"},\"committer\":{\"name\":\"GitHub\",\"email\":\"noreply@github.com\",\"username\":\"web-flow\"},\"added\":[],\"removed\":[],\"modified\":[\"README.md\"]},\"repository\":{\"id\":10534595,\"name\":\"Git-Auto-Deploy\",\"full_name\":\"olipo186/Git-Auto-Deploy\",\"owner\":{\"name\":\"olipo186\",\"email\":\"oliver@poignant.se\"},\"private\":false,\"html_url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"description\":\"Deploy your GitHub, GitLab or Bitbucket projects automatically on Git push events or webhooks using this small HTTP server written in Python. Continuous deployment in it's most simple form.\",\"fork\":false,\"url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"forks_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/forks\",\"keys_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/keys{/key_id}\",\"collaborators_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/collaborators{/collaborator}\",\"teams_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/teams\",\"hooks_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/hooks\",\"issue_events_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues/events{/number}\",\"events_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/events\",\"assignees_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/assignees{/user}\",\"branches_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/branches{/branch}\",\"tags_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/tags\",\"blobs_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/blobs{/sha}\",\"git_tags_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/tags{/sha}\",\"git_refs_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/refs{/sha}\",\"trees_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/trees{/sha}\",\"statuses_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/statuses/{sha}\",\"languages_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/languages\",\"stargazers_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/stargazers\",\"contributors_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/contributors\",\"subscribers_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/subscribers\",\"subscription_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/subscription\",\"commits_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/commits{/sha}\",\"git_commits_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/git/commits{/sha}\",\"comments_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/comments{/number}\",\"issue_comment_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues/comments{/number}\",\"contents_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/contents/{+path}\",\"compare_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/compare/{base}...{head}\",\"merges_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/merges\",\"archive_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/{archive_format}{/ref}\",\"downloads_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/downloads\",\"issues_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues{/number}\",\"pulls_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/pulls{/number}\",\"milestones_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/milestones{/number}\",\"notifications_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/notifications{?since,all,participating}\",\"labels_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/labels{/name}\",\"releases_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/releases{/id}\",\"deployments_url\":\"https://api.github.com/repos/olipo186/Git-Auto-Deploy/deployments\",\"created_at\":1370546738,\"updated_at\":\"2016-12-27T09:44:12Z\",\"pushed_at\":1482835807,\"git_url\":\"git://github.com/olipo186/Git-Auto-Deploy.git\",\"ssh_url\":\"git@github.com:olipo186/Git-Auto-Deploy.git\",\"clone_url\":\"https://github.com/olipo186/Git-Auto-Deploy.git\",\"svn_url\":\"https://github.com/olipo186/Git-Auto-Deploy\",\"homepage\":\"http://olipo186.github.io/Git-Auto-Deploy/\",\"size\":622,\"stargazers_count\":528,\"watchers_count\":528,\"language\":\"Python\",\"has_issues\":true,\"has_downloads\":true,\"has_wiki\":true,\"has_pages\":true,\"forks_count\":115,\"mirror_url\":null,\"open_issues_count\":11,\"forks\":115,\"open_issues\":11,\"watchers\":528,\"default_branch\":\"master\",\"stargazers\":528,\"master_branch\":\"master\"},\"pusher\":{\"name\":\"olipo186\",\"email\":\"oliver@poignant.se\"},\"sender\":{\"login\":\"olipo186\",\"id\":1056476,\"avatar_url\":\"https://avatars.githubusercontent.com/u/1056476?v=3\",\"gravatar_id\":\"\",\"url\":\"https://api.github.com/users/olipo186\",\"html_url\":\"https://github.com/olipo186\",\"followers_url\":\"https://api.github.com/users/olipo186/followers\",\"following_url\":\"https://api.github.com/users/olipo186/following{/other_user}\",\"gists_url\":\"https://api.github.com/users/olipo186/gists{/gist_id}\",\"starred_url\":\"https://api.github.com/users/olipo186/starred{/owner}{/repo}\",\"subscriptions_url\":\"https://api.github.com/users/olipo186/subscriptions\",\"organizations_url\":\"https://api.github.com/users/olipo186/orgs\",\"repos_url\":\"https://api.github.com/users/olipo186/repos\",\"events_url\":\"https://api.github.com/users/olipo186/events{/privacy}\",\"received_events_url\":\"https://api.github.com/users/olipo186/received_events\",\"type\":\"User\",\"site_admin\":false}}",
      "timestamp": 1483187734.015505,
      "messages": [
        "Incoming request from 192.30.252.40:33912",
        "Handling the request with GitHubRequestParser",
        "Received 'push' event from GitHub",
        "Deploying",
        "Done"
      ],
      "request-headers": {
        "content-length": "7212",
        "x-github-event": "push",
        "x-github-delivery": "3ade9980-cc22-11e6-9efe-3be1665744c8",
        "x-hub-signature": "sha1=b73756e722ba28729aac624a48591fa83163e747",
        "user-agent": "GitHub-Hookshot/7676889",
        "host": "narpau.se:8001",
        "content-type": "application/json"
      },
      "client-port": 33912,
      "client-address": "192.30.252.40",
      "type": "WebhookAction",
      "id": 1
    });*/
    
        this.setState({ events: events, loaded: true });
      })
      .catch(err => {
        this.setState({loaded: false});
      });
  }

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
