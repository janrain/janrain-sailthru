"""Entry point for beanstalk to load the flask application."""
# must be named application for beanstalk to find it automatically
from janrain_sailthru import app as application
