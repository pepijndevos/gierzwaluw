import os
import sys
import shutil
import socket
from zeroconf import ServiceBrowser, Zeroconf
from PySide import QtCore

from gierzwaluw.server import FileServer
from gierzwaluw.client import Client

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
                c.progress.connect(progress)
                c.save(dl)
        else:
            print("No info")


class Saver(QtCore.QObject):

    def __init__(self, dir=None):
        QtCore.QObject.__init__(self)
        self.dir = dir

    @QtCore.Slot(object)
    def save_file(self, upload):
        if self.dir:
            print('Saving %s' % upload.filename)
            upload.save(self.dir)

def progress(ratio, width=50):
    bar = ("#" * int(ratio * width)).ljust(width)
    sys.stdout.write("\r[%s] %.2f%%" % (bar, ratio*100))
    if ratio >= 1:
        sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == '__main__':
    import argparse

    QtCore.QCoreApplication(sys.argv) # for timer

    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", help="Directory to upload files")
    parser.add_argument("--download", help="File to offer for download")
    parser.add_argument("--browse", help="Browse peers", action="store_true")
    args = parser.parse_args()
    
    if args.browse:
        zeroconf = Zeroconf()
        listener = CLIListener()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        browser.join()
    else:
        saver = Saver(args.upload)
        server = FileServer()
        server.set_download(args.download)
        server.uploaded.connect(saver.save_file)
        server.start()
