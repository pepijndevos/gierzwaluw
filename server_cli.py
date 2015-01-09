import os
import sys
import shutil
import cherrypy
from cherrypy.process import plugins

from server import FileServer

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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", help="Directory to upload files")
    parser.add_argument("--download", help="File to offer for download")
    args = parser.parse_args()

    CLIPlugin(cherrypy.engine, file_dl=args.download, file_ul=args.upload).subscribe()
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                            'server.socket_port': 7557})
    cherrypy.quickstart(FileServer())
