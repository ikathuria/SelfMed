import sys
path = '/home/ikathuria/selfmed'
if path not in sys.path:
   sys.path.insert(0, path)

from index import app as application
