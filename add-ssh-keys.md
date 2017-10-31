# How to add your SSH keys to Git-Auto-Deploy

1. Copy your ssh keys from your account to /etc/git-auto-deploy/.ssh/

```cp -R ~/.ssh /etc/git-auto-deploy/```

2. Add gitlab, github or your hostname to the known_hosts file, eg.

```ssh-keyscan -t rsa gitlab.com >> /etc/git-auto-deploy/.ssh/known_hosts```

3. Add read and write permissions to /etc/git-auto-deploy

``` 
chown -R git-auto-deploy:git-auto-deploy /etc/git-auto-deploy
chmod -R 700 /etc/git-auto-deploy/.ssh/* 
```

4. Add write permissions to your repository path
```chown -R git-auto-deploy:git-auto-deploy /home/myrepo```

Make sure you use your ssh url in your config.
