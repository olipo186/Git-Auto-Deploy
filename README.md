# What is it?

GitAutoDeploy.py consists of a small HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository.</p>

![workflow](https://cloud.githubusercontent.com/assets/1056476/9344294/d3bc32a4-4607-11e5-9a44-5cd9b22e61d9.png)

# How does it work?

When commits are pushed to your Git repository, the Git server will notify ```GitAutoDeploy.py``` by sending a HTTP POST request with a JSON body to a pre configured URL (your-host:8001). The JSON body contains detailed information about the repository and what event that triggered the request. GitAutoDeploy.py parses and validates the request, and if all goes well it issues a ```git pull```.

Additionally, ```GitAutoDeploy.py``` can be configured to execute a shell command upon each successful ```git pull```, which can be used to trigger custom build actions or test scripts.</p>

# Getting started with command line utility
## Dependencies
* Git (tested on version 2.5.0)
* Python (tested on version 2.7)

## Configuration

* Copy ```GitAutoDeploy.conf.json.example``` to ```GitAutoDeploy.conf.json```
* Modify ```GitAutoDeploy.conf.json``` to match your project setup
* Make sure that the ```pidfilepath``` path is writable for the user running the script, as well as any other path configured for your repositories.

## Running the application
```python GitAutoDeploy.py```

## Command line options

--daemon-mode (-d) Run in background (daemon mode)
--quiet (-q) Suppress all output
--ssh-keygen
--force
--config <path> Specify custom configuration file

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

# Getting started with Docker image

## Run it directly with conf file
```
$ docker run -t --name autodeploy \
    -p 8001:8001 \
    -v $HOME/.ssh/id_rsa:/root/.ssh/id_rsa:ro \
    -v $HOME/Desktop/autodeploy/GitAutoDeploy.conf.json:/var/GitAutoDeploy.conf.json \
    -v $HOME/Desktop/autodeploy/repository:/var/repositories/myrepo \
    qnch/github-gitlab-auto-deploy
```

## or run it configured by environment variables

Configuration file is optional. If you include it, environment variables will override it.

```
$ docker run -t --name autodeploy \
    -p 8001:8001 \
    -v $HOME/.ssh/id_rsa:/root/.ssh/id_rsa:ro \
    -e AUTODEPLOY_URL=git@github.com:olipo186/Git-Auto-Deploy.git \
    -e AUTODEPLOY_BRANCH=master \
    -v $HOME/Desktop/autodeploy/repository:/var/repository \
    qnch/github-gitlab-auto-deploy
```

## All options

You can use this environment variables:

Variable name     | Desciption
----------------- | --------------------------------------------------------------------
AUTODEPLOY_URL    | SSH or HTTP[S] URL
AUTODEPLOY_BRANCH | GIT branch to follow (default: "master")
AUTODEPLOY_PATH   | Path to checkout working dir (default: "/var/repository")
AUTODEPLOY_PRE    | Command to call before deployment (default: "echo Deploy started!")
AUTODEPLOY_POST   | Command to call after deployment (default: "echo Deploy completed!")

If you want to deploy more than one repositories, you have to use your own config file. Then you don't have to set environment variables.

Possible volumes:

Volume path       | Description
----------------- | -------------------------------------------------------------------------------------------
/root/.ssh/id_rsa | Private key used to authenticate in repository (if not set, only HTTP connection will work)
/var/repository   | Working tree where will be deployed selected branch. Usually used for local development.


# Configure webhook

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
