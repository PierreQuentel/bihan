
from scripts import utils
def index(dialog):
    if not utils.has_users():
        return dialog.template("init_users.html",
            title="Create users database"
        )

    return dialog.template("index.html", 
        title="bihan demo application",
        role=utils.role(dialog)
    )

index.url = "/"