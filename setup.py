from setuptools import setup, find_packages
import os
import sys

def package_files(package_path, directory_name):
    paths = []
    directory_path = os.path.join(package_path, directory_name)

    for (path, directories, filenames) in os.walk(directory_path):
        relative_path = os.path.relpath(path, package_path)
        for filename in filenames:
            if filename[0] == ".":
                continue
            paths.append(os.path.join(relative_path, filename))
    return paths

# Get path to project
package_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "gitautodeploy")

# Get list of data files
wwwroot_files = package_files(package_path, "wwwroot")
data_files = package_files(package_path, "data")

setup(name='git-auto-deploy',
      version='0.10',
      url='https://github.com/olipo186/Git-Auto-Deploy',
      author='Oliver Poignant',
      author_email='oliver@poignant.se',
      packages = find_packages(),
      package_data={'gitautodeploy': data_files + wwwroot_files},
      entry_points={
          'console_scripts': [
              'git-auto-deploy = gitautodeploy.__main__:main'
          ]
      },
      install_requires=[
            'lockfile'
      ],
      description = "Deploy your GitHub, GitLab or Bitbucket projects automatically on Git push events or webhooks.",
      long_description = "GitAutoDeploy consists of a HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository."
)
