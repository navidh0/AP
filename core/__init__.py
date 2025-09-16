import environ

env = environ.Env()
environ.Env.read_env('.env')

if env("PROD", cast=bool):
    from .prod import *
else:
    from .dev import *
