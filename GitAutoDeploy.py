#!/usr/bin/env python

import json, urlparse, sys, os, signal, socket, re
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call
from threading import Timer

class GitAutoDeploy(BaseHTTPRequestHandler):

	CONFIG_FILEPATH = './GitAutoDeploy.conf.json'
	config = None
	debug = True
	quiet = False
	daemon = False

	@classmethod
	def getConfig(myClass):
		if(myClass.config == None):
			try:
				configString = open(myClass.CONFIG_FILEPATH).read()
			except:
				print "Could not load %s file" % myClass.CONFIG_FILEPATH
				sys.exit(2)

			try:
				myClass.config = json.loads(configString)
			except:
				print "%s file is not valid JSON" % myClass.CONFIG_FILEPATH
				sys.exit(2)

			for repository in myClass.config['repositories']:
				if(not os.path.isdir(repository['path'])):
					print "Directory %s not found" % repository['path']
					call(['git clone '+repository['url']+' '+repository['path']], shell=True)
					if(not os.path.isdir(repository['path'])):
						print "Unable to clone repository %s" % repository['url']
						sys.exit(2)
					else:
						print "Repository %s successfully cloned" % repository['url']
				if(not os.path.isdir(repository['path'] + '/.git')):
					print "Directory %s is not a Git repository" % repository['path']
					sys.exit(2)
				myClass.clearLock(repository['path'])

		return myClass.config

	def do_POST(self):
		urls = self.parseRequest()
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
						call(['echo "Error during \'pull\' or \'deploy\' operation on path: ' + repo['path'] + '"'], shell=True)
					finally:
						self.unlock(repo['path'])

	def parseRequest(self):
		contenttype = self.headers.getheader('content-type')
		length = int(self.headers.getheader('content-length'))
		body = self.rfile.read(length)

		items = []
		
		try:
			if contenttype == "application/json" or contenttype == "application/x-www-form-urlencoded":
				post = urlparse.parse_qs(body)

			# If payload is missing, we assume gitlab syntax.
			if contenttype == "application/json" and "payload" not in post:
				mode = "github"
			# If x-www-form-urlencoded, we assume bitbucket syntax.
			elif contenttype == "application/x-www-form-urlencoded":
				mode = "bitbucket"
			# Oh Gitlab, dear Gitlab...
			else:
				mode = "gitlab"

			
			if mode == "github":
				response = json.loads(body)
				items.append(response['repository']['url'])
				
			elif mode == "bitbucket":
				for itemString in post['payload']:
					item = json.loads(itemString)
					items.append("ssh://hg@bitbucket.org" + item['repository']['absolute_url'][0:-1])

			# Otherwise, we assume github/bitbucket syntax.
			elif mode == "gitlab":
				for itemString in post['payload']:
					item = json.loads(itemString)
					items.append(item['repository']['url'])
			
			# WTF?!
			else:
				pass
		except Exception:
			pass

		return items

	def getMatchingPaths(self, repoUrl):
		res = []
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['url'] == repoUrl):
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
	def clearLock(myClass, path):
		call(['sh clear_lock.sh "' + path + '"'], shell=True)

	def pull(self, path, branch):
		if(not self.quiet):
			print "\nPost push request received"
			print 'Updating ' + path
		res = call(['sleep 5; cd "' + path + '" && git fetch origin ; git update-index --refresh &> /dev/null ; git reset --hard origin/' + branch], shell=True)
		call(['echo "Pull result: ' + str(res) + '"'], shell=True)
		return res

	def deploy(self, path):
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['path'] == path):
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
			if(arg == '-d' or arg == '--daemon-mode'):
				GitAutoDeploy.daemon = True
				GitAutoDeploy.quiet = True
			if(arg == '-q' or arg == '--quiet'):
				GitAutoDeploy.quiet = True
			if(arg == '--ssh-keyscan'):
				print 'Scanning repository hosts for ssh keys...'
				self.ssh_key_scan()
			if(arg == '--force'):
				print '[KILLER MODE] Warning: The --force option will try to kill any process ' \
					'using %s port. USE AT YOUR OWN RISK' %GitAutoDeploy.getConfig()['port']
				self.kill_them_all()

		if(GitAutoDeploy.daemon):
			pid = os.fork()
			if(pid > 0):
				sys.exit(0)
			os.setsid()

		self.create_pidfile()

		if(not GitAutoDeploy.quiet):
			print 'Github & Gitlab Autodeploy Service v 0.1 started'
		else:
			print 'Github & Gitlab Autodeploy Service v 0.1 started in daemon mode'

		try:
			self.server = HTTPServer((GitAutoDeploy.getConfig()['host'], GitAutoDeploy.getConfig()['port']), GitAutoDeploy)
			sa = self.server.socket.getsockname()
			print "Listeing on", sa[0], "port", sa[1]
			self.server.serve_forever()
		except socket.error, e:
			if(not GitAutoDeploy.quiet and not GitAutoDeploy.daemon):
				print "Error on socket: %s" % e
				self.debug_diagnosis()
			sys.exit(1)

	def ssh_key_scan(self):
		for repository in GitAutoDeploy.getConfig()['repositories']:
			url = repository['url']
			print "Scanning repository: %s" %  url
			m = re.match('.*@(.*?):', url)
			if(m != None):
				port = repository['port']
				port = '' if port == None else ('-p' + port)
				call(['ssh-keyscan -t ecdsa,rsa ' + port + ' ' + m.group(1) + ' >> $HOME/.ssh/known_hosts'], shell=True)
			else:
				print 'Could not find regexp match in path: %s' % url

	def kill_them_all(self):
		pid = self.get_pid_on_port(GitAutoDeploy.getConfig()['port'])
		if pid == False:
			print '[KILLER MODE] I don\'t know the number of pid that is using my configured port\n ' \
				'[KILLER MODE] Maybe no one? Please, use --force option carefully'
			return False

		os.kill(pid, signal.SIGKILL)
		return True
 
	def create_pidfile(self):
		with open(GitAutoDeploy.getConfig()['pidfilepath'], 'w') as f:
			f.write(str(os.getpid()))

	def read_pidfile(self):
		with open(GitAutoDeploy.getConfig()['pidfilepath'],'r') as f:
			return f.readlines()

	def remove_pidfile(self):
		os.remove(GitAutoDeploy.getConfig()['pidfilepath'])

	def debug_diagnosis(self):
		if GitAutoDeploy.debug == False:
			return

		port = GitAutoDeploy.getConfig()['port']
		pid = self.get_pid_on_port(port)
		if pid == False:
			print 'I don\'t know the number of pid that is using my configured port'
			return
		
		print 'Process with pid number %s is using port %s' % (pid, port)
		with open("/proc/%s/cmdline" % pid) as f:
			cmdline = f.readlines()
			print 'cmdline ->', cmdline[0].replace('\x00', ' ')

	def get_pid_on_port(self,port):
		with open("/proc/net/tcp",'r') as f:
			filecontent = f.readlines()[1:]

		pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
		conf_port = str(GitAutoDeploy.getConfig()['port'])
		mpid = False

		for line in filecontent:
			if mpid != False:
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
		if(self.server is not None):
			self.server.socket.close()

	def exit(self):
		if(not GitAutoDeploy.quiet):
			print '\nGoodbye'
		self.remove_pidfile()
		sys.exit(0)

	def signal_handler(self, signum, frame):
		self.stop()
		if(signum == 1):
			self.run()
			return
		elif(signum == 2):
			print '\nKeyboard Interrupt!!!'
		elif(signum == 6):
			print 'Requested close by SIGABRT (process abort signal). Code 6.'

		self.exit()

if __name__ == '__main__':
	gadm = GitAutoDeployMain()

	signal.signal(signal.SIGHUP, gadm.signal_handler)
	signal.signal(signal.SIGINT, gadm.signal_handler)
	signal.signal(signal.SIGABRT, gadm.signal_handler)
	signal.signal(signal.SIGPIPE, signal.SIG_IGN)

	gadm.run()
