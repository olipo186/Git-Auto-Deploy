from setuptools import setup, find_packages

setup(name='git-auto-deploy',
      version='0.9',
      url='https://github.com/olipo186/Git-Auto-Deploy',
      author='Oliver Poignant',
      author_email='oliver@poignant.se',
      packages = find_packages(),
      package_data={'gitautodeploy': ['data/*', 'wwwroot/*']},
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
