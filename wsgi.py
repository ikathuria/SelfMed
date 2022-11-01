import sys
project_home = '/home/ikathuria/selfmed'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from index import app as application
