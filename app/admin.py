from flask import redirect, url_for, request
from flask_admin.contrib import sqla
from flask_login import current_user
from werkzeug.urls import url_parse

class RLModelView(sqla.ModelView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.static_folder = 'static'

    def is_accessible(self):
        return current_user.is_authenticated and \
            current_user.username == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        next = url_parse(request.url).path
        return redirect(url_for('login', next=next))
