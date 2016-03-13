# Start automatically on boot

```Git-Auto-Deploy``` can be automatically started at boot time using various techniques. Below you'll find a couple of suggested approaches with instructions.

## Crontab
The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the following:

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
