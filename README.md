# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
============
```pip install bihan```

Hello World
===========
Create a module (eg __home.py__) with

```python
def index(dialog):
    return "Hello World"
```

and a script, __wsgi.py__

```python
from bihan import application
import home

application.run(modules=[home])
```

This starts a built-in web server on port 8000. Enter 
_http://localhost:8000/index_ in the browser address bar, it shows the
"Hello World" message.

URL dispatching
===============
By default, bihan uses function names as urls : in the modules passed in the
argument _modules_ of `application.run()`, all the callables whose name 
doesn't start with an underscore are accessible by their name.

For instance, the function `index()` in module __home__ is mapped to the url
_/index_.

You can specify another url for the function by setting its attribute `url` :

```python
def index(dialog):
    return "Hello World"
index.url = "/"
```

will associate the url "/" to the function.

The return value of the function is the body of the response sent to the
browser. If it is not a string, it is converted by `str()`.

The argument `dialog`
=====================

The functions that are mapped to urls take a single argument, `dialog`.

`dialog` has two main attributes, `request`, which holds the information sent
by the browser, and `response` which is used to send back information to the
browser.

`dialog.request`
----------------
The attributes of _dialog.request_ are :

- `dialog.request.url` : the requested url (without query string).

- `dialog.request.headers` : the http request headers sent by the user agent.
  Instance of [email.message.Message](https://docs.python.org/3/library/email.message.html).

- `dialog.request.encoding` : the encoding used in the request.

- `dialog.request.cookies` : instance of [http.cookies.SimpleCookie]
  (https://docs.python.org/3/library/http.cookies.html), holds the cookies 
  sent by the user agent.

- if the request is sent with the GET method, or the POST method with
  enctype or content-type set to 'application/x-www-form-urlencoded' or 
  'multipart/...' :

  - `dialog.request.fields` : a dictionary for key/values received 
    either in the query string, or in the request body for POST
    requests. Keys and values are strings, not bytes.

- else :

  - `dialog.request.raw` : request body as bytes for requests of other types (eg
    Ajax requests with JSON content).
  
  - `dialog.request.json()` : function with no argument that returns a
    dictionary built as the parsing of request body.

`dialog.response`
-----------------
The attributes that can be set to `dialog.response` are:

- `dialog.response.headers` : the HTTP response headers. Instance of
  [email.message.Message](https://docs.python.org/3/library/email.message.html)

- `dialog.response.cookie` : instance of [http.cookies.SimpleCookie]
  (https://docs.python.org/3/library/http.cookies.html), used to set cookies 
  to send to the user agent with the response.

- `dialog.response.encoding` : Unicode encoding to use to convert the 
  string returned by script functions into a bytestring. Defaults to 
  "utf-8".

other attributes of `dialog`
----------------------------
- `dialog.root` : path of document root in the server file system.

- `dialog.environ` : WSGI environment variables.

- `dialog.error` : an exception to raise if the script wants to return an
  HTTP error code, eg `raise dialog.error(404)`.

- `dialog.redirection` : an exception to raise if the script wants to 
  perform a temporary redirection (302) to a specified URL : 
  `raise dialog.redirection(url)`.

- `dialog.template(filename, **kw)` : if the templating engine [patrom]
  (https://github.com/PierreQuentel/patrom) is installed, renders the template 
  file at the location __templates/<filename>__ with the key/values in `kw`.