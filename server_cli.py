import os
import sys
import shutil
import cherrypy
import socket
from cherrypy.process import plugins
from zeroconf import ServiceBrowser, Zeroconf

from server import start
from client import Client

class CLIListener(object):

    def remove_service(self, zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        print(name)
        info = zeroconf.get_service_info(type, name)
        if info:
            addr = "http://%s:%d" % (socket.inet_ntoa(info.address), info.port)
            c = Client(addr)
            f = c.poll()
            if f:
                print("Serving", f)
                dl = input("Enter download location [ignore]: ")
            else:
                print("Serving nothing")
                dl = None

            if dl:
                c.save(dl)
        else:
            print("No info")


class CLIPlugin(plugins.SimplePlugin):

    def __init__(self, bus, file_dl=None, file_ul=None):
        plugins.SimplePlugin.__init__(self, bus)
        self.file_dl = os.path.abspath(file_dl) if file_dl else None
        self.file_ul = file_ul

    def start(self):
        self.bus.log('Starting up CLI')
        self.bus.subscribe("file-ul", self.save_file)
        self.bus.publish('file-dl', self.file_dl)

    def stop(self):
        self.bus.log('Stopping CLI')
        self.bus.unsubscribe("file-ul", self.save_file)

    def save_file(self, file_ul):
        if self.file_ul:
            self.bus.log('Saving %s' % file_ul.filename)
            with open(os.path.join(self.file_ul, file_ul.filename), 'wb') as outfile:
                shutil.copyfileobj(file_ul.file, outfile)
            return True
        else:
            return False

def progress(ratio, width=50):
    bar = ("#" * int(ratio * width)).ljust(width)
    sys.stdout.write("\r[%s] %.2f%%" % (bar, ratio*100))
    if ratio >= 1:
        sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", help="Directory to upload files")
    parser.add_argument("--download", help="File to offer for download")
    parser.add_argument("--browse", help="Browse peers", action="store_true")
    args = parser.parse_args()
    
    if args.browse:
        cherrypy.engine.subscribe("progress", progress)
        zeroconf = Zeroconf()
        listener = CLIListener()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        browser.join()
    else:
        CLIPlugin(cherrypy.engine, file_dl=args.download, file_ul=args.upload).subscribe()
        start()
