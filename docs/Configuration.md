# Command line options and environment variables

```Git-Auto-Deploy``` supports a number of configurable options. Some of them are available using command line options, where others are only configurable from the config file. Below is a list of the options made available from the command line. Every command line option has also a corresponding environment variable. In the cases where a corresponding config file attribute is available, that attribute name is listed.

There is also support for supplying configuration options for up to one repository using environmetn variables. Variable names and descriptios are available in the section (Repository configuration using environment variables)[#eepository-configuration-using-environment-variables].

The list of available command line options can also be seen by invoke the application with the argument ```--help```.

Command line option    | Environment variable | Config attribute | Description
---------------------- | -------------------- | ---------------- | --------------------------
--daemon-mode (-d)     | GAD_DAEMON_MODE      |                  | Run in background (daemon mode)
--quiet (-q)           | GAD_QUIET            |                  | Supress console output
--config (-c) <path>   | GAD_CONFIG           |                  | Custom configuration file
--pid-file <path>      | GAD_PID_FILE         | pidfilepath      | Specify a custom pid file
--log-file <path>      | GAD_LOG_FILE         | logfilepath      | Specify a log file
--host <host>          | GAD_HOST             | host             | Address to bind to
--port <port>          | GAD_PORT             | port             | Port to bind to
--ssh-keyscan          | GAD_SSH_KEYSCAN      |                  | Scan repository hosts for ssh keys and add them to $HOME/.ssh/known_hosts

# Configuration file options
The configuration file is formatted according to a `JSON` inspired format, with the additional feature of supporting inline comments. The possible root elements are 
as follow:

 - **pidfilepath**: The path where `pid` files are kept.
 - **logfilepath**: To enable logging, set this to a valid file path.
 - **log-level**: Sets the threshold for the log output. Default value is NOTSET (all details). Recommended value is INFO (less details).
 - **host**: What IP address to listen on.
 - **port**: The port for the web server to listen on.
 - **global_deploy**: An array of two specific commands or path to scripts
   to be executed for all repositories defined:
    - `[0]` = The pre-deploy script.
    - `[1]` = The post-deploy script.
 - **repositories**: An array of repository configurations.

## Repositories
Repository configurations are comprised of the following elements:

 - **url**: The URL to the repository.
 - **match-url**: An alternative URL used when matching incoming webhook requests (see https://github.com/olipo186/Git-Auto-Deploy/pull/148) 
 - **branch**: The branch which will be checked out.
 - **remote**: The name of the remote to use.
 - **path**: Path to clone the repository to. If omitted, the repository won't
   be cloned, only the deploy scripts will be executed.
 - **deploy**: A command to be executed. If `path` is set, the command is 
   executed after a successfull `pull`.
 - **payload-filter**: A list of inclusive filters/rules that is applied to the request body of incoming web hook requests and determines whether the deploy command should be executed or not. See section *Filters* for more details.
 - **header-filter**: A set of inclusive filters/rules that is applied to the request header of incoming web hook requests and determines whether the deploy command should be executed or not. See section *Filters* for more details.
 - **secret-token**: The secret token set for your webhook (currently only implemented for [GitHub](https://developer.github.com/webhooks/securing/) and GitLab)
 - **prepull**: A command to execute immediately before the `git pull`.  This command could do something required for the ``git pull`` to succeed such as changing file permissions. 
 - **postpull**: A command to execute immediately after the `git pull`.  After the **prepull** command is executed, **postpull** can clean up any changes made.

## Filters
*(Currently only supported for GitHub and GitLab)*

With filters, it is possible to trigger the deploy only if a set of specific criterias are met. The filter can be applied to the web hook request header (if specified using the *header-filter* option) or to the request body (*payload-filter*).

### Allow web hooks with specific header values only (header-filter)

Some Git providers will add custom HTTP headers in their web hook requests when sending them to GAD. Using a *header-filter*, you can configure GAD to only process web hooks that has a specific HTTP header specified.

For example, if you'd like to only process requests that has the *X-Event-Key* header set to the value *pullrequest:fulfilled*, you could use the following config;

```json
{
  ...
  "repositories": [
    {
      ...
      "header-filter": {
          "X-Event-Key": "pullrequest:fulfilled"
      }
    }
  ]
}
```

If a header name is specified but with the value set to true, any request that has the header specified will pass without regard to the header value.

```json
{
  ...
  "repositories": [
    {
      ...
      "header-filter": {
          "X-Event-Key": true
      }
    }
  ]
}
```

### Allow web hooks with specific payload only (payload-filter)

A web hook request typically contains a payload, or a request body, made up of a JSON object. The JSON object in the request body will follow a format choosen by the Git server. Thus, it's format will differ depending on whether you are using GitHub, GitLab, Bitbucket or any other Git provider.

A *payload-filter* can be used to set specific criterias for which incoming web hook requests should actually trigger the deploy command. Filter can be setup to only trigger deploys when a commit is made to a specific branch, or when a pull request is closed and has a specific destination branch.

Since the format of the payload differs depending on what Git provider you are using, you'll need to inspect the web hook request format yourself and write a filter that matches its structure.

To specify a filter that should be applied further down the object tree, a dot notation (".") is used. For example, if the request body looks like this;
```json
{
  "action": "opened",
  "number": 69,
  "pull_request": {
    "url": "https://api.github.com/repos/olipo186/Git-Auto-Deploy/pulls/69",
    "id": 61793882,
    "html_url": "https://github.com/olipo186/Git-Auto-Deploy/pull/69",
    "diff_url": "https://github.com/olipo186/Git-Auto-Deploy/pull/69.diff",
    "patch_url": "https://github.com/olipo186/Git-Auto-Deploy/pull/69.patch",
    "issue_url": "https://api.github.com/repos/olipo186/Git-Auto-Deploy/issues/69",
    "number": 69,
    "state": "open",
    "locked": false,
    "title": "Refactoring. Fixed some imminent issues.",
    "user": {
      "login": "olipo186",
      "id": 1056476,
      "avatar_url": "https://avatars.githubusercontent.com/u/1056476?v=3",
      "gravatar_id": "",
      ...
  },
  ...
}
```

You could specify the following filter, which would only trigger on pull requests created by olipo186.

```json
{
  ...
  "repositories": [
    {
      ...
      "payload-filter": [
        {
          "action": "opened",
          "pull_request.user.login": "olipo186"
        }
      ]
    }
  ]
}
```

## Legacy filters (older format)

For example, deploy on `push` to the `master` branch only, ignore other branches.

Filters are defined by providing keys/values to be looked up in the original 
data sent by the web hook. 

For example, GitLab web hook data looks like this:

```json
 {
  "object_kind":"build",
  "ref":"master",
  "tag":false,
  ...
 }
```

A filter can use `object_kind` and `ref` attributes for example to execute the
deploy action only on a `build` event on the `master` branch.

### Examples

#### GitHub

The following example will trigger when a pull request with **master** as base is closed. The command `./prepull` and `./postpull` will execute immediately before and after the pull
```json
{
  "host": "0.0.0.0",
  "port": 8080,
  "global_deploy": [
    "echo Pre-deploy script",
    "echo Post-deploy script"
  ],
  "repositories": [
    {
      "url": "https://github.com/olipo186/Git-Auto-Deploy.git",
      "branch": "master",
      "remote": "origin",
      "path": "~/repositories/Git-Auto-Deploy",
      "deploy": "echo deploying",
      "prepull": "chmod u+w config.json",
      "postpull": "chmod u-w config.json",
      "filters": [
        {
            "action": "closed",
            "pull_request": true,
            "pull_request.base.ref": "master"
        }
      ]
    }
  ]
}
```

#### GitLab
*(Note: the filter examples below are valid for GitLab)*

Execute pre-deploy script, don't `pull` the repository but execute a deploy
script, and finish with a post-deploy script. Execute only for `push` events on
the `master` branch.

```json
{
  "pidfilepath": "~/.gitautodeploy.pid",
  "host": "0.0.0.0",
  "port": 8080,
  "global_deploy": [
    "echo Pre-deploy script",
    "echo Post-deploy script"
  ],
  "repositories": [
    {
      "url": "http://gitlab/playground/hooktest.git",
      "deploy": "echo deploying",
      "filters": [
        {
          "object_kind": "push",
          "ref": "refs/heads/master"
        }
      ]
    }
  ]
}
```

Clone repository on `push` to `master`.

```json
{
  "pidfilepath": "~/.gitautodeploy.pid",
  "host": "0.0.0.0",
  "port": 8080,
  "repositories": [
    {
      "url": "http://gitlab/playground/hooktest.git",
      "branch": "master",
      "remote": "origin",
      "path": "~/repositories/hooktest",
      "filters": [
        {
          "object_kind": "push",
          "ref": "refs/heads/master"
        }
      ]
    }
  ]
}
```

Execute script upon GitLab CI successful build of `master` branch.

```json
{
  "pidfilepath": "~/.gitautodeploy.pid",
  "host": "0.0.0.0",
  "port": 8080,
  "global_deploy": [
    "echo Pre-deploy script",
    "echo Post-deploy script"
  ],
  "repositories": [
    {
      "url": "http://gitlab/playground/hooktest.git",
      "deploy": "echo deploying project!",
      "filters": [
        {
          "object_kind": "build",
          "ref": "master",
          "build_status": "success"
        }
      ]
    }
  ]
}
```

# Repository configuration using environment variables

It's possible to configure up to one repository using environment variables. This can be useful in some specific use cases where a full config file is undesired.

Environment variable | Description
-------------------- | --------------------------
GAD_REPO_URL         | Repository URL
GAD_REPO_BRANCH      |
GAD_REPO_REMOTE      |
GAD_REPO_PATH        | Path to where ```Git-Auto-Deploy``` should clone and pull repository
GAD_REPO_DEPLOY      | Deploy command
