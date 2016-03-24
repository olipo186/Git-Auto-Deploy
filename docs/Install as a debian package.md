# Install as debian package from PPA (experimental)

Add our PPA

    add-apt-repository ppa:olipo186/git-auto-deploy
    apt-get update

Install the package

    apt-get install git-auto-deploy

Make your changes to the configuration file

    nano /etc/git-auto-deploy.conf.json

Run the application

    service git-auto-deploy start
    service git-auto-deploy status
    
# Install from .deb file (experimental)

Below is instructions on how to create a debian (.deb) package using stdeb. You can follow the instructions below to build the .deb package, or use the prepared script (platforms/debian/scripts/create-debian-package.sh) that will do the same. Once the package is created, you can install it using ```dpkg -i```. A sample configuration file as well as a init.d start up script will be installed as part of the package.

### Install dependencies

Install stdeb and other dependencies

    apt-get install python-stdeb fakeroot python-all

### Download and build

    git clone https://github.com/olipo186/Git-Auto-Deploy.git
    cd Git-Auto-Deploy
    make deb

### Install

When installing the package, a sample configuration file and a init.d start up script will be created.

    dpkg -i dist/deb/git-auto-deploy-<version>.deb

### Configuration

    nano /etc/git-auto-deploy.conf.json

### Running the application

    service git-auto-deploy start
    service git-auto-deploy status
    
