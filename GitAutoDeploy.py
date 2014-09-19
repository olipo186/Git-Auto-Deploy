#!/usr/bin/env python

import json, urlparse, sys, os, signal, socket
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

class GitAutoDeploy(BaseHTTPRequestHandler):

	CONFIG_FILEPATH = './GitAutoDeploy.conf.json'
	config = None
	quiet = False
	daemon = False

	@classmethod
	def getConfig(myClass):
		if(myClass.config == None):
			try:
				configString = open(myClass.CONFIG_FILEPATH).read()
			except:
				sys.exit('Could not load ' + myClass.CONFIG_FILEPATH + ' file')

			try:
				myClass.config = json.loads(configString)
			except:
				sys.exit(myClass.CONFIG_FILEPATH + ' file is not valid json')

			for repository in myClass.config['repositories']:
				if(not os.path.isdir(repository['path'])):
					sys.exit('Directory ' + repository['path'] + ' not found')
				if(not os.path.isdir(repository['path'] + '/.git')):
					sys.exit('Directory ' + repository['path'] + ' is not a Git repository')

		return myClass.config

	def do_POST(self):
		urls = self.parseRequest()
		for url in urls:
			paths = self.getMatchingPaths(url)
			for path in paths:
				self.pull(path)
				self.deploy(path)
		self.respond()

	def parseRequest(self):
		length = int(self.headers.getheader('content-length'))
		body = self.rfile.read(length)
		post = urlparse.parse_qs(body)
		items = []

		# If payload is missing, we assume gitlab syntax.
		if not 'payload' in post and 'repository' in body:
			response = json.loads(body)
			items.append(response['repository']['url'])

		# Otherwise, we assume github syntax.
		else:
			for itemString in post['payload']:
				item = json.loads(itemString)
				items.append(item['repository']['url'])

		return items

	def getMatchingPaths(self, repoUrl):
		res = []
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['url'] == repoUrl):
				res.append(repository['path'])
		return res

	def respond(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/plain')
		self.end_headers()

	def pull(self, path):
		if(not self.quiet):
			print "\nPost push request received"
			print 'Updating ' + path
		call(['cd "' + path + '" && git fetch origin && git update-index --refresh &> /dev/null && git reset --hard origin/master'], shell=True)

	def deploy(self, path):
		config = self.getConfig()
		for repository in config['repositories']:
			if(repository['path'] == path):
				cmds = []
				if 'deploy' in repository:
					cmds.append(repository['deploy'])

				gd = config['global_deploy']
				print gd
				if len(gd[0]) is not 0:
					cmds.insert(0, gd[0])
				if len(gd[1]) is not 0:
					cmds.append(gd[1])

				if(not self.quiet):
					print 'Executing deploy command(s)'
				print cmds
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
			
		if(GitAutoDeploy.daemon):
			pid = os.fork()
			if(pid != 0):
				sys.exit()
			os.setsid()

		self.create_pidfile()

		if(not GitAutoDeploy.quiet):
			print 'Github & Gitlab Autodeploy Service v 0.1 started'
		else:
			print 'Github & Gitlab Autodeploy Service v 0.1 started in daemon mode'

		try:
			self.server = HTTPServer(('', GitAutoDeploy.getConfig()['port']), GitAutoDeploy)
			self.server.serve_forever()
		except socket.error, e:
			print "Error on socket: %s" % e
			self.debug_diagnosis()
			sys.exit(1)	

	def create_pidfile(self):
		mainpid = os.getpid()
		f = open(GitAutoDeploy.getConfig()['pidfilepath'], 'w')
		f.write(str(mainpid))
		f.close()

	def read_pidfile(self):
		f = open(GitAutoDeploy.getConfig()['pidfilepath'],'r')
		pid = f.readlines();
		return pid;

	def remove_pidfile(self):
		os.remove(GitAutoDeploy.getConfig()['pidfilepath'])

	def debug_diagnosis(self):
		if(GitAutoDeploy.getConfig()['debug'] == "True" ):
			f = open("/proc/net/tcp",'r')
			filecontent = f.readlines()
			f.close()
			filecontent.pop(0)

			pids = [int(x) for x in os.listdir('/proc') if x.isdigit()]
			for line in filecontent:
				a_line = " ".join(line.split()).split(" ")
				hexport = a_line[1].split(':')[1]
				decport = str(int(hexport,16))
				inode = a_line[9]

				if(decport  == str(GitAutoDeploy.getConfig()['port'])):
					mpid = False
					for pid in pids:
						try:
							for fd in os.listdir("/proc/%s/fd" % pid):
								cinode = os.readlink("/proc/%s/fd/%s" % (pid, fd))
								try:
									minode = cinode.split("[")[1].split("]")[0]
									if(minode == inode):
										mpid = pid
								except IndexError:
									continue
						
						except OSError:
							continue
					if(mpid != False):
						print 'Process with pid number', mpid, 'is using port', decport
						f = open("/proc/%s/cmdline" % mpid)
						cmdline = f.readlines();
						print 'cmdline ->', cmdline

	def stop(self):
		if(self.server is not None):
			self.server.socket.close()

	def exit(self):
		if(not GitAutoDeploy.quiet):
			print '\nGoodbye'
		self.remove_pidfile()
		sys.exit(0)

	def signal_handler(self, signum, frame):
		if(signum == 1):
			self.stop()
			self.run()
		elif(signum == 2):
			print 'Keyboard Interrupt!!!'
			self.stop()
			self.exit()
		else:
			self.stop()
			self.exit()	

if __name__ == '__main__':
	gadm = GitAutoDeployMain()
	
	signal.signal(signal.SIGHUP, gadm.signal_handler)
	signal.signal(signal.SIGINT, gadm.signal_handler)

	gadm.run()
