# What is it?

Git-Auto-Deploy consists of a small HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository.</p>

![workflow](https://cloud.githubusercontent.com/assets/1056476/9344294/d3bc32a4-4607-11e5-9a44-5cd9b22e61d9.png)

# How does it work?

When commits are pushed to your Git repository, the Git server will notify ```Git-Auto-Deploy``` by sending a HTTP POST request with a JSON body to a pre configured URL (your-host:8001). The JSON body contains detailed information about the repository and what event that triggered the request. ```Git-Auto-Deploy``` parses and validates the request, and if all goes well it issues a ```git pull```.

Additionally, ```Git-Auto-Deploy``` can be configured to execute a shell command upon each successful ```git pull```, which can be used to trigger custom build actions or test scripts.</p>

Table of contents
=================

  * [What is it?](#what-is-it)
  * [How does it work?](#how-does-it-work)
  * [Table of contents](#table-of-contents)
  * [Getting started](#getting-started)
    * [Dependencies](#dependencies)
    * [Install from repository (recommended)](#install-from-repository-recommended)
      * [Download and install](#download-and-install)
      * [Configuration](#configuration)
      * [Running the application](#running-the-application)
      * [Starting automatically on boot using crontab](#starting-automatically-on-boot-using-crontab)
    * [Command line options](#command-line-options)
    * [Configuring external services](#configuring-external-services)
      * [GitHub](#github)
      * [GitLab](#gitlab)
      * [BitBucket](#bitbucket)
  * [Alternative installation methods](#alternative-installation-methods)
    * [Install as a python module (experimental)](#install-as-a-python-module-experimental)
    * [Install as a debian package (experimental)](#install-as-a-debian-package-experimental)

# Getting started

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

Tip: Make sure that the path specified in ```pidfilepath``` is writable for the user running the script, as well as any other path configured for your repositories.

### Running the application

Run the application my invoking ```python``` and referencing the ```gitautodeploy``` module (the directory ```Git-Auto-Deploy/gitautodeploy```).

    python gitautodeploy

### Start automatically on boot using crontab

The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the entry below.

    @reboot /usr/bin/python /path/to/Git-Auto-Deploy/gitautodeploy --daemon-mode --quiet --config /path/to/git-auto-deploy.conf.json

## Command line options

Command line option    | Environment variable | Config attribute | Description
---------------------- | -------------------- | ---------------- | --------------------------
--daemon-mode (-d)     | GAD_DAEMON_MODE      |                  | Run in background (daemon mode)
--quiet (-q)           | GAD_QUIET            |                  | Supress console output
--ssh-keygen           | GAD_SSH_KEYGEN       |                  | Scan repository hosts for ssh keys
--force                | GAD_FORCE            |                  | Kill any process using the configured port
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

# Alternative installation methods

## Install as a python module (experimental)

### Download and install

Install using [pip](http://www.pip-installer.org/en/latest/), a package manager for Python, by running the following command.

    pip install pip install --upgrade https://github.com/olipo186/Git-Auto-Deploy/archive/master.tar.gz

If you don't have pip installed, try installing it by running this from the command
line:

    curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

Or, you can [download the source code
(ZIP)](https://github.com/olipo186/Git-Auto-Deploy/zipball/master "Git-Auto-Deploy
source code") for `Git-Auto-Deploy` and then run:

    python setup.py install

You may need to run the above commands with `sudo`.

Once ```Git-Auto-Deploy``` has been installed as a python module, it can be started using the executable ```git-auto-deploy```. During installation with pip, the executable is usually installed in ```/usr/local/bin/git-auto-deploy```. This can vary depending on platform.

### Configuration

Copy the content of [config.json.sample](./config.json.sample) and save it anywhere you like, for example ```~/git-auto-deploy.conf.json```. Modify it to match your project setup. [Read more about the configuration options](./docs/Configuration.md).
 [](./docs/Configuration.md)

### Running the application

Run the application using the executable ```git-auto-deploy``` which has been provided by pip. Provide the path to your configuration file as a command line argument.
 referencing the ```gitautodeploy``` module (the directory ```Git-Auto-Deploy/gitautodeploy```).

    git-auto-deploy --config ~/git-auto-deploy.conf.json

### Start automatically on boot

#### Using crontab

The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the entry below.

When installing with pip, the executable ```git-auto-deploy``` is usually installed in ```/usr/local/bin/git-auto-deploy```. It is a good idea to verify the path to ```git-auto-deploy``` before adding the entry below.

    @reboot /usr/local/bin/git-auto-deploy --daemon-mode --quiet --config /path/to/git-auto-deploy.conf.json

## Installation as a debian package (experimental)

### Download and install

### Configuration

### Running the application

# Start automatically on boot

## Crontab
The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is through crontab. Open crontab in edit mode using ```crontab -e``` and add the following:

```@reboot /usr/bin/python /path/to/gitautodeploy --daemon-mode --quiet```

## Debian and Sys-V like init system.

* Copy file ```initfiles/debianLSBInitScripts/gitautodeploy``` to ```/etc/init.d/```
* Make it executable: ```chmod 755 /etc/init.d/gitautodeploy```
* Also you need to make ```GitAutoDeploy.py``` executable (if it isn't already): ```chmod 755 GitAutoDeploy.py```
* This init script assumes that you have ```GitAutoDeploy.py``` installed in ```/opt/Git-Auto-Deploy/``` and that the ```pidfilepath``` config option is set to ```/var/run/gitautodeploy.pid```. If this is not the case, edit the ```gitautodeploy``` init script and modify ```DAEMON```, ```PWD``` and ```PIDFILE```.
* Now you need to add the correct symbolic link to your specific runlevel dir to get the script executed on each start up. On Debian_Sys-V just do ```update-rc.d gitautodeploy defaults```

## Systemd

* Copy file ```initfiles/systemd/gitautodeploy.service``` to ```/etc/systemd/system```
* Also you need to make ```GitAutoDeploy.py``` executable (if it isn't already): ```chmod 755 GitAutoDeploy.py```
* And also you need to create the user and the group ```www-data``` if those not exists ```useradd -U www-data```
* This init script assumes that you have ```GitAutoDeploy.py``` installed in ```/opt/Git-Auto-Deploy/```. If this is not the case, edit the ```gitautodeploy.service``` service file and modify ```ExecStart``` and ```WorkingDirectory```.
* now reload daemons ```systemctl daemon-reload```
* Fire it up ```systemctl start gitautodeploy```
* Make is start on system boot ```systemctl enable gitautodeploy```

# Example workflows

## Continuous Delivery via Pull requests (GitHub only)

It's possible to configure Git-Auto-Deploy to trigger when pull requests are opened or closed on GitHub. To read more about this workflow and how to configure Git-Aut-Deploy here: [Continuous Delivery via Pull requests](./docs/Continuous Delivery via Pull requests.md)
