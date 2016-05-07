import unittest

class WebhookTestCaseBase(unittest.TestCase):

    thread = None

    def setUp(self):
        import sys

        # Use our custom importer to replace certain modules with stub modules to
        # enable testing of other parts of GAD
        sys.meta_path.append(StubImporter())

    def start_gad(self, test_config):
        import sys
        import time
        import os

        # Add repo root to sys path
        repo_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
        sys.path.insert(1, repo_root)

        from gitautodeploy.cli.config import get_config_defaults, init_config

        config = get_config_defaults()
        config.update(test_config)

        init_config(config)

        # Create a GAD instance
        self.thread = GADRunnerThread(config)

        # Run GAD in a thread
        self.thread.start()

    def gad_port(self):
        return self.thread.port

    def await_gad(self):
        """Waits for GAD and all it's threads to complete."""
        import threading

        # Wait for GAD runner thread to finish
        self.thread.join()

        # Wait for all request handler threads to finish
        main_thread = threading.currentThread()
        for current_thread in threading.enumerate():
            if current_thread == main_thread:
                continue
            #print "Waiting for thread %s to finish" % current_thread
            current_thread.join()

    def tearDown(self):
        pass


class StubImporter(object):

    overload_modules = ['gitautodeploy.wrappers.git', 'gitautodeploy.wrappers.process']

    def find_module(self, full_name, package_path):

        # Intervene when any wrapper module is imported
        if full_name in self.overload_modules:

            # Return a loader
            return self

        return None

    def load_module(self, full_name):
        """Load matching module from stubs package (test stub) instead of main gitautodeploy package."""
        import imp
        import sys
        import os

        repo_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

        module_name = full_name.split('.')[-1]
        module_info = imp.find_module(module_name, [repo_root+'/test/stubs'])
        module = imp.load_module(module_name, *module_info)
        sys.modules[module_name] = module

#        print "returning module %s" % module_name

#        module.history.append('WAH')

        # Return a module
        return module


import threading

class GADRunnerThread(threading.Thread):
    def __init__(self, config):
        super(GADRunnerThread, self).__init__()
        import sys
        import time

        from gitautodeploy import GitAutoDeploy

        self._app = GitAutoDeploy()
        self._app.setup(config)

        # Store PID and port in thread instance
        self.pid = self._app._pid
        self.port = self._app._port

    def run(self):
        self._app.handle_request()

    def exit(self):
        self._app.stop()
        self._app.close()
