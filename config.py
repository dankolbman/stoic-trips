import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    HOST = '0.0.0.0'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SSL_DISABLE = os.environ.get('SSL_DISABLE', False)
    JWT_AUTH_USERNAME_KEY = 'username'
    JWT_AUTH_PASSWORD_KEY = 'password'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI',
                                             'postgres://postgres:5432/stoic')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SSL_DISABLE = True
    SQLALCHEMY_DATABASE_URI = 'postgres:///stoic_dev'


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = 'secret'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgres:///stoic_test'


class ProductionConfig(Config):

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'unix': UnixConfig,

    'default': DevelopmentConfig
}
