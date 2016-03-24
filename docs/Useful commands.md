
# Create debian package
apt-get install python-stdeb fakeroot python-all

https://pypi.python.org/pypi/stdeb/0.8.5
python setup.py --command-packages=stdeb.command –package=git-auto-deploy bdist_deb
python setup.py --command-packages=stdeb.command sdist_dsc bdist_deb


# Debianize
python setup.py --command-packages=stdeb.command debianize

# deb source
add-apt-repository ppa:olipo186/git-auto-deploy
