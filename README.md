![How it works](http://olipo186.github.com/Github-Gitlab-Auto-Deploy/images/Github-Gitlab-Auto-Deploy.png)

h1. What is it?

this is a small HTTP server written in python.
It allows you to have a version of your project installed, that will be updated automatically on each Github or Gitlab push.

To set it up, do the following:
* install python
* copy the ```GitAutoDeploy.conf.json.example``` to ```GitAutoDeploy.conf.json```. This file will be gitignored and can be environment specific.
* enter the matching for your project(s) in the ```GitAutoDeploy.conf.json``` file
* start the server by typing ```python GitAutoDeploy.py```
* to run it as a daemon add ```--daemon-mode```
* On the Github or Gitlab page go to a repository, then "Admin", "Service Hooks",
"Post-Receive URLs" and add the url of your machine + port (e.g. ```http://example.com:8001```).

You can even test the whole thing here, by clicking on the "Test Hook" button, whohoo!

h2. Configure GitAutoDeploy to get executed at start up

h3. Debian and Sys-V like init system.
* Copy file ```initfiles/debianLSBInitScripts/gitautodeploy``` to ```/etc/init.d/```
* Make it executable: ```chmod 755 /etc/init.d/gitautodeploy```
* Also you need to make ```GitAutoDeploy.py``` executable (if it isn't already): ```chmod 755 GitAutoDeploy.py```
* This init script assumes that you have ```GitAutoDeploy.py``` in ```/opt/Gitlab_Auto_Deploy/GitAutoDeploy.py```. If this is not the case, edit ```gitautodeploy``` init script and modify ```DAEMON``` and ```PWD```.
* Now you need to add the correct symbolic link to your specific runlevel dir to get the script executed on each start up. On Debian_Sys-V just do ```update.rc.d gitautodeploy defaults```

h1. How this works

When someone pushes changes into Github or Gitlab, it sends a json file to the service hook url.
It contains information about the repository that was updated.

All it really does is match the repository urls to your local repository paths in the config file,
move there and run "git pull".


Additionally it runs a deploy bash command that you can add to the config file optionally, and it also
allows you to add two global deploy commands, one that would run at the beginning and one that would run at the end of the deploy.
Make sure that you start the server as the user that is allowed to pull from the github or gitlab repository.
