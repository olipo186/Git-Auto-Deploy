#!/usr/bin/env python

import json, urlparse, sys, os, signal, socket, re
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call
from threading import Timer


class GitAutoDeploy(BaseHTTPRequestHandler):

    CONFIG_FILE_PATH = './GitAutoDeploy.conf.json'
    config = None
    debug = True
    quiet = False
    daemon = False

    @classmethod
    def get_config(cls):

        if not cls.config:

            try:
                config_string = open(cls.CONFIG_FILE_PATH).read()

            except:
                print "Could not load %s file" % cls.CONFIG_FILE_PATH
                sys.exit(2)

            try:
                cls.config = json.loads(config_string)

            except:
                print "%s file is not valid JSON" % cls.CONFIG_FILE_PATH
                sys.exit(2)

            for repository in cls.config['repositories']:

                if not os.path.isdir(repository['path']):

                    print "Directory %s not found" % repository['path']
                    call(['git clone --recursive '+repository['url']+' '+repository['path']], shell=True)

                    if not os.path.isdir(repository['path']):
                        print "Unable to clone repository %s" % repository['url']
                        sys.exit(2)

                    else:
                        print "Repository %s successfully cloned" % repository['url']

                if not os.path.isdir(repository['path'] + '/.git'):
                    print "Directory %s is not a Git repository" % repository['path']
                    sys.exit(2)

                cls.clear_lock(repository['path'])

        return cls.config

    def do_POST(self):
        urls = self.parse_request()
        self.respond()
        Timer(1.0, self.do_process, [urls]).start()

    def do_process(self, urls):
        
        for url in urls:
            
            repos = self.getMatchingPaths(url)
            for repo in repos:
                
                if self.lock(repo['path']):
                    
                    try:
                        n = 4
                        while 0 < n and 0 != self.pull(repo['path'], repo['branch']):
                            --n
                        if 0 < n:
                            self.deploy(repo['path'])
                        
                    except:
                        call(['echo "Error during \'pull\' or \'deploy\' operation on path: ' + repo['path'] + '"'],
                             shell=True)
                        
                    finally:
                        self.unlock(repo['path'])
    
    def parse_request(self):
        content_type = self.headers.getheader('content-type')
        length = int(self.headers.getheader('content-length'))
        body = self.rfile.read(length)

        items = []
        
        try:
            if content_type == "application/json" or content_type == "application/x-www-form-urlencoded":
                post = urlparse.parse_qs(body)

            # If payload is missing, we assume GitLab syntax.
            if content_type == "application/json" and "payload" not in post:
                mode = "github"

            # If x-www-form-urlencoded, we assume BitBucket syntax.
            elif content_type == "application/x-www-form-urlencoded":
                mode = "bitbucket"

            # Oh GitLab, dear GitLab...
            else:
                mode = "gitlab"

            
            if mode == "github":
                response = json.loads(body)
                items.append(response['repository']['url'])
                
            elif mode == "bitbucket":
                for itemString in post['payload']:
                    item = json.loads(itemString)
                    items.append("ssh://hg@bitbucket.org" + item['repository']['absolute_url'][0:-1])

            # Otherwise, we assume GitHub/BitBucket syntax.
            elif mode == "gitlab":
                for itemString in post['payload']:
                    item = json.loads(itemString)
                    items.append(item['repository']['url'])
            
            # WTF?!
            else:
                pass

        except:
            pass

        return items

    def getMatchingPaths(self, repoUrl):
        res = []
        config = self.get_config()
        for repository in config['repositories']:
            if repository['url'] == repoUrl:
                res.append({
                    'path': repository['path'],
                    'branch': ('branch' in repository) and repository['branch'] or 'master'
                })
        return res

    def respond(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def lock(self, path):
        return 0 == call(['sh lock.sh "' + path + '"'], shell=True)

    def unlock(self, path):
        call(['sh unlock.sh "' + path + '"'], shell=True)

    @classmethod
    def clear_lock(cls, path):
        call(['sh clear_lock.sh "' + path + '"'], shell=True)

    def pull(self, path, branch):
        if not self.quiet:
            print "\nPost push request received"
            print 'Updating ' + path
        res = call(['sleep 5; cd "' + path + '" && unset GIT_DIR && git fetch origin && git update-index --refresh && git reset --hard origin/' + branch + ' && git submodule init && git submodule update'], shell=True)
        call(['echo "Pull result: ' + str(res) + '"'], shell=True)
        return res

    def deploy(self, path):
        config = self.get_config()
        for repository in config['repositories']:
            if repository['path'] == path:
                cmds = []
                if 'deploy' in repository:
                    cmds.append(repository['deploy'])

                gd = config['global_deploy']
                if len(gd[0]) is not 0:
                    cmds.insert(0, gd[0])
                if len(gd[1]) is not 0:
                    cmds.append(gd[1])

                if(not self.quiet):
                    print 'Executing deploy command(s)'
                for cmd in cmds:
                    call(['cd "' + path + '" && ' + cmd], shell=True)

                break


class GitAutoDeployMain:

    server = None

    def run(self):
        for arg in sys.argv:

            if arg == '-d' or arg == '--daemon-mode':
                GitAutoDeploy.daemon = True
                GitAutoDeploy.quiet = True

            if arg == '-q' or arg == '--quiet':
                GitAutoDeploy.quiet = True

            if arg == '--ssh-keyscan':
                print 'Scanning repository hosts for ssh keys...'
                self.ssh_key_scan()

            if arg == '--force':
                print '[KILLER MODE] Warning: The --force option will try to kill any process ' \
                    'using %s port. USE AT YOUR OWN RISK' % GitAutoDeploy.get_config()['port']
                self.kill_them_all()

        if GitAutoDeploy.daemon:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
            os.setsid()

        self.create_pidfile()

        if not GitAutoDeploy.quiet:
            print 'GitHub & GitLab auto deploy service v 0.1 started'
        else:
            print 'GitHub & GitLab auto deploy service v 0.1 started in daemon mode'

        try:
            self.server = HTTPServer((GitAutoDeploy.get_config()['host'], GitAutoDeploy.get_config()['port']), GitAutoDeploy)
            sa = self.server.socket.getsockname()
            print "Listeing on", sa[0], "port", sa[1]
            self.server.serve_forever()

        except socket.error, e:

            if not GitAutoDeploy.quiet and not GitAutoDeploy.daemon:
                print "Error on socket: %s" % e
                self.debug_diagnosis()
            sys.exit(1)

    def ssh_key_scan(self):

        for repository in GitAutoDeploy.get_config()['repositories']:

            url = repository['url']
            print "Scanning repository: %s" %  url
            m = re.match('.*@(.*?):', url)

            if m:
                port = repository['port']
                port = '' if not port else ('-p' + port)
                call(['ssh-keyscan -t ecdsa,rsa ' + port + ' ' + m.group(1) + ' >> $HOME/.ssh/known_hosts'], shell=True)

            else:
                print 'Could not find regexp match in path: %s' % url

    def kill_them_all(self):

        pid = self.get_pid_on_port(GitAutoDeploy.get_config()['port'])

        if not pid:
            print '[KILLER MODE] I don\'t know the number of pid that is using my configured port\n ' \
                '[KILLER MODE] Maybe no one? Please, use --force option carefully'
            return False

        os.kill(pid, signal.SIGKILL)
        return True
 
    def create_pidfile(self):
        import sys
        from os import path, makedirs

        pid_file_path = GitAutoDeploy.get_config()['pidfilepath']
        pid_file_dir = path.dirname(pid_file_path)

        # Create necessary directory structure if needed
        if not path.exists(pid_file_dir):

            try:
                makedirs(pid_file_dir)

            except OSError as e:
                print "Unable to create PID file: %s" % e
                sys.exit(2)


        with open(pid_file_path, 'w') as f:
            f.write(str(os.getpid()))

    def read_pidfile(self):
        with open(GitAutoDeploy.get_config()['pidfilepath'],'r') as f:
            return f.readlines()

    def remove_pidfile(self):
        os.remove(GitAutoDeploy.get_config()['pidfilepath'])

    def debug_diagnosis(self):
        if not GitAutoDeploy.debug:
            return

        port = GitAutoDeploy.get_config()['port']
        pid = self.get_pid_on_port(port)

        if not pid:
            print 'I don\'t know the number of pid that is using my configured port'
            return
        
        print 'Process with pid number %s is using port %s' % (pid, port)
        with open("/proc/%s/cmdline" % pid) as f:
            cmdline = f.readlines()
            print 'cmdline ->', cmdline[0].replace('\x00', ' ')

    def get_pid_on_port(self, port):

        with open("/proc/net/tcp",'r') as f:
            file_content = f.readlines()[1:]

        pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
        conf_port = str(GitAutoDeploy.get_config()['port'])
        mpid = False

        for line in file_content:

            if mpid:
                break

            _, laddr, _, _, _, _, _, _, _, inode = line.split()[:10]
            decport = str(int(laddr.split(':')[1], 16))

            if decport != conf_port:
                continue

            for pid in pids:

                try:
                    path = "/proc/%s/fd" % pid
                    if os.access(path, os.R_OK) is False:
                        continue

                    for fd in os.listdir(path):
                        cinode = os.readlink("/proc/%s/fd/%s" % (pid, fd))
                        minode = cinode.split(":")

                        if len(minode) == 2 and minode[1][1:-1] == inode:
                            mpid = pid

                except Exception as e:
                    pass

        return mpid

    def stop(self):
        if self.server is not None:
            self.server.socket.close()

    def exit(self):

        if not GitAutoDeploy.quiet:
            print '\nGoodbye'

        self.remove_pidfile()
        sys.exit(0)

    def signal_handler(self, signum, frame):
        self.stop()

        if signum == 1:
            self.run()
            return

        elif signum == 2:
            print '\nKeyboard Interrupt!!!'

        elif signum == 6:
            print 'Requested close by SIGABRT (process abort signal). Code 6.'

        self.exit()

if __name__ == '__main__':
    gadm = GitAutoDeployMain()

    signal.signal(signal.SIGHUP, gadm.signal_handler)
    signal.signal(signal.SIGINT, gadm.signal_handler)
    signal.signal(signal.SIGABRT, gadm.signal_handler)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    gadm.run()
