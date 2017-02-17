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

with application.register:
    import home

application.run()
```

This starts a built-in web server on port 8000. Enter 
_http://localhost:8000/index_ in the browser address bar, it shows the
"Hello World" message.

URL dispatching
===============
bihan maps urls to callables (usually functions) in the _registered modules_.

Registered modules
------------------
The name "module" in this paragraph is used both for modules and packages.

The _registered modules_ are determined inside the `with application.register`
block. They are all the modules imported inside this block, including those
that they may themselves import. 

Only the modules whose source file is in inside the application directory are 
registered (modules from the standard library for instance are not
registered).

To prevent a module imported in the `with` block from being registered, put
the line

```python
__expose__ = False
```

Mapping a url to a function in a registered module
--------------------------------------------------
By default, bihan uses function names as urls : all the functions whose name 
doesn't start with an underscore are accessible by their name.

For instance, the function `index()` in module __home__ is mapped to the url
_/index_.

You can specify another url for the function by setting its attribute `url` :

```python
def index(dialog):
    return "Hello World"
index.url = "/"
```

If a module defines a variable `__prefix__`, it is prepended to the url for
all the functions in the module :

```python
__prefix__ = "books"

def show(dialog):
    ...
```
will map the url _books/show_ to the function `show()`

If a callable must not be made accessible, set its attribute `__expose__` to
`False`.

Smart URLs
----------
If the url includes parts of the form `<x>`, the value matching `x` we be
available as one the request fields.

For instance :

```python
def show(dialog):
    return "showing record #{}".format(dialog.request.fields['num'])
index.url = "/show/<num>"
```

Mapping control
---------------
bihan makes sure that a url matches only one callable in a _registered
module_. Otherwise it raises a `RoutingError`, with a message giving the
scripts and functions that define the same url.

Application attributes and methods
==================================

- `application.debug` sets the debug mode. If `True`, all the modules are
  reloaded at each request, so that changes made to the scripts are taken
  into account and the mapping between urls and functions is reset.
  Defaults to `True`.
  
- `application.root` is a path in the server file system. It will be
  available in scripts as `dialog.root`.

- `application.run([host, [port]])` starts the application on the development
  server, on the specified host and port. _host_ defaults to `"localhost"` 
  and _port_ to `8000`.

- `application.static` is a dictionary mapping paths of the form "/path" and 
  directories in the server file system. It it used to serve static files 
  (HTML pages, images, Javascript programs, etc.). By default, the dictionary 
  maps "/static" to the folder __static__ in the server directory.
  

Response body
=============

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
  file at the location __templates/filename__ with the key/values in `kw`.
  
Development server
==================
The built-in development server checks the changes made to all the modules
used by the application and located in the application directory. If the
source code of one of these modules is changed, the application is restarted.

If an exception happens when reloading the registered modules, the server 
doesn't crash, but the exception is stored and will be shown as the result of
the next request.