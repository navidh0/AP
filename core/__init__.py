import environ

env = environ.Env()
environ.Env.read_env('.env')

if env("PROD", cast=bool):
    from .settings.prod import *
else:
    from .settings.dev import *
