
# Create debian package
https://pypi.python.org/pypi/stdeb/0.8.5
python setup.py --command-packages=stdeb.command bdist_deb

# Debianize
python setup.py --command-packages=stdeb.command debianize
