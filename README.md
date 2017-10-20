# bihan
bihan (small, in breton) is a minimalist web framework.

Why create yet another one when we already have well-known competitors ? Well,
I have used Flask for some time and it's great, but there are a few things in
it that I don't like or understand:

- the magical `request` object

- each script must begin with `from flask import Flask, request, ...`

- the mapping between urls and functions uses a decorator, and I almost always
  give the url name to the function ; it would be easier if the mapping
  between url and function name was done by the framework, at least by default

- to get the value of a form field, the attribute of `request` is not the same
  for GET (`request.args`) and POST (`request.post`) requests, I don't
  understand why

- if a key is missing in `request.args` or `request.form`, a 400 error message
  is returned, even on debug mode. Debugging would be easier with a `KeyError`
  exception traceback

- on debug mode, when there is a syntax error in one of the scripts, the
  built-in server crashes when I save the file

bihan is a very lightweight WSGI framework, with a single file like Bottle.
Its design principles are:

- requests are served by functions and classes defined in _registered modules_

- classes are used if the same url can be called with different HTTP methods
  (GET, POST...), in a REST API for example ; functions can be used when the
  HTTP method is not relevant

- by default, the function/class name is used to serve the url of the same
  name (but the mapping can be customized if necessary)

- functions, or class methods, take a single argument representing the request
  / response dialog

Installation
============
```pip install bihan```

Hello World
===========

```python
from bihan import application

function hello(dialog):
    return "Hello World"

application.run()
```

This script starts a built-in web server on port 8000. Enter
_http://localhost:8000/hello_ in the browser address bar, it shows the
"Hello World" message.

URL dispatching
===============
Registered modules
------------------
bihan serves requests using the functions and classes defined in the
_registered modules_, which are:

- the main module, ie the one where the application is started by
  `application.run()`
- all the modules _in the application directory_ (ie not from the standard
  library or third-party) that are imported in the main module

For instance, if the main module is

```python
import datetime
from bihan import application

# menu is a module in the same directory as this script
import menu

# scripts is a package, also in the same directory
from scripts import views

function hello(dialog):
    now = datetime.datetime.now()
    return "Hello, it's {}:{}".format(now.hour, now.minute)

application.run()
```

then the _registered modules_ are the main module, plus the modules `menu` and
`views` ; `datetime` is not registered because it is in the standard library.

The name of a _registered module_ must be in the main script namespace. An
import like `import scripts.views` doesn't register the module __views__ ; it
must be imported with `from scripts import views`.

If a module is imported in the main module but must _not_ be registered, put
this line at the beginning :

```python
__register__ = False
```

Mapping a url to a function or a class in a registered module
-------------------------------------------------------------
By default, all the functions and classes defined in a registered module (not
those imported from another module) are accessible by their name. Functions
and classes whose name starts with an underscore are ignored.

A function serves all the requests sent to the url, regardless of the HTTP
method (GET, POST, etc.).

A class serves a GET request to the url by its method `get()`, a POST request
by its method `post()`, etc.

For instance, if a registered module includes:

```python
function menu(dialog):
    return "Application menu"

class user:

    def get(self):
        """Returns information about a user."""

    def post(self):
        """Replace or create a user."""

    def delete(self):
        """Delete a user."""
```

then the application handles:

- all the requests to the url _/menu_ with the function `menu`
- GET requests to the url _/user_ with method `get` of class `user`
- POST requests to the url _/user_ with method `post` of class `user`, etc.

Customize url mapping
---------------------
If the module defines a variable `__prefix__`, it is prepended to the url for
all the functions and classes in the module :

```python
__prefix__ = "library"

class user:
    ...
```
will map the url _library/user_ to the class `user`

Special case : if a function or class is called `index`, it is also mapped by
default to the url _/_.

To specify another url (including _smart urls_, see below) for a class, set
the class attribute _url_ (a single url) or _urls_ (a list of urls):

```python
class user:

    url = '/user/<id>'

    def get(self):
        ...
```

or

```python
class user:

    urls = ['/user', '/user/<id>']

    def post(self):
        ...
```

The url(s) can also be specified at the method level:

```python
class user:

    def post(self):
        """Serves POST requests on urls /user and /user/<id>."""
    post.urls = ["/user", "/user/<id>"]
```

For a function:

```python
def menu(dialog):
    return "Application menu"
menu.url = "/mymenu"
```

Smart URLs
----------
If the url includes parts of the form `<x>`, the value matching `x` will be
available as one the request fields.

For instance :

```python
function show(dialog):
    ...
show.url = "/show/<num>"
```

Function `show()` is called for urls like _/show/76_, and the value
(the string "76") is available in the function body as
`dialog.request.fields["num"]` (see the attributes of `dialog` below).

Mapping control
---------------
If the same tuple (HTTP method, url) is defined more than once, a
`RoutingError` is raised, with a message giving the functions or classes that
define the same route.


Application attributes and methods
==================================

`application.root`

> A path in the server file system. Defaults to the application directory.

`application.run(host="localhost", port=8000, debug=False)`

> Starts the application on the development server, on the specified _host_
> and _port_.
>
> _debug_ sets the debug mode. If `True`, the program periodically checks if
> a change has been made to the modules used by the application (registered or
> not) and located in the application directory, including the main module. If
> the source code of one of these modules is changed, the application is
> restarted.
>
> If an exception happens when restarting the application, the server doesn't
> crash, but the exception is stored and will be shown as the result of the
> next request.


`application.static`

> A dictionary mapping paths of the form _/path_ to directories in the server
> file system. It it used to serve static files (HTML pages, images,
> Javascript programs, etc.). By default, the dictionary maps _/static_ to the
> folder __static__ in the server directory.


Response body
=============

The response body is the return value of the method that serves the request.

If the return value is a bytes objects, it is returned unmodified.

If it is a string, it is encoded with the attribute `encoding` of
`dialog.response` (see below).

If it is another type, it is converted into a string by `str()` and encoded
with `dialog.response.encoding`.


Dialog object attributes
========================
A functions or a class method that serves a request takes a single argument
representing the request / response dialog.

By convention, this _dialog object_ it is called `dialog` in functions and
(obviously) `self` in class methods. In this documentation page, we will use
`dialog`.

It has two main attributes:

- `request` : holds the information sent by the user agent
- `response` : used to send back information (other than the response body) to
  the user agent

`dialog.request`
----------------
The attributes of _dialog.request_ are :

`dialog.request.cookies`

> The cookies sent by the user agent. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html).

`dialog.request.encoding`

> The encoding used by the user agent to encode request data. If one of the
> request headers defines a value for "charset", this value is used ;
> otherwise, it is set to "iso-8859-1".

`dialog.request.headers`

> The http request headers sent by the user agent. Instance of
> [email.message.Message](https://docs.python.org/3/library/email.message.html).

`dialog.request.method`

> The request method ("GET", "POST", etc).

`dialog.request.url`

> The requested url (without the query string).

If the request is sent with the GET method, or the POST method with
enctype or content-type set to "application/x-www-form-urlencoded" or
"multipart/..." :

`dialog.request.fields`

> A dictionary for key/values received either in the query string, or in the
> request body for POST requests, or in named arguments in _smart urls_ (see
> above). Keys and values are strings, not bytes.
>
> For file uploads, the value associated with the key has the attributes
> `filename`, and `file`, a file-like object open for reading. Its `read()`
> method returns bytes.

For requests sent with other methods or content-type (eg Ajax requests with
JSON content) :

`dialog.request.json()`

> Function with no argument that returns a dictionary built as the parsing of
> the request body.

`dialog.request.raw`

> Request body as bytes.

`dialog.response`
-----------------
The attributes that can be set to `self.response` are:

`dialog.response.headers`

> The HTTP response headers. Instance of
> [email.message.Message](https://docs.python.org/3/library/email.message.html).
> To set the content type of the response, you can use the method
> `set_type()`:
>
>     dialog.response.headers.set_type("text/plain")

`dialog.response.cookie`

> Used to set cookies to send to the user agent with the response. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html)

`dialog.response.encoding`

> Unicode encoding to use to convert the string returned by the function into
> a bytestring. Defaults to "utf-8".

other attributes of `dialog`
----------------------------
`dialog.root`

> Path of document root in the server file system. Set to the value of
> `application.root`.

`dialog.environ`

> The WSGI environment variables.

`dialog.error`

> Used to return an HTTP error code, eg
>
>  `return dialog.error(404)`.

`dialog.redirection`

> Used to perform a temporary redirection (302) to a specified URL, eg
>
> `return dialog.redirection(url)`.

`dialog.template(filename, **kw)`

> If the templating engine [patrom](https://github.com/PierreQuentel/patrom)
> is installed, renders the template file at the location
> __templates/filename__ with the key/values in `kw`.
