import unittest
from utils import WebhookTestCaseBase

class WebhookTestCase(WebhookTestCaseBase):

    test_case = None
    test_name = None

    def set_test_case(self, test_case, test_name):
        self.test_case = test_case
        self.test_name = test_name

    def shortDescription(self):
        return self.test_name[:-15]

    def runTest(self):
        import requests
        import json

        # GAD configuration for this test case
        config = {
            'port': 0,
            'intercept-stdout': False,
            'detailed-response': True,
            'log-level': 'ERROR',
            'repositories': []
        }

        if 'url' in self.test_case['config']:
            config['repositories'].append(self.test_case['config'])

        # Start GAD instance
        self.start_gad(config)

        # Send webhook request
        session = requests.session()
        response = requests.post('http://localhost:%s/' % self.gad_port(), data=json.dumps(self.test_case['payload']), headers=self.test_case['headers'])

        # Verify response status
        self.assertEqual(response.status_code, self.test_case['expected']['status'])

        # Compare results
        #if 'data' in self.test_case['expected']:
        #    actual = json.dumps(response.json())
        #    expected = json.dumps(self.test_case['expected']['data'])
        #    self.assertEqual(actual, expected)

        # Wait for GAD to handle the request
        self.await_gad()

def suite():
    import os
    import json

    suite = unittest.TestSuite()

    # Look for test cases in samples dir
    samples_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'samples')
    for item in os.listdir(samples_dir):

        if not item[-15:] == '.test-case.json':
            continue

        file = open(os.path.join(samples_dir, item), 'r')
        test_case = json.loads(file.read())

        t = WebhookTestCase()
        t.set_test_case(test_case, item)

        suite.addTest(t)

    return suite

def main():
    from unittest import TestResult
    #result = TestResult()
    #suite().run(result)
    #unittest.main()
    #print result
    s = suite()
    result = unittest.TextTestRunner(verbosity=2).run(s)

if __name__ == '__main__':
    main()
