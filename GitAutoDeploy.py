import json, urlparse, sys, os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

class GitAutoDeploy(BaseHTTPRequestHandler):

    CONFIG_FILEPATH = './GitAutoDeploy.conf.json'
    config = None
    deamonMode = False

    @classmethod
    def getConfig(myClass):
        if(myClass.config == None):
            try:
                configString = open(myClass.CONFIG_FILEPATH).read()
            except:
                print 'Could not load ' + myClass.CONFIG_FILEPATH + ' file'
                sys.exit()

            try:
                myClass.config = json.loads(configString)
            except:
                print myClass.CONFIG_FILEPATH + ' file is not valid json'
                sys.exit()

            for repository in myClass.config['repositories']:
                if(not os.path.isdir(repository['path'])):
                    print 'Directory ' + repository['path'] + ' not found'
                    sys.exit()
                if(not os.path.isdir(repository['path'] + '/.git')):
                    print 'Directory ' + repository['path'] + ' is not a Git repository'
                    sys.exit()

        return myClass.config

    def do_POST(self):
        urls = self.parseRequest()
        for url in urls:
            path = self.getMatchingPath(url)
            self.pull(path)
            self.deploy(path)

    def parseRequest(self):
        length = int(self.headers.getheader('content-length'))
        body = self.rfile.read(length)
        post = urlparse.parse_qs(body)
        items = []
        for itemString in post['payload']:
            item = json.loads(itemString)
            items.append(item['repository']['url'])
        return items

    def getMatchingPath(self, repoUrl):
        config = self.getConfig()
        for repository in config['repositories']:
            if(repository['url'] == repoUrl):
                return repository['path']

    def respond(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def pull(self, path):
        print "\nPost push request received"
        print "Updating " + path
        call(['cd "' + path + '"; git pull'], shell=True)

    def deploy(self, path):
        config = self.getConfig()
        for repository in config['repositories']:
            if(repository['path'] == path):
                if 'deploy' in repository:
                     print "Executing deploy command"
                     call(['cd "' + path + '";' + repository['deploy']], shell=True)
                break

def main():
    try:
        print "Github Autodeploy Service v 0.1 started"
        server = HTTPServer(('', GitAutoDeploy.getConfig()['port']), GitAutoDeploy)
        server.serve_forever()
    except KeyboardInterrupt:
        print "Closing"
        server.socket.close()

if __name__ == '__main__':
     main()
