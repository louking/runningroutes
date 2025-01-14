from os import environ

__version__ = environ['APP_VER']    # from .env
__docversion__ = __version__
# uncomment for development
# __docversion__ = 'latest'