from flask import redirect
from flask import request
from flask import url_for
from flask.ext import login
from flask.ext.admin import AdminIndexView
from flask.ext.admin import expose
from flask.ext.admin import helpers
from flask.ext.admin.contrib.sqla import ModelView
from pdf2img.web import db
from pdf2img.web.models import User
from werkzeug.security import check_password_hash
from wtforms import fields
from wtforms import form
from wtforms import validators


class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()


class AdminLoginView(AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(AdminLoginView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated():
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(AdminLoginView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


class AuthModelView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated()
