
import os
import datetime
import re
import csv
import json
import locale
import urllib.parse
import functools
import hashlib

from scripts import utils

def requires_level(role):

    def requires(f):
        
        @functools.wraps(f)
        def func(dialog):
            user_role = utils.role(dialog)
            if role == "manager" and user_role in ["manager", "admin"]:
                return f(dialog)
            elif role == "admin" and user_role == "admin":
                return f(dialog)
            return dialog.template("info.html",
                title="Permission denied",
                message="Permission denied {} {}".format(role, user_role))

        return func

    return requires
    
data_dir = utils.data_dir

class add_user:

    @requires_level("admin")
    def post(self):
        """Add a new user in the database."""
        mail = self.request.fields['mail']
        role = self.request.fields['role']
        password = utils.gen_password()
        salt = utils.gen_salt()
        pw = salt+password
        m = hashlib.sha1(pw.encode("utf-8")).hexdigest()
        
        users = utils.get_users()
        for user in users:
            if user["mail"] == mail:
                return self.template("info.html",
                    title="error",
                    message = "This mail address is already in the base")
    
        users.append({"mail": mail, "salt": salt, "pw": m, "role": role})
    
        with open(utils.users_store, "w", encoding="utf-8") as out:
            json.dump(users, out, indent=4)
        
        return self.template("user_added.html",
            title="",
            mail=mail,
            role=role,
            password=password
        )   
    

class authent:
    
    def post(self):
        mail = self.request.fields['mail']
        password = self.request.fields['password']
        users = utils.get_users()
        for user in users:
            if user["mail"] == mail:
                pw = user["salt"]+password
                h = hashlib.sha1(pw.encode("utf-8")).hexdigest()
                if h == user["pw"]:
                    self.response.cookies["user"] = mail
                    self.response.cookies["user"]["expires"] = 10*24*3600
                    return self.redirection("/")
        return self.template('info.html', 
            title="Permission refused",
            message="Permission refused")

    
class create_users_db:
    
    def get(self):
        """Create users database."""
        if utils.has_users():
            return self.template("info.html",
                title="Error",
                message="Database already exists"
            )
        mail = self.request.fields['mail']
        password = self.request.fields['password']
        salt = utils.gen_salt()
        pw = salt+password
        
        m = hashlib.sha1(pw.encode("utf-8")).hexdigest()
        
        with open(utils.users_store, "w", encoding="utf-8") as out:
            json.dump([{"mail": mail, "salt": salt, "pw": m, "role": "admin"}], 
                out, indent=4)
        
        return self.redirection("/")

class del_user:

    @requires_level("admin")
    def post(self):
        """Delete a user from the database."""
        mail = self.request.fields["mail"]
        users = utils.get_users()
        for i, user in enumerate(users):
            if user["mail"] == mail:
                del users[i]
                with open(utils.users_store, "w", encoding="utf-8") as out:
                    json.dump(users, out, indent=4)
                return self.redirection("/list_users")
        return self.template("info.html",
            title="error",
            message="Can't delete user, unknown address"
        )
            

class logout:

    def get(self):
        """Log out."""
        self.response.cookies["user"] = ""
        self.response.cookies["user"]["expires"] = 0
        return self.redirection("/")


class list_users:

    @requires_level("admin")
    def get(self):
        """List users."""
        users = utils.get_users()
        return self.template("list_users.html",
            title="Users list",
            users=utils.get_users()
        )


class reset_pw:

    @requires_level("manager")
    def post(self):
        """Reset user password."""
        mail = self.request.fields["mail"]
        password = self.request.fields["password"]
    
        salt = utils.gen_salt()
        pw = salt+password
        m = hashlib.sha1(pw.encode("utf-8")).hexdigest()
        
        users = utils.get_users()
        for user in users:
            if user["mail"] == mail:
                user["salt"] = salt
                user["pw"] = m
    
                with open(utils.users_store, "w", encoding="utf-8") as out:
                    json.dump(users, out, indent=4) 
        
                return self.template("info.html",
                    title="",
                    message = "Password changed"
                )   
    
        return self.template("info.html",
            title="Error",
            message="Unknown user: {}".format(mail)
            )