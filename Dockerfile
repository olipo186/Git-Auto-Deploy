FROM google/python-runtime

RUN apt-get -y install openssh-client
RUN mkdir $HOME/.ssh && chmod 600 $HOME/.ssh
COPY deploy_rsa /root/.ssh/id_rsa

ENTRYPOINT ["/env/bin/python", "-u", "GitAutoDeploy.py", "--ssh-keyscan"]
