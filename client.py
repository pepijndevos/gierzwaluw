import requests
import cherrypy
from urllib.parse import urljoin
from cgi import parse_header

class Client(object):

    def __init__(self, base):
        self.session = requests.Session()
        self.base = base
    
    def poll(self):
        res = self.session.head(urljoin(self.base, '/download'))
        cd = res.headers.get('Content-Disposition', '')
        _, params = parse_header(cd)
        return params.get('filename')

    def save(self, filename):
        with open(filename, 'wb') as handle:
            response = self.session.get(urljoin(self.base, '/download'), stream=True)
            response.raise_for_status()
            lenght = int(response.headers['content-length'])
            written = 0

            for block in response.iter_content(1024):
                written += len(block)
                cherrypy.engine.publish('progress', written / lenght) 
                if not block:
                    break
                handle.write(block)
