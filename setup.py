from setuptools import setup, find_packages

setup(name='git-auto-deploy',
      version='0.2.0',
      url='https://github.com/olipo186/Git-Auto-Deploy',
      author='Oliver Poignant',
      author_email='oliver@poignant.se',
      packages = find_packages(),
      entry_points={
          'console_scripts': [
              'gad-server = gitautodeploy.__main__:main'
              'gad-generate-config = gitautodeploy.__main__:main'
          ]
      },
      description = "Deploy your GitHub, GitLab or Bitbucket projects automatically on Git push events or webhooks.",
      long_description = "GitAutoDeploy consists of a HTTP server that listens for Web hook requests sent from GitHub, GitLab or Bitbucket servers. This application allows you to continuously and automatically deploy you projects each time you push new commits to your repository."
)
