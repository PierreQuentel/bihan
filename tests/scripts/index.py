import json
import mimetypes

from scripts.utils import format_response

class index:

    def get(self):
        return 'hello'

class show_argument:
    
    def get(self):
        return json.dumps(self.request.fields)
    
    post = get

class test_smart_url:
    
    def get(self):
        return self.request.fields['x']
    get.url = 'test_smart_url/<x>'

class upload_form:
    
    def get(self):
        return self.template("upload.html")

class upload:
    
    def post(self):
        fobj = self.request.fields['info']
        mtype, encoding = mimetypes.guess_type(fobj.filename)
        self.response.headers.set_type(mtype)
        return fobj.file.read()

class smart_func:
    
    def get(self):
        fields = self.request.fields
        return fields['x'], fields['y']
    get.url = '/very_smart/<x>/url/<y>'

class redirection:
    
    def get(self):
        return self.redirection('/foo')

class error403:
    
    def get(self):
        return self.error(403)

class trailing_slash:
    
    def get(self):
        return 'trailing slash'
    get.url = '/trailing_slash/'