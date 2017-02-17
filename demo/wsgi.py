from bihan import application

with application.register:
    from scripts import views, users

application.run(port=8080)
