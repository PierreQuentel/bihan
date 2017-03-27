import json
import mimetypes

from scripts.utils import format_response

def index(dialog):
    return 'hello'

def show_argument(dialog):
    return json.dumps(dialog.request.fields)
    
def test_smart_url(dialog):
    return dialog.request.fields['x']
test_smart_url.url = 'test_smart_url/<x>'

def upload_form(dialog):
    return dialog.template("upload.html")

def upload(dialog):
    fobj = dialog.request.fields['info']
    mtype, encoding = mimetypes.guess_type(fobj.filename)
    dialog.response.headers.set_type(mtype)
    return fobj.file.read()

def smart_func(dialog):
    fields = dialog.request.fields
    return fields['x'], fields['y']
smart_func.url = '/very_smart/<x>/url/<y>'

def redirection(dialog):
    return dialog.redirection('/foo')

def error403(dialog):
    return dialog.error(403, 'Access refused')
    