# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
------------
```pip install bihan```

Hello World
-----------
Create a module (eg __home.py__) with

```python
def index(dialog):
    return 'Hello World'
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
---------------
By default, bihan uses function names as urls : in the modules passed in the
argument _modules_ of `application.run()`, all the callables whose name 
doesn't start with an underscore are accessible by their name.

For instance, the function `index()` in module __home__ is mapped to the url
_/index_.
