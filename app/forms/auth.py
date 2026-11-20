from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email'),  # US-06-AC3
        Email(message='Email không đúng định dạng'),
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu'),
    ])
    submit = SubmitField('Đăng nhập')
