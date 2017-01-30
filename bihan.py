"""Script server handling GET and POST requests, HTTP redirection

Runs Python functions defined in scripts, with one argument representing the
dialog (request+response) :

    1. dialog.request : information sent by user agent to server
    
      - dialog.request.url : requested url (without query string)

      - dialog.request.headers : the http request headers sent by user agent
      
      - dialog.request.encoding : encoding used in request

      - dialog.request.cookies : instance of http.cookies.SimpleCookie, holds 
        the cookies sent by user agent

      - if the request is sent with the GET method, or the POST method with
        enctype or content-type set to 'application/x-www-form-urlencoded' or 
        'multipart/...' :

          - dialog.request.fields : a dictionary for key/values received 
            either in the query string, or in the request body for POST 
            requests. Keys and values are strings, not bytes

      - else :

          - dialog.request.raw : for requests of other types (eg Ajax requests 
            with JSON content), request body as bytes
          
          - dialog.request.json() : function with no argument that returns a
            dictionary built as the parsing of request body 

    2. dialog.response : data set by script
    
      - dialog.response.headers : the HTTP response headers
    
      - dialog.response.cookie : instance of http.cookies.SimpleCookie, used 
        to set cookies to send to the user agent with the response

      - dialog.response.encoding : Unicode encoding to use to convert the 
        string returned by script functions into a bytestring. Defaults to 
        "utf-8".

    3. variables, exceptions and functions used in the script
    
      - dialog.root : path of document root in the server file system

      - dialog.environ : WSGI environment variables
    
      - dialog.error : an exception to raise if the script wants to return an
        HTTP error code : raise dialog.error(404)

      - dialog.redirection : an exception to raise if the script wants to 
        perform a temporary redirection (302) to a specified URL : 
        raise dialog.redirection(url)
      
      - dialog.template(filename, **kw) : renders the template file at
        templates/<filename> with the key/values in kw

The response body is the return value of the function. If it is a string, it
is converted in bytes using dialog.response.encoding.

Attributes of class Application :

    - root : document root. Defaults to current directory.
    
    - static : list of directories for static files. Defaults to subdirectory
      "static" of document root.

    - dispatch(mapping) : mapping maps url patterns to callables. If a url 
      matches the pattern, the associated function will be executed. The 
      pattern may include the form <name>, in this case dialog.request.fields 
      has the key "name".
      
      For instance if mapping is 
      
          {'test/<book_id>': module.function}
      
      calling url 'test/3' will run module.function(dialog) with 
      dialog.request.fields set to {'book_id': '3'}

"""

import sys
import os
import imp
import importlib
import re
import io
import traceback
import datetime
import string
import types
import collections
import random
import tokenize

import html.parser

import cgi
import urllib.parse
import http.cookies
import http.server
import email.utils
import email.message
import json


class HttpRedirection(Exception):pass
class HttpError(Exception):pass
class DispatchError(Exception): pass
class RoutingError(Exception): pass


class Message:

    def __init__(self):
        self.headers = email.message.Message()
        self.cookies = http.cookies.SimpleCookie()


class Dialog:
    """Instances of Dialog are passed as arguments to the script functions.
    They have attributes taken from the application instance."""

    def __init__(self, obj):
        self.request = obj.request
        self.response = obj.response
        self.root = obj.root
        self.environ = obj.env
        self.template = obj.template
        self.redirection = HttpRedirection
        self.error = HttpError


class application(http.server.SimpleHTTPRequestHandler):

    root = os.getcwd()
    static = {'static': 'static'}
    patterns = {}
    config_file = os.path.join(root, 'config.json')

    def __init__(self, environ, start_response):
    
        self.env = environ
        self.start_response = start_response

        # Set attributes for logging
        path = self.env['PATH_INFO']
        if self.env['QUERY_STRING']:
            path += '?'+self.env['QUERY_STRING']
        
        self.request_version = self.env['SERVER_PROTOCOL']
        self.requestline = '%s %s %s' %(self.env['REQUEST_METHOD'],
            path, self.request_version)
        self.client_address = [self.env['REMOTE_ADDR'],
            self.env.get('REMOTE_PORT', self.env['SERVER_PORT'])]

        # Initialise attribute "request" from data sent by user agent
        self.request = request = Message()
        request.url = self.env['PATH_INFO']
        request.method = self.env['REQUEST_METHOD']
        
        for key in self.env:
            if key=='HTTP_COOKIE':
                request.cookies = http.cookies.SimpleCookie(self.env[key])
            elif key.startswith('HTTP_'):
                request.headers[key[5:]] = self.env[key]
            elif key.upper() == 'CONTENT_LENGTH':
                request.headers['Content-Length'] = self.env[key]
            elif key.upper() == 'CONTENT_TYPE':
                request.headers['Content-Type'] = self.env[key]

        # Initialise attribute "response"
        self.response = Message()
        self.response.encoding = "utf-8"

        self.status = "200 Ok"

    def __iter__(self):
        """Iteration expected by the WSGI protocol. Calls start_response
        then yields the response body
        """
        try:
            self.get_request_fields()
            self.handle()
        except:
            import traceback
            out = io.StringIO()
            traceback.print_exc(file=out)
            self.response.headers['Content-type'] = "text/plain"
            self.response.body = out.getvalue().encode(self.response.encoding)

        self.start_response(str(self.status), self.response_headers())
        yield self.response.body

    def get_request_fields(self):
        """Set self.request.fields, a dictionary indexed by field names
        If field name ends with [], the value is a list of values
        Else, it is a single value, or a list if there are several values
        """
        request = self.request
        request.fields = {}

        # Get request fields from query string
        fields = cgi.parse_qs(self.env.get('QUERY_STRING',''), 
            keep_blank_values=1)
        
        for key in fields:
            if key.endswith('[]'):
                request.fields[key[:-2]] = fields[key]
            elif len(fields[key])==1:
                request.fields[key] = fields[key][0]
            else:
                request.fields[key] = fields[key]

        if request.method in ['POST', 'PUT', 'DELETE']:

            # Get encoding of request data
            charset = 'utf-8'
            for key in request.headers:
                mo = re.search('charset\s*=(.*)$', request.headers[key])
                if mo:
                    charset = mo.groups()[0]
                    break
            request.encoding = charset

            fp = self.env['wsgi.input']

            has_keys = True
            if 'content-type' in request.headers:
                ctype, pdict = cgi.parse_header(request.headers['content-type'])
                has_keys = ctype == 'application/x-www-form-urlencoded' or \
                    ctype.startswith('multipart/')

            # If data is not structured with key and value (eg JSON content),
            # only read raw data and set attribute "raw" and "json" of request 
            # object
            if not has_keys:
                length = int(request.headers['content-length'])
                request.raw = fp.read(length)
                def _json():
                    return json.loads(request.raw.decode(charset))
                request.json = _json
                return

            # Update request fields from POST data
            body = cgi.FieldStorage(fp, headers=request.headers,
                environ={'REQUEST_METHOD':'POST'})

            data = {}
            for k in body.keys():
                if isinstance(body[k],list): # several fields with same name
                    values = [x.value for x in body[k]]
                    if k.endswith('[]'):
                        data[k[:-2]] = values
                    else:
                        data[k] = values
                else:
                    if body[k].filename: # file upload : don't read the value
                        data[k] = body[k]
                    else:
                        if k.endswith('[]'):
                            data[k[:-2]] = [body[k].value]
                        else:
                            data[k] = body[k].value
            request.fields.update(data)
            
    def handle(self):
        """Process the data received"""
        response = self.response
        self.elts = urllib.parse.urlparse(self.env['PATH_INFO']+
            '?'+self.env['QUERY_STRING'])
        self.url = self.elts[2]
        response.headers.add_header("Content-type",'text/html') # default

        kind, arg = self.resolve(self.url)
        if kind=='file':
            if not os.path.exists(arg):
                return self.send_error(404, 'File not found', 
                    'No file matching {}'.format(self.url))
            return self.send_static(arg)
        
        func, kw = arg
        self.request.fields.update(kw)

        # Run function
        return self.run_script(func)

    def send_static(self, fs_path):
        """Send the content of a file in a static directory"""
        try:
            f = open(fs_path,'rb')
        except IOError:
            return self.send_error(404, "File not found",
                "No file found for given url")
        # Use browser cache if possible
        if "If-Modified-Since" in self.request.headers:
            ims = email.utils.parsedate(
                self.request.headers["If-Modified-Since"])
            if ims is not None:
                ims_datetime = datetime.datetime(*ims[:7])
                ims_dtstring = ims_datetime.strftime("%d %b %Y %H:%M:%S")
                last_modif = datetime.datetime.utcfromtimestamp(
                    os.stat(fs_path).st_mtime).strftime("%d %b %Y %H:%M:%S")
                if last_modif == ims_dtstring:
                    self.done(304, io.BytesIO())
                    return
        ctype = self.guess_type(fs_path)
        self.response.headers.set_type(ctype)
        self.response.headers['Content-length'] = str(os.fstat(f.fileno())[6])
        self.done(200,f)

    def load_routes(self):
        """Returns a mapping between regular expressions and paths to 
        scripts and callables
        """
        # on debug mode, reload all modules in application folders
        if application.debug:
            for name, module in sys.modules.items():
                if name == "__main__":
                    continue
                filename = getattr(module, "__file__", "")
                if filename.startswith(application.root):
                    try:
                        imp.reload(module) # deprecated in version 3.4
                    except AttributeError:
                        importlib.reload(module)
        mapping = {}
        for module in application.modules:
            for key in dir(module):
                obj = getattr(module, key)
                if callable(obj) and not key.startswith('_'):
                    url = obj.url if hasattr(obj, "url") else "/"+key
                    pattern = '^'+re.sub('<(.*?)>', r'(?P<\1>[^/]+?)', url)+'$'
                    value = module.__file__+'/'+key
                    mapping[pattern] = value
        return mapping

    def resolve(self, url):
        """Combine url and the routes defined for the application to return 
        # a file path, function name and additional arguments.
        """
        # Split url in elements separated by /
        elts = urllib.parse.unquote(url).lstrip('/').split('/')

        target, patterns = None, []
        for pattern, func in self.load_routes().items():
            mo = re.match(pattern, url, flags=re.I)
            if mo:
                patterns.append(pattern)
                if target is not None:
                    # If more than one pattern matches the url, refuse to guess
                    msg = 'url %s matches at least 2 patterns : %s'
                    raise DispatchError(msg %(url, patterns))
                target = (func, mo.groupdict())
        if target is not None:
            return 'func', target

        # finally, try a path in the file system
        return 'file', os.path.join(self.root, *elts)

    def run_script(self, path):
        """Run the function specified by string path
        path has the form module/callable
        module is a path to a Python script
        """
        module, call = path.rsplit('/', 1)
        path = os.path.join(self.root, *module.split('/'))
        with open(path, encoding="utf-8") as fobj:
            src = fobj.read()
        ns = {}
        initial_modules = list(sys.modules)
        exec(src, ns)
        func = ns[call]
        try:
            # run function with Dialog(self) as positional argument
            result = func(Dialog(self))
        except HttpRedirection as url:
            self.response.headers['Location'] = url
            return self.done(302,io.BytesIO())
        except HttpError as err:
            return self.done(err.args[0], io.BytesIO())
        except: # Other exception : print traceback
            result = io.StringIO()
            traceback.print_exc(file=result)
            result = result.getvalue() # string
            return self.send_error(500, 'Server error', result)

        # Get response encoding
        encoding = self.response.encoding
        if not "charset" in self.response.headers["Content-type"]:
            if encoding is not None:
                ctype = self.response.headers["Content-type"]
                self.response.headers.replace_header("Content-type",
                    ctype + "; charset=%s" %encoding)

        # Build response body as a bytes stream
        output = io.BytesIO()
        
        if self.request.method != 'HEAD':
            if isinstance(result, bytes):
                output.write(result)
            elif isinstance(result, str):
                try:
                    output.write(result.encode(encoding))
                except UnicodeEncodeError:
                    msg = io.StringIO()
                    traceback.print_exc(file=msg)
                    return self.done(500,
                        io.BytesIO(msg.getvalue().encode('ascii')))
            else:
                output.write(str(result).encode(encoding))

        response_code = getattr(self.response, 'status', 200)
        self.response.headers['Content-length'] = output.tell()
        self.done(response_code, output)

    def template(self, filename, **kw):
        """Returns a string : the template at /templates/filename executed 
        with the data in kw
        """
        from patrom import TemplateParser, TemplateError
        parser = TemplateParser()
        path = os.path.join(application.root, 'templates', filename)
        try:
            result = parser.render(path, **kw)
            self.response.headers.set_type("text/html")
        except TemplateError as exc:
            result = str(exc)
            self.response.headers.set_type('text/plain')
        return result

    def send_error(self, code, expl, msg=''):
        self.status = '%s %s' %(code, expl)
        self.response.headers.set_type('text/plain')
        self.response.body = msg.encode(self.response.encoding)

    def response_headers(self):
        headers = [(k, str(v)) for (k,v) in self.response.headers.items()]
        for morsel in self.response.cookies.values():
            headers.append(('Set-Cookie', morsel.output(header='').lstrip()))
        return headers

    def done(self, code, infile):
        """Send response, cookies, response headers and the data read from 
        infile
        """
        self.status = '%s %s' %(code, 
            http.server.BaseHTTPRequestHandler.responses[code])
        if code == 500:
            self.response.headers.set_type('text/plain')
        infile.seek(0)
        self.response.body = infile.read()

    @classmethod
    def run(cls, port=8000, modules=None, debug=True):
        application.debug = debug
        # scripts is a list of modules
        application.modules = modules or []
        from wsgiref.simple_server import make_server
        httpd = make_server('localhost', port, application)
        print("Serving on port %s" %port)
        httpd.serve_forever()

if __name__ == '__main__':
    application.run(port=8000)