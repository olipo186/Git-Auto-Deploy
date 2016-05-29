#!/usr/bin/env bash
# 
# DEPRECATED: Use make instead
# 
# This script compiles a binary Debian package (.deb)
# 

echo "DEPRECATED: Use make instead"
exit

# Get current path
ORIGINAL_CWD=`pwd -P`

# Get script path (<path>/Git-Auto-Deploy/platforms/debian/scripts)
pushd `dirname $0` > /dev/null
SCRIPT_PATH=`pwd -P`
popd > /dev/null

# Path to Git-Auto-Deploy project directory
PROJECT_PATH=`readlink -f $SCRIPT_PATH/../../../`
cd $PROJECT_PATH

# Get package name and version
PACKAGE_NAME=`python setup.py --name`
PACKAGE_VERSION=`python setup.py --version`

# Generate a Debian source package
echo
echo "** Generating a Debian source package **"
python setup.py --command-packages=stdeb.command sdist_dsc -x platforms/debian/stdeb.cfg

# Path to newly generated deb_dist directory
TARGET=`readlink -f "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION"`

# Copy configuration files
echo
echo "** Copying configuration files **"
cp -vr "$PROJECT_PATH/platforms/debian/stdeb"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/"
#cp -vrp "$PROJECT_PATH/platforms/debian/etc"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/"
#cp -vrp "$PROJECT_PATH/platforms/debian/etc"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/source"
#mkdir "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/gitautodeploy"
#mkdir "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/git-auto-deploy"
#mkdir "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/tmp"
#cp -vrp "$PROJECT_PATH/platforms/debian/etc"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/gitautodeploy"
#cp -vrp "$PROJECT_PATH/platforms/debian/etc"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/debian/tmp"
#cp -vrp "$PROJECT_PATH/platforms/debian/etc"/* "$PROJECT_PATH/deb_dist/$PACKAGE_NAME-$PACKAGE_VERSION/gitautodeploy"

# Copile a Debian binary package
echo
echo "** Compiling a Debian binary package **"
cd "$PROJECT_PATH/deb_dist/"*

#dpkg-source --commit

dpkg-buildpackage -rfakeroot -uc -us

# Restore cwd
cd $ORIGINAL_CWD