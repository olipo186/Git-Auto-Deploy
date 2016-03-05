# What is it?

GitAutoDeploy.py consists of a small HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository.</p>

![workflow](https://cloud.githubusercontent.com/assets/1056476/9344294/d3bc32a4-4607-11e5-9a44-5cd9b22e61d9.png)

# How does it work?

When commits are pushed to your Git repository, the Git server will notify ```GitAutoDeploy.py``` by sending a HTTP POST request with a JSON body to a pre configured URL (your-host:8001). The JSON body contains detailed information about the repository and what event that triggered the request. GitAutoDeploy.py parses and validates the request, and if all goes well it issues a ```git pull```.

Additionally, ```GitAutoDeploy.py``` can be configured to execute a shell command upon each successful ```git pull```, which can be used to trigger custom build actions or test scripts.</p>

# Getting started
## Dependencies
* Git (tested on version 2.5.0)
* Python (tested on version 2.7)

## Configuration

* Copy ```GitAutoDeploy.conf.json.example``` to ```GitAutoDeploy.conf.json```
* Modify ```GitAutoDeploy.conf.json``` to match your project setup
* Make sure that the ```pidfilepath``` path is writable for the user running the script, as well as any other path configured for your repositories.
* If you don't want to execute ```git pull``` after webhook was fired, you can leave field ```"path"``` empty.

### Logging

To start logging you can define ```"logfilepath": "/home/hermes/gitautodeploy.log"```. Note that you can`t see triggered command output when log is defined, only script output. If you leave ```"logfilepath"``` empty - everething will work as usual (without log).

## Running the application
```python GitAutoDeploy.py```

## Command line options

Command line option  | Environment variable | Description
-------------------- | --------------------------------------------------------------------
--daemon-mode (-d)   | GAD_DAEMON_MODE      | |Run in background (daemon mode)
--quiet (-q)         | GAD_QUIET            | Supress console output
--ssh-keygen         | GAD_SSH_KEYGEN       | Scan repository hosts for ssh keys
--force              | GAD_FORCE            | Attempt to kill any process that is occupying the configured port
--config (-c) <path> | GAD_CONFIG           | Custom configuration file path

## Start automatically on boot

### Crontab
The easiest way to configure your system to automatically start ```GitAutoDeploy.py``` after a reboot is through crontab. Open crontab in edit mode using ```crontab -e``` and add the following:

```@reboot /usr/bin/python /path/to/GitAutoDeploy.py --daemon-mode --quiet```

### Debian and Sys-V like init system.

* Copy file ```initfiles/debianLSBInitScripts/gitautodeploy``` to ```/etc/init.d/```
* Make it executable: ```chmod 755 /etc/init.d/gitautodeploy```
* Also you need to make ```GitAutoDeploy.py``` executable (if it isn't already): ```chmod 755 GitAutoDeploy.py```
* This init script assumes that you have ```GitAutoDeploy.py``` installed in ```/opt/Git-Auto-Deploy/``` and that the ```pidfilepath``` config option is set to ```/var/run/gitautodeploy.pid```. If this is not the case, edit the ```gitautodeploy``` init script and modify ```DAEMON```, ```PWD``` and ```PIDFILE```.
* Now you need to add the correct symbolic link to your specific runlevel dir to get the script executed on each start up. On Debian_Sys-V just do ```update-rc.d gitautodeploy defaults```

### Systemd

* Copy file ```initfiles/systemd/gitautodeploy.service``` to ```/etc/systemd/system```
* Also you need to make ```GitAutoDeploy.py``` executable (if it isn't already): ```chmod 755 GitAutoDeploy.py```
* And also you need to create the user and the group ```www-data``` if those not exists ```useradd -U www-data```
* This init script assumes that you have ```GitAutoDeploy.py``` installed in ```/opt/Git-Auto-Deploy/```. If this is not the case, edit the ```gitautodeploy.service``` service file and modify ```ExecStart``` and ```WorkingDirectory```.
* now reload daemons ```systemctl daemon-reload```
* Fire it up ```systemctl start gitautodeploy```
* Make is start on system boot ```systemctl enable gitautodeploy```

## Configure GitHub

* Go to your repository -> Settings -> Webhooks and Services -> Add webhook</li>
* In "Payload URL", enter your hostname and port (your-host:8001)
* Hit "Add webhook"

## Configure GitLab
* Go to your repository -> Settings -> Web hooks
* In "URL", enter your hostname and port (your-host:8001)
* Hit "Add Web Hook"

## Configure Bitbucket
* Go to your repository -> Settings -> Webhooks -> Add webhook
* In "URL", enter your hostname and port (your-host:8001)
* Hit "Save"

# Example workflows

## Continuous Delivery via Pull requests (GitHub only)

It's possible to configure Git-Auto-Deploy to trigger when pull requests are opened or closed on GitHub. To read more about this workflow and how to configure Git-Aut-Deploy here: [Continuous Delivery via Pull requests](./docs/Continuous Delivery via Pull requests.md)
