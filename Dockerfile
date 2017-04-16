FROM r.fds.so:5000/python2.7

RUN apt-get update && \
    apt-get -y install openssh-client

RUN mkdir $HOME/.ssh && chmod 600 $HOME/.ssh
COPY deploy_rsa /root/.ssh/id_rsa

ENTRYPOINT ["/usr/bin/python", "-u", "GitAutoDeploy.py", "--ssh-keyscan"]
