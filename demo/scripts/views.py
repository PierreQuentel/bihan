from scripts import utils

class Index:

    def get(self):
        if not utils.has_users():
            return self.template("init_users.html",
                title="Create users database"
            )
    
        return self.template("index.html", 
            title="bihan demo application",
            role=utils.role(self)
        )

