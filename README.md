# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
============
```pip install bihan```

Hello World
===========

```python
from bihan import application

def hello(dialog):
    return "Hello World"

application.run()
```

This starts a built-in web server on port 8000. Enter 
_http://localhost:8000/hello_ in the browser address bar, it shows the
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

Special case : if a function is called `index`, it is also mapped by default
to the url _/_.

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
show.url = "/show/<num>"
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

`application.root`

> a path in the server file system. It is available in
> scripts as `dialog.root`. Defaults to the application directory.

`application.run(host="localhost", port=8000, debug=False)`

> starts the application on the development server, on the specified _host_
> and _port_.
>
> _debug_ sets the debug mode. If `True`, the program periodically checks if
> a change has been made to the modules used by the application (registered or
> not) and located in the application directory, including the main module. If
> the source code of one of these modules is changed, the application is 
> restarted.
>
> If an exception happens when reloading the registered modules, the server
> doesn't crash, but the exception is stored and will be shown as the result
> of the next request.


`application.static`

> a dictionary mapping paths of the form _/path_ to directories in the server
> file system. It it used to serve static files (HTML pages, images,
> Javascript programs, etc.). By default, the dictionary maps _/static_ to the
> folder __static__ in the server directory.


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

`dialog.request.url`

> The requested url (without the query string).

`dialog.request.headers`

> The http request headers sent by the user agent. Instance of 
> [email.message.Message](https://docs.python.org/3/library/email.message.html).

`dialog.request.encoding`

> The encoding used in the request.

`dialog.request.cookies`

> The cookies sent by the user agent. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html).
>

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

For requests sent with other methods or content-type :

`dialog.request.raw`

> Request body as bytes for requests of other types (eg Ajax requests with
> JSON content).
  
`dialog.request.json()`

> Function with no argument that returns a dictionary built as the parsing of
> the request body.

`dialog.response`
-----------------
The attributes that can be set to `dialog.response` are:

`dialog.response.headers`

> The HTTP response headers. Instance of
> [email.message.Message](https://docs.python.org/3/library/email.message.html)

`dialog.response.cookie`

> Used to set cookies to send to the user agent with the response. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html)

`dialog.response.encoding`

> Unicode encoding to use to convert the string returned by script functions
> into a bytestring. Defaults to "utf-8".

other attributes of `dialog`
----------------------------
`dialog.root`

> Path of document root in the server file system. Set to the value of
> `application.root`.

`dialog.environ`

> WSGI environment variables.

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
