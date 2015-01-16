import requests
from urllib.parse import urljoin
from cgi import parse_header
from PySide import QtCore

class Client(QtCore.QObject):

    progress = QtCore.Signal(float)

    def __init__(self, base):
        QtCore.QObject.__init__(self)
        self.session = requests.Session()
        self.base = base
    
    def poll(self):
        try:
            res = self.session.head(urljoin(self.base, '/download'), timeout=5)
            cd = res.headers.get('Content-Disposition', '')
            _, params = parse_header(cd)
            return params.get('filename')
        except requests.exceptions.RequestException:
            return None

    def save(self, filename):
        handle = open(filename, 'wb')

        response = self.session.get(urljoin(self.base, '/download'), stream=True)
        response.raise_for_status()
        lenght = int(response.headers['content-length'])
        self.written = 0

        timer = QtCore.QTimer(self)
        def download():
            block = response.raw.read(1024)
            self.written += len(block)
            self.progress.emit(self.written / lenght * 100) 
            if not block:
                timer.stop()
                handle.close()
                return
            handle.write(block)
        timer.timeout.connect(download)
        timer.start()
