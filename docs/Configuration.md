# Command line options and environment variables

```Git-Auto-Deploy``` supports a number of configurable options. Some of them are available using command line options, where others are only configurable from the config file. Below is a list of the options made available from the command line. Every command line option has also a corresponding environemnt variable. In the cases where a corresponding config file attribute is available, that attribute name is listed.

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
--force                | GAD_FORCE            |                  | Kill any process using the configured port
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
 - **branch**: The branch which will be checked out.
 - **remote**: The name of the remote to use.
 - **path**: Path to clone the repository to. If omitted, the repository won't
   be cloned, only the deploy scripts will be executed.
 - **deploy**: A command to be executed. If `path` is set, the command is 
   executed after a successfull `pull`.
 - **filters**: Filters to apply to the web hook events so that only the desired
   events result in executing the deploy actions. See section *Filters* for more
   details.
 - **secret-token**: The secret token set for your webhook (currently only implemented for [GitHub](https://developer.github.com/webhooks/securing/) and GitLab)

## Filters
*(Currently only supported for GitHub and GitLab)*

With filter, it is possible to trigger the deploy only if the criteria are met.
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

# Examples

## GitHub

The following example will trigger when a pull request with **master** as base is closed.
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

## GitLab
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
