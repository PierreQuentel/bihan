__expose__ = False

import os
import json
import random
import string

data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

users_store = os.path.join(data_dir, "users.json")

def gen_password():
    # generate a random password
    return ''.join(random.choice(string.ascii_letters+string.digits*3) 
        for _ in range(8))

def gen_salt():
    # generate a random "salt"
    return ''.join(random.choice(string.ascii_letters) for _ in range(32))

def get_users():
    store = os.path.join(data_dir, "users.json")
    if not os.path.exists(store):
        return []
    with open(store, encoding="utf-8") as fobj:
        return json.load(fobj)

def has_users():
    return os.path.exists(os.path.join(data_dir, 'users.json'))

def role(dialog):
    # return the user level : visitor, editor, admin
    if 'user' in dialog.request.cookies:
        mail = dialog.request.cookies['user'].value
        users = get_users()
        for user in users:
            if user["mail"] == mail:
                return user["role"]
    return 'visitor'

    