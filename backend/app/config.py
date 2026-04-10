import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret")
    TESTING = False


class TestingConfig(Config):
    TESTING = True
