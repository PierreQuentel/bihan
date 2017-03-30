# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
============
```pip install bihan```

Hello World
===========

```python
from bihan import application

class Hello:

    def get(self):
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
HTTP requests are sent with a method (GET, POST, PUT, etc) to a url. bihan
maps urls to the classes defined in the _registered modules_, and uses the
methods defined in these classes to serve the request.

The _registered modules_ are:

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

class Hello:

    def get(self):
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
__expose__ = False
```

Mapping a url to a class in a registered module
-----------------------------------------------
By default, bihan uses class names as urls : all the classes defined in
the module (not those imported from another module) are accessible by their
name.

For instance, if a registered module defines this class:

```python
class User:

    def get(self):
        return "Here is information about a user"

    def post(self):
        return "Replacing or creating a user"
    
    def delete(self):
        return "Deleting a user"
```

then its method `get()` serves GET requests to the _/user_ (urls are
case-insensivite), its method `post()` serves POST request to this url, etc.

If the module defines a variable `__prefix__`, it is prepended to the url for
all the classes in the module :

```python
__prefix__ = "library"

class Users:
    ...
```
will map the url _library/users_ to the class `Users`

Special case : if a class is called `Index`, it is also mapped by default to
the url _/_.

If the class serves other urls than the class name (including _smart urls_,
see below), set its attribute _url_ (a single url) or _urls_ (a list of urls):

```python
class User:

    url = '/user/<id>'
    
    def get(self):
        ...
```

or

```python
class User:

    urls = ['/user', '/user/<id>']
    
    def post(self):
        ...
```

The url(s) can also be specified at the method level:

```python
class User:

    def get(self):
        # serves GET requests on url "/users"
    
    def post(self):
        # serves POST requests on urls "/users" and "/users/<id>"
    post.urls = ["/users", "/users/<id>"]
```

Smart URLs
----------
If the url includes parts of the form `<x>`, the value matching `x` will be
available as one the request fields.

For instance :

```python
class Show:

    def get(self):
        ...
    get.url = "/show/<num>"
```

The method `Show.get()` is called for urls like _/show/76_, and the value (76)
is available in the function body as `self.request.fields["num"]` (see the
attributes of `self` below).

Mapping control
---------------
bihan makes sure that a url matches only one method in a _registered module_.
Otherwise it raises a `RoutingError`, with a message giving the scripts and
methods that define the same url.

Application attributes and methods
==================================

`application.root`

> A path in the server file system. It is available in scripts as
> `self.root`. Defaults to the application directory.

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

The return value of the method is the body of the response sent to the
user agent. If it is not a string, it is converted by `str()`.

Instance attributes
===================

A method that serves a request takes a single argument, `self`. It has two main
attributes:

- `request` : holds the information sent by the user agent
- `response` : used to send back information (other than the response body) to
  the user agent

`self.request`
----------------
The attributes of _self.request_ are :

`self.request.cookies`

> The cookies sent by the user agent. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html).
>

`self.request.encoding`

> The encoding used by the user agent to encode request data. If one of the
> request headers defines a value for "charset", this value is used ;
> otherwise, it is set to "iso-8859-1".

`self.request.headers`

> The http request headers sent by the user agent. Instance of 
> [email.message.Message](https://docs.python.org/3/library/email.message.html).

`self.request.method`

> The request method ("GET", "POST", etc).

`self.request.url`

> The requested url (without the query string).

If the request is sent with the GET method, or the POST method with
enctype or content-type set to "application/x-www-form-urlencoded" or 
"multipart/..." :

`self.request.fields`

> A dictionary for key/values received either in the query string, or in the
> request body for POST requests, or in named arguments in _smart urls_ (see 
> above). Keys and values are strings, not bytes.
>
> For file uploads, the value associated with the key has the attributes
> `filename`, and `file`, a file-like object open for reading. Its `read()`
> method returns bytes.

For requests sent with other methods or content-type (eg Ajax requests with
JSON content) :

`self.request.json()`

> Function with no argument that returns a dictionary built as the parsing of
> the request body.

`self.request.raw`

> Request body as bytes.
  
`self.response`
-----------------
The attributes that can be set to `self.response` are:

`self.response.headers`

> The HTTP response headers. Instance of
> [email.message.Message](https://docs.python.org/3/library/email.message.html)

`self.response.cookie`

> Used to set cookies to send to the user agent with the response. Instance of
> [http.cookies.SimpleCookie](https://docs.python.org/3/library/http.cookies.html)

`self.response.encoding`

> Unicode encoding to use to convert the string returned by the function into
> a bytestring. Defaults to "utf-8".

other attributes of `self`
--------------------------
`self.root`

> Path of document root in the server file system. Set to the value of
> `application.root`.

`self.environ`

> The WSGI environment variables.

`self.error`

> Used to return an HTTP error code, eg 
>
>  `return self.error(404)`.

`self.redirection`

> Used to perform a temporary redirection (302) to a specified URL, eg
>
> `return self.redirection(url)`.

`self.template(filename, **kw)`

> If the templating engine [patrom](https://github.com/PierreQuentel/patrom)
> is installed, renders the template file at the location 
> __templates/filename__ with the key/values in `kw`.
