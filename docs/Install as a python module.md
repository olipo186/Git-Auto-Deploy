# Install as a python module (experimental)

## Download and install

Install using [pip](http://www.pip-installer.org/en/latest/), a package manager for Python, by running the following command.

    pip install git-auto-deploy

If you don't have pip installed, try installing it by running this from the command
line:

    curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

Or, you can [download the source code
(ZIP)](https://github.com/olipo186/Git-Auto-Deploy/zipball/master "Git-Auto-Deploy
source code") for `Git-Auto-Deploy` and then run:

    python setup.py install

You may need to run the above commands with `sudo`.

Once ```Git-Auto-Deploy``` has been installed as a python module, it can be started using the executable ```git-auto-deploy```. During installation with pip, the executable is usually installed in ```/usr/local/bin/git-auto-deploy```. This can vary depending on platform.

## Configuration

Copy the content of [config.json.sample](../config.json.sample) and save it anywhere you like, for example ```~/git-auto-deploy.conf.json```. Modify it to match your project setup. [Read more about the configuration options](../docs/Configuration.md).

## Running the application

Run the application using the executable ```git-auto-deploy``` which has been provided by pip. Provide the path to your configuration file as a command line argument.

    git-auto-deploy --config ~/git-auto-deploy.conf.json

## Start automatically on boot using crontab

The easiest way to configure your system to automatically start ```Git-Auto-Deploy``` after a reboot is using crontab. Open crontab in edit mode using ```crontab -e``` and add the entry below.

When installing with pip, the executable ```git-auto-deploy``` is usually installed in ```/usr/local/bin/git-auto-deploy```. It is a good idea to verify the path to ```git-auto-deploy``` before adding the entry below.

    @reboot /usr/local/bin/git-auto-deploy --daemon-mode --quiet --config /path/to/git-auto-deploy.conf.json

