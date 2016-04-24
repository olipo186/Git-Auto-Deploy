# Start automatically on boot

```Git-Auto-Deploy``` can be automatically started at boot time using various techniques. Below you'll find a couple of suggested approaches with instructions.

The following instructions assumes that you are running ```Git-Auto-Deploy``` from a clone of this repository. In such a case, ```Git-Auto-Deploy``` is started by invoking ```python``` and referencing the ```gitautodeploy``` python module which is found in the cloned repository. Such a command can look like ```python /path/to/Git-Auto-Deploy/gitautodeploy --daemon-mode```.

If you have used any of the alternative installation methods (install with pip or as a debian package), you will instead start ```Git-Auto-Deploy``` using a installed executable. ```Git-Auto-Deploy``` would then be started using a command like ```git-auto-deploy --daemon-mode``` instead. If you have installed ```Git-Auto-Deploy``` in this way, you will need to modify the paths and commands used in the instructions below.

## Crontab
The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the following:

    @reboot /usr/bin/python /path/to/Git-Auto-Deploy/gitautodeploy --daemon-mode --quiet

## Debian and Sys-V like init system.

Copy the sample init script into ```/etc/init.d/``` and make it executable.

    cp platforms/linux/initfiles/debianLSBInitScripts/git-auto-deploy /etc/init.d/
    chmod 755 /etc/init.d/git-auto-deploy

**Important:** The init script assumes that you have ```Git-Auto-Deploy``` installed in ```/opt/Git-Auto-Deploy/``` and that the ```pidfilepath``` config option is set to ```/var/run/git-auto-deploy.pid```. If this is not the case, edit the ```git-auto-deploy``` init script and modify ```DAEMON```, ```PWD``` and ```PIDFILE```.

**Important:** The init script will run GAD as the ```root``` user by default, which is convenient but not secure. The recommended way to run GAD is to set up a separate user and modify the init script to run GAD as that user. When running GAD as a user other than root, you will need to make sure that the correct permissions are set on all directories and files that GAD requires access to (such as the path specified in the variable PIDFILE and LOGFIE in the init script).

Now you need to add the correct symbolic link to your specific runlevel dir to get the script executed on each start up. On Debian_Sys-V just do;

    update-rc.d git-auto-deploy defaults

Fire it up and verify;

    service git-auto-deploy start
    service git-auto-deploy status

## Systemd

Copy the sample systemd service file ```git-auto-deploy.service``` into ```/etc/systemd/system```;

    cp platforms/linux/initfiles/systemd/git-auto-deploy.service /etc/systemd/system

Create the user and group specified in git-auto-deploy.service (```www-data```) if those do not exist already.

    useradd -U www-data

This init script assumes that you have ```Git-Auto-Deploy``` installed in ```/opt/Git-Auto-Deploy/```. If this is not the case, edit the ```git-auto-deploy.service``` service file and modify ```ExecStart``` and ```WorkingDirectory```.

Now, reload daemons and fire ut up;

    systemctl daemon-reload
    systemctl start git-auto-deploy

Make is start automatically on system boot;

    systemctl enable gitautodeploy
    

