# bihan
bihan (small, in breton) is a minimalist web framework.

Installation
------------
```pip install bihan```

Hello World
-----------
Create a script (eg __home.py__) with

```python
def index(dialog):
    return 'Hello World'
```

and another script, __wsgi.py__

```python
from bihan import application
import home

application.run(scripts=home)
```

This starts a built-in web server on port 8000. Enter 
_http://localhost:8000/index_ in the browser address bar, it show the
"Hello World" message