# What is it?

Git-Auto-Deploy consists of a small HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository.</p>

![workflow](https://cloud.githubusercontent.com/assets/1056476/9344294/d3bc32a4-4607-11e5-9a44-5cd9b22e61d9.png)

# How does it work?

When commits are pushed to your Git repository, the Git server will notify ```Git-Auto-Deploy``` by sending a HTTP POST request with a JSON body to a pre configured URL (your-host:8001). The JSON body contains detailed information about the repository and what event that triggered the request. ```Git-Auto-Deploy``` parses and validates the request, and if all goes well it issues a ```git pull```.

Additionally, ```Git-Auto-Deploy``` can be configured to execute a shell command upon each successful ```git pull```, which can be used to trigger custom build actions or test scripts.</p>

# Getting started

  * [Getting started](#getting-started)
    * [Dependencies](#dependencies)
    * [Install from repository (recommended)](#install-from-repository-recommended)
      * [Download and install](#download-and-install)
      * [Configuration](#configuration)
      * [Running the application](#running-the-application)
      * [Start automatically on boot using crontab](#start-automatically-on-boot)
    * [Alternative installation methods](#alternative-installation-methods)
    * [Command line options](#command-line-options)
    * [Configuring external services](#configuring-external-services)
      * [GitHub](#github)
      * [GitLab](#gitlab)
      * [BitBucket](#bitbucket)

## Dependencies
* Git (tested on version 2.5.0)
* Python (tested on version 2.7)

## Install from repository (recommended)

### Download and install

    git clone https://github.com/olipo186/Git-Auto-Deploy.git
    cd Git-Auto-Deploy

### Configuration

Make a copy of the sample configuration file and modify it to match your project setup. [Read more about the configuration options](./docs/Configuration.md).

    cp config.json.sample config.json

*Tip:* Make sure that the path specified in ```pidfilepath``` is writable for the user running the script, as well as any other path configured for your repositories.

### Running the application

Run the application my invoking ```python``` and referencing the ```gitautodeploy``` module (the directory ```Git-Auto-Deploy/gitautodeploy```).

    python gitautodeploy

### Start automatically on boot

The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the entry below.

    @reboot /usr/bin/python /path/to/Git-Auto-Deploy/gitautodeploy --daemon-mode --quiet --config /path/to/git-auto-deploy.conf.json

*Tip:* You can also configure ```Git-Auto-Deploy``` to start automatically using a init.d-script (for Debian and Sys-V like init systems) or a service for systemd. [Read more about other starting automatically using init.d or systemd](./docs/Start automatically on boot.md)

## Alternative installation methods

* [Install as a python module (experimental)](./docs/Install as a python module.md)
* [Install as a debian package (experimental)](./docs/Install as a debian package.md)

## Command line options

Below is a summarized list of the most common command line options. For a full list of available command line options, invoke the application with the argument ```--help``` or read the documentation article about [all avaialble command line options, environment variables and config attributes](./docs/Configuration.md).

Command line option    | Environment variable | Config attribute | Description
---------------------- | -------------------- | ---------------- | --------------------------
--daemon-mode (-d)     | GAD_DAEMON_MODE      |                  | Run in background (daemon mode)
--quiet (-q)           | GAD_QUIET            |                  | Supress console output
--config (-c) <path>   | GAD_CONFIG           |                  | Custom configuration file
--pid-file <path>      | GAD_PID_FILE         | pidfilepath      | Specify a custom pid file
--log-file <path>      | GAD_LOG_FILE         | logfilepath      | Specify a log file
--host <host>          | GAD_HOST             | host             | Address to bind to
--port <port>          | GAD_PORT             | port             | Port to bind to

## Configuring external services
To make your git provider send notifications to ```Git-Auto-Deploy``` you will need to provide the hostname and port for your ```Git-Auto-Deploy``` instance. Instructions for the most common git providers is listed below.

### GitHub
* Go to your repository -> Settings -> Webhooks and Services -> Add webhook</li>
* In "Payload URL", enter your hostname and port (your-host:8001)
* Hit "Add webhook"

### GitLab
* Go to your repository -> Settings -> Web hooks
* In "URL", enter your hostname and port (your-host:8001)
* Hit "Add Web Hook"

### Bitbucket
* Go to your repository -> Settings -> Webhooks -> Add webhook
* In "URL", enter your hostname and port (your-host:8001)
* Hit "Save"


# Example workflows

## Continuous Delivery via Pull requests (GitHub only)

It's possible to configure Git-Auto-Deploy to trigger when pull requests are opened or closed on GitHub. To read more about this workflow and how to configure Git-Aut-Deploy here: [Continuous Delivery via Pull requests](./docs/Continuous Delivery via Pull requests.md)
