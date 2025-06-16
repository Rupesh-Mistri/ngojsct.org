import os
import sys


# sys.path.insert(0, os.path.dirname(__file__))


# def application(environ, start_response):
#     start_response('200 OK', [('Content-Type', 'text/plain')])
#     message = 'It works!\n'
#     version = 'Python %s\n' % sys.version.split()[0]
#     response = '\n'.join([message, version])
#     return [response.encode()]

# Add the path to your Django project directory to the sys.path
#sys.path.insert(0, '/home/username/path/to/your/django/project')

# Set the Django settings module environment variable
os.environ['DJANGO_SETTINGS_MODULE'] = 'ngojsct.settings'


from ngojsct.wsgi import application