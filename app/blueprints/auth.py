from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from app.forms.auth import LoginForm
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('events.list_events'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user is not None and user.check_password(form.password.data):
            if user.is_locked:  # US-06-AC4 / BR17
                flash('Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên', 'danger')
            else:
                login_user(user)
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('events.list_events'))
        else:
            # US-06-AC2: chỉ báo lỗi chung, không tiết lộ email tồn tại hay không
            flash('Email hoặc mật khẩu không đúng', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()  # US-06-AC6: hủy phiên
    flash('Bạn đã đăng xuất', 'info')
    return redirect(url_for('auth.login'))
