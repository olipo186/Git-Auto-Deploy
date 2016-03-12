# Configuration
The configuration file is formatted in `JSON`. The possible root elements are 
as follow:

 - **pidfilepath**: The path where `pid` files are kept.
 - **logfilepath**: To enable logging, set this to a valid file path.
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