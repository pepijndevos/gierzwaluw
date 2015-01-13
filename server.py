import os
import queue
import requests
import socket
import cherrypy
from cherrypy.lib.static import serve_file
from cherrypy.process import plugins
from zeroconf import ServiceInfo, Zeroconf

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

# Announce on web
announce_url = "http://wishfulcoding.nl/announce.php"
session = requests.Session()
def announce_web():
    cherrypy.engine.log('Announcing %s at %s' % (hostname, privip))
    try:
        session.get(announce_url,
                params={"ip": privip, "hostname": hostname},
                timeout=5)
    except requests.exceptions.RequestException:
        cherrypy.engine.log('Failed to announce')

# Announce on Zeroconf
sinfo = ServiceInfo("_http._tcp.local.",
                   hostname+".gierzwaluw._http._tcp.local.",
                   socket.inet_aton(privip), 7557, 0, 0,
                   {})

def announce_zeroconf():
    zeroconf = Zeroconf()
    zeroconf.register_service(sinfo)
    cherrypy.engine.log('Announcing mDNS')

class FileServer(object):

    def __init__(self):
        self.file_dl = None
        cherrypy.engine.subscribe('file-dl', self.set_file_dl)

    def set_file_dl(self, f):
        self.file_dl = f

    @cherrypy.expose
    def index(self):
        return serve_file(abs_dir + "/static/index.html")

    @cherrypy.expose
    def upload(self, file_ul):
        if any(cherrypy.engine.publish('file-ul', file_ul)):
            raise cherrypy.HTTPRedirect("/")
        else:
            raise cherrypy.HTTPError(403, "File not accepted")

    @cherrypy.expose
    def download(self):
        if not self.file_dl:
            raise cherrypy.HTTPError(404, "No file available for download")
        else:
            return serve_file(self.file_dl, "application/x-download", "attachment")

def start(block=True):
    announce_web()
    plugins.BackgroundTask(60, announce_web).start()

    announce_zeroconf()

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': 7557,
        'engine.autoreload.on': False,
        #'environment': 'embedded',
    })

    cherrypy.tree.mount(FileServer())
    cherrypy.engine.start()
    if block:
        cherrypy.engine.block()

