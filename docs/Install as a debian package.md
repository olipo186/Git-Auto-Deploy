# Install as a debian package (experimental)

Below is instructions on how to create a debian (.deb) package using stdeb. You can follow the instructions below to build the .deb package, or use the prepared script (platforms/debian/scripts/create-debian-package.sh) that will do the same. Once the package is created, you can install it using ```dpkg -i```. A sample configuration file as well as a init.d start up script will be installed as part of the package.

### Install dependencies

Install stdeb and other dependencies

    apt-get install python-stdeb fakeroot python-all

### Download and build

    git clone https://github.com/olipo186/Git-Auto-Deploy.git
    cd Git-Auto-Deploy
    
    # Generate a Debian source package
    python setup.py --command-packages=stdeb.command sdist_dsc -x platforms/debian/stdeb.cfg

    # Copy configuration files
    cp -vr ./platforms/debian/stdeb/* ./deb_dist/git-auto-deploy-<version>/debian/

    # Copile a Debian binary package
    cd ./deb_dist/git-auto-deploy-<version>
    dpkg-buildpackage -rfakeroot -uc -us

### Install

When installing the package, a sample configuration file and a init.d start up script will be created.

    dpkg -i git-auto-deploy-<version>.deb

### Configuration

    nano /etc/git-auto-deploy.conf.json

### Running the application

    service git-auto-deploy start
    service git-auto-deploy status
    
