import os
import queue
import requests
import socket
from zeroconf import ServiceInfo, Zeroconf
from bottle import Bottle, run, static_file, request, redirect, abort
from PySide import QtCore

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

class WebAnnouncer(QtCore.QThread):

    def announce(self):
        try:
            session.get(announce_url,
                    params={"ip": privip, "hostname": hostname},
                    timeout=5)
        except requests.exceptions.RequestException:
            pass
    
    def run(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.announce)
        timer.start(1000*60*4)

        self.exec_()


# Announce on Zeroconf
sinfo = ServiceInfo("_http._tcp.local.",
                   hostname+".gierzwaluw._http._tcp.local.",
                   socket.inet_aton(privip), 7557, 0, 0,
                   {})

def announce_zeroconf():
    zeroconf = Zeroconf()
    zeroconf.register_service(sinfo)

class FileServer(QtCore.QObject):

    uploaded = QtCore.Signal(object)

    def __init__(self):
        QtCore.QObject.__init__(self)
        self.file_dl = None
        self.app = Bottle()
        self.app.get('/', callback=self.index)
        self.app.post('/upload', callback=self.upload)
        self.app.get('/download', callback=self.download)

    def start(self):
        self.w = WebAnnouncer()
        self.w.start()
        announce_zeroconf()
        self.app.run(host='0.0.0.0', port=7557)

    @QtCore.Slot(str)
    def set_download(self, f):
        self.file_dl = os.path.abspath(f)

    def index(self):
        return static_file("/static/index.html", root=abs_dir)

    def upload(self):
        self.uploaded.emit(request.files.get('upload'))
        redirect("/")

    def download(self):
        if not self.file_dl:
            abort(404, "No file available for download")
        else:
            return static_file(self.file_dl, root='/', download=os.path.basename(self.file_dl))

