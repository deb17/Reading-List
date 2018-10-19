from flask_wtf import FlaskForm
from flask_wtf.recaptcha import RecaptchaField
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     IntegerField, SelectField, TextAreaField)
from wtforms.validators import (ValidationError, DataRequired, Email, EqualTo,
                                Optional, Length)
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField('Captcha')
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(),
                                                     Length(8)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')

msg = 'Will take some time to process.\nTitle should be accurate.'

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()],
                        render_kw={'maxlength': '150'})
    author = StringField('Author', render_kw={'maxlength': '150'})
    edition = IntegerField('Edition', validators=[Optional()])
    format = SelectField('Format', choices=[('1', 'Print'), ('2', 'Online')])
    about = TextAreaField('About', render_kw={'rows': '4', 'maxlength': '500'})
    private = BooleanField('Private', default='checked')
    cover = BooleanField('Open Library cover image',
                         render_kw={'title': msg})
    submit1 = SubmitField('Save')
    submit2 = SubmitField('Update')
