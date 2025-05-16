# Server (server.py)
from xmlrpc.server import SimpleXMLRPCServer

def set_filename(filename):
    print("Server: set filename = {0:s}".format(filename))
    return filename 

server = SimpleXMLRPCServer(("localhost", 8000))
server.register_function(set_filename, 'set_filename')

print("Listening on port 8000...")
server.serve_forever()
