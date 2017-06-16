from scripts import utils

class index:

    def get(self):
        if not utils.has_users():
            return self.template("init_users.html",
                title="Create users database"
            )
    
        return self.template("index.html", 
            title="bihan demo application",
            role=utils.role(self)
        )


class other:
    
    def get(self):
        return "ok"

class r2other:
    
    def get(self):
        return self.routes