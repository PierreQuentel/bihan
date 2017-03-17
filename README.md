# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
============
```pip install bihan```

Hello World
===========

```python
from bihan import application

def index(dialog):
    return "Hello World"

application.run()
```

This starts a built-in web server on port 8000. Enter 
_http://localhost:8000/index_ in the browser address bar, it shows the
"Hello World" message.

URL dispatching
===============
Registered modules
------------------
bihan maps urls to functions in the _registered modules_ ("module" in this
paragraph is used both for modules and packages).

The registered modules are the main module, and all the modules _in the 
application directory_ (ie not from the standard library or third-party)
that are imported in the main module.

For instance, if the main module is

```python
import datetime
from bihan import application

# menu is a module in the same directory as this script
import menu
# scripts is a package, also in the same directory
from scripts import views

def index(dialog):
    now = datetime.datetime.now()
    return "Hello, it's {}:{}".format(now.hour, now.minute)

application.run()
```

then modules `menu` and `views` are registered, but not `datetime` because it
is in the standard library.

The name of a _registered module_ must be in the main script namespace. An
import like `import scripts.views` doesn't register the module __views__ ; it
must be imported with `from scripts import views`.

If a module is imported in the main module but must not be registered, put
this line at the beginning :

```python
__expose__ = False
```

Mapping a url to a function in a registered module
--------------------------------------------------
By default, bihan uses function names as urls : all the functions whose name 
doesn't start with an underscore are accessible by their name.

For instance, if a registered module has this function:

```python
def users(dialog):
    return "Here is a list of users"
```

the function is mapped to the url _/users_.

You can specify another url for the function by setting its attribute `url` :

```python
def users(dialog):
    return "Here is a list of users"
users.url = "/show_users"
```

If a registered module defines a variable `__prefix__`, it is prepended to the
url for all the functions in the module :

```python
__prefix__ = "library"

def users(dialog):
    ...
```
will map the url _library/users_ to the function `users()`

If a function must not be mapped to a url, set its attribute `__expose__` to
`False` :

```python
__prefix__ = "library"

def users(dialog):
    ...
users.__expose__ = False
```


Smart URLs
----------
If the url includes parts of the form `<x>`, the value matching `x` will be
available as one the request fields.

For instance :

```python
def show(dialog):
    ...
index.url = "/show/<num>"
```

This function is called for urls like _/show/76_, and the value (76) is
available in the function body as `dialog.request.fields["num"]`.

Mapping control
---------------
bihan makes sure that a url matches only one function in a _registered
module_. Otherwise it raises a `RoutingError`, with a message giving the
scripts and functions that define the same url.

Application attributes and methods
==================================

- `application.debug` sets the debug mode. If `True`, all the modules are
  reloaded at each request, so that changes made to the scripts are taken
  into account and the mapping between urls and functions is reset.
  Defaults to `True`.
  
- `application.root` is a path in the server file system. It is available in
  scripts as `dialog.root`. Defaults to the application directory.

- `application.run([host, [port]])` starts the application on the development
  server, on the specified host and port. _host_ defaults to `"localhost"` 
  and _port_ to `8000`.

- `application.static` is a dictionary mapping paths of the form _/path_ to 
  directories in the server file system. It it used to serve static files 
  (HTML pages, images, Javascript programs, etc.). By default, the dictionary 
  maps _/static_ to the folder __static__ in the server directory.
  

Response body
=============

The return value of the function is the body of the response sent to the
user agent. If it is not a string, it is converted by `str()`.

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

- `dialog.request.cookies` : instance of 
  [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html),
  holds the cookies sent by the user agent.

- if the request is sent with the GET method, or the POST method with
  enctype or content-type set to "application/x-www-form-urlencoded" or 
  "multipart/..." :

  - `dialog.request.fields` : a dictionary for key/values received either in
    the query string, or in the request body for POST requests, or in named 
    arguments in _smart urls_ (see above). Keys and values are strings, not
    bytes.

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

- `dialog.response.cookie` : instance of
  [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html),
  used to set cookies  to send to the user agent with the response.

- `dialog.response.encoding` : Unicode encoding to use to convert the 
  string returned by script functions into a bytestring. Defaults to 
  "utf-8".

other attributes of `dialog`
----------------------------
- `dialog.root` : path of document root in the server file system.

- `dialog.environ` : WSGI environment variables.

- `dialog.error` : used if the script wants to return an HTTP error code, eg 
  `return dialog.error(404)`.

- `dialog.redirection` : used if the script wants to perform a temporary
  redirection (302) to a specified URL : 
  `return dialog.redirection(url)`.

- `dialog.template(filename, **kw)` : if the templating engine 
  [patrom](https://github.com/PierreQuentel/patrom) is installed, renders the
  template file at the location __templates/filename__ with the key/values in
  `kw`.

Development server
==================
The built-in development server periodically checks the changes made to all 
the modules used by the application (registered or not) and located in the 
application directory, including the main module. If the source code of one of
these modules is changed, the application is restarted.

If an exception happens when reloading the registered modules, the server 
doesn't crash, but the exception is stored and will be shown as the result of
the next request.
