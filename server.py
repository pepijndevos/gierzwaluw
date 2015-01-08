import os
import queue
import requests
import socket
import shutil
import cherrypy
from cherrypy.lib.static import serve_file
from cherrypy.process import plugins

import pdb

local_dir = os.path.dirname(__file__)
abs_dir = os.path.join(os.getcwd(), local_dir)

hostname = socket.gethostname()
# might be 127.0.0.1
privip = socket.gethostbyname(hostname)
# try to get private IP used for outbound traffic
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.4.4",53))
    privip = s.getsockname()[0]
except socket.error:
    pass
finally:
    s.close()

announce_url = "http://wishfulcoding.nl/announce.php"
session = requests.Session()
def announce():
    cherrypy.engine.log('Announcing %s at %s' % (hostname, privip))
    session.get(announce_url, params={"ip": privip, "hostname": hostname})

class FileServer(object):

    def __init__(self):
        self.file_dl = None
        cherrypy.engine.subscribe('file-dl', self.set_file_dl)
        announce()
        plugins.BackgroundTask(60, announce).start()

    def set_file_dl(self, f):
        self.file_dl = f

    @cherrypy.expose
    def index(self):
        return serve_file(abs_dir + "/static/index.html")

    @cherrypy.expose
    def upload(self, file_ul):
        cherrypy.engine.publish('file-ul', file_ul)
        raise cherrypy.HTTPRedirect("/")

    @cherrypy.expose
    def download(self):
        if not self.file_dl:
            raise cherrypy.HTTPError(404, "No file available for download")
        else:
            return serve_file(self.file_dl, "application/x-download", "attachment")


class CLIPlugin(plugins.SimplePlugin):

    def __init__(self, bus, file_dl=None, file_ul=None):
        plugins.SimplePlugin.__init__(self, bus)
        self.file_dl = os.path.abspath(file_dl)
        self.file_ul = file_ul

    def start(self):
        self.bus.log('Starting up CLI')
        self.bus.subscribe("file-ul", self.save_file)
        self.bus.publish('file-dl', self.file_dl)

    def stop(self):
        self.bus.log('Stopping CLI')
        self.bus.unsubscribe("file-ul", self.save_file)

    def save_file(self, file_ul):
        self.bus.log('Saving %s' % file_ul.filename)
        with open(os.path.join(self.file_ul, file_ul.filename), 'wb') as outfile:
            shutil.copyfileobj(file_ul.file, outfile)

if __name__ == '__main__':
    import sys
    CLIPlugin(cherrypy.engine, file_dl=sys.argv[1], file_ul=sys.argv[2]).subscribe()
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 7557})
    cherrypy.quickstart(FileServer())
