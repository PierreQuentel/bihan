import os
import time
import unittest
import urllib.parse
import urllib.request
import json

from wsgiref.simple_server import make_server

from test import support
threading = support.import_module('threading')

class TestServerThread(threading.Thread):

    def __init__(self, test_object):
        threading.Thread.__init__(self)
        self.test_object = test_object

    def run(self):
        application.load_routes()
        self.server = make_server('localhost', 8080, application)
        self.test_object.server_started.set()
        self.test_object = None
        try:
            self.server.serve_forever(0.05)
        finally:
            self.server.server_close()

    def stop(self):
        self.server.shutdown()

class NoRedirection(urllib.request.HTTPErrorProcessor):

    def http_response(self, request, response):
        return response

    https_response = http_response

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self._threads = support.threading_setup()
        os.environ = support.EnvironmentVarGuard()
        self.server_started = threading.Event()
        self.thread = TestServerThread(self)
        self.thread.start()
        self.server_started.wait()

    def tearDown(self):
        self.thread.stop()
        self.thread = None
        os.environ.__exit__()
        support.threading_cleanup(*self._threads)

def request(path, **kw):
    url = "http://localhost:8080{}"
    if "data" in kw:
        kw["data"] = urllib.parse.urlencode(kw["data"]).encode("utf-8")
        return urllib.request.urlopen(url.format(path), **kw)
    else:
        return urllib.request.urlopen(url.format(path))


class Test(BaseTestCase):
    
    def test_basic(self):
        req = request('/')
        self.assertEqual(req.read(), b'hello')

    def test_argument(self):
        # GET request
        req = request('/show_argument?x=1&y=arg')
        res = json.loads(req.read().decode('utf-8'))
        self.assertEqual(res, {'x': '1', 'y': 'arg'})
        # POST request
        req = request('/show_argument', data={'x':2, 'y': 'arg'})
        res = json.loads(req.read().decode('utf-8'))
        self.assertEqual(res, {'x': '2', 'y': 'arg'})
        
    def test_smart_url(self):
        req = request('/test_smart_url/99')
        self.assertEqual(req.read(), b'99')

    def test_very_smart_url(self):
        req = request('/very_smart/a/url/99')
        self.assertEqual(req.read(), b"('a', '99')")
        
    def test_redirection(self):
        opener = urllib.request.build_opener(NoRedirection)
        response = opener.open('http://localhost:8080/redirection')
        self.assertEqual(response.code, 302)
        self.assertEqual(response.headers['Location'], '/foo')
    
    def test_error403(self):
        opener = urllib.request.build_opener(NoRedirection)
        response = opener.open('http://localhost:8080/error403')
        self.assertEqual(response.code, 403)
        assert response.reason.startswith("('Forbidden'")
        
    def test_error404(self):
        opener = urllib.request.build_opener(NoRedirection)
        response = opener.open('http://localhost:8080/i_don_t_exist')
        self.assertEqual(response.code, 404)

    def test_func_in_package_is_not_exposed(self):
        opener = urllib.request.build_opener(NoRedirection)
        response = opener.open('http://localhost:8080/func_init')
        self.assertEqual(response.code, 404)
    
    def test_url_with_trailing_slash(self):
        req = request('/trailing_slash/')
        self.assertEqual(req.read(), b"trailing slash")

    def test_url_without_trailing_slash_redirects(self):
        opener = urllib.request.build_opener(NoRedirection)
        response = opener.open('http://localhost:8080/trailing_slash')
        self.assertEqual(response.code, 302)
        self.assertEqual(response.headers['Location'], '/trailing_slash/')
        
# start server in a thread
from bihan import application
from scripts import index

unittest.main()