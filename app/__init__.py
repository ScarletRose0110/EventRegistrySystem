from flask import Flask, render_template
from app.config import Config
from app.extensions import csrf, db, migrate, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.models import User  # noqa: F401 (đăng ký model cho db/migrate)

    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        if user is not None and user.is_locked:  # BR17: khóa là mất phiên ngay
            return None
        return user

    from app.blueprints.auth import auth_bp
    from app.blueprints.events import events_bp
    from app.blueprints.registrations import reg_bp
    from app.blueprints.manage import manage_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(reg_bp)
    app.register_blueprint(manage_bp)

    @app.after_request
    def no_cache_html(response):
        if response.mimetype == 'text/html':
            response.headers['Cache-Control'] = 'no-store, max-age=0'
        return response

    @app.errorhandler(403)
    def forbidden(e):
        message = getattr(e, 'description', None) or 'Bạn không có quyền truy cập chức năng này'
        return render_template('errors/403.html', message=message), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    return app
