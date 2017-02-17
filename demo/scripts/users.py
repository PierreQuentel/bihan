
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
        
        def func(dialog):
            user_role = utils.role(dialog)
            if role == "manager" and user_role in ["manager", "admin"]:
                return f(dialog)
            elif role == "admin" and user_role == "admin":
                return f(dialog)
            return dialog.template("info.html",
                title="Permission denied",
                message="Permission denied {} {}".format(role, user_role))
        func.__name__ = f.__name__
        return func

    return requires
    
data_dir = utils.data_dir


@requires_level("admin")
def add_user(dialog):
    mail = dialog.request.fields['mail']
    role = dialog.request.fields['role']
    password = utils.gen_password()
    salt = utils.gen_salt()
    pw = salt+password
    m = hashlib.sha1(pw.encode("utf-8")).hexdigest()
    
    users = utils.get_users()
    for user in users:
        if user["mail"] == mail:
            return dialog.template("info.html",
                title="error",
                message = "This mail address is already in the base")

    users.append({"mail": mail, "salt": salt, "pw": m, "role": role})

    with open(utils.users_store, "w", encoding="utf-8") as out:
        json.dump(users, out, indent=4)
    
    return dialog.template("user_added.html",
        title="",
        mail = mail,
        role=role,
        password=password
    )   
    

def authent(dialog):
    mail = dialog.request.fields['mail']
    password = dialog.request.fields['password']
    users = utils.get_users()
    for user in users:
        if user["mail"] == mail:
            pw = user["salt"]+password
            h = hashlib.sha1(pw.encode("utf-8")).hexdigest()
            if h == user["pw"]:
                dialog.response.cookies["user"] = mail
                dialog.response.cookies["user"]["expires"] = 10*24*3600
                raise dialog.redirection("/")
    return render_template('authent_failed.html')

    
def create_users_db(dialog):
    if utils.has_users():
        return "la base existe déjà"
    mail = dialog.request.fields['mail']
    password = dialog.request.fields['password']
    salt = utils.gen_salt()
    pw = salt+password
    
    m = hashlib.sha1(pw.encode("utf-8")).hexdigest()
    
    with open(utils.users_store, "w", encoding="utf-8") as out:
        json.dump([{"mail": mail, "salt": salt, "pw": m, "role": "admin"}], 
            out, indent=4)
    
    raise dialog.redirection("/")

@requires_level("admin")
def del_user(dialog):
    mail = dialog.request.fields["mail"]
    users = utils.get_users()
    print(mail, users)
    for i, user in enumerate(users):
        if user["mail"] == mail:
            del users[i]
            with open(utils.users_store, "w", encoding="utf-8") as out:
                json.dump(users, out, indent=4)
            raise dialog.redirection("/list_users")
    return dialog.template("info.html",
        title="error",
        message="Can't delete user, unknown address"
    )
            

def logout(dialog):
    dialog.response.cookies["user"] = ""
    dialog.response.cookies["user"]["expires"] = 0
    raise dialog.redirection("/")


@requires_level("admin")
def list_users(dialog):
    users = utils.get_users()
    return dialog.template("list_users.html",
        title="Users list",
        users=utils.get_users()
    )


@requires_level("manager")
def reset_pw():
    mail = request.form["mail"]
    password = request.form["password"]

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
    
            return render_template("info.html",
                message = "Le mot de passe a été modifié"
            )   

    return render_template("info.html",
        message="pas d'utilisateur {}".format(mail)
        )