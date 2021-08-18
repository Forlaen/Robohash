#!/usr/bin/env python
# This Python file uses the following encoding: utf-8

# Find details about this project at https://github.com/e1ven/robohash

from __future__ import unicode_literals
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import socket
import os
import hashlib
import random
from robohash import Robohash
import re
import io
import base64

# Import urllib stuff that works in both Py2 and Py3
try:
    import urllib.request
    import urllib.parse
    urlopen = urllib.request.urlopen
    urlencode = urllib.parse.urlencode
except ImportError:
    import urllib2
    import urllib
    urlopen = urllib2.urlopen
    urlencode = urllib.urlencode

from tornado.options import define, options
import io

define("port", default=80, help="run on the given port", type=int)



class MainHandler(tornado.web.RequestHandler):
    def get(self):
        ip = self.request.remote_ip

        self.write(self.render_string('templates/root.html',ip=ip))

class ImgHandler(tornado.web.RequestHandler):
    """
    The ImageHandler is our tornado class for creating a robot.
    called as Robohash.org/$1, where $1 becomes the seed string for the Robohash obj
    """
    def get(self,string=None):


        # Set default values
        sizex = 300
        sizey = 300
        format = "png"

        # Normally, we pass in arguments with standard HTTP GET variables, such as
        # ?set=any and &size=100x100
        #
        # Some sites don't like this though.. They cache it weirdly, or they just don't allow GET queries.
        # Rather than trying to fix the intercows, we can support this with directories... <grumble>
        # We'll translate /abc.png/s_100x100/set_any to be /abc.png?set=any&s=100x100
        # We're using underscore as a replacement for = and / as a replacement for [&?]

        args = self.request.arguments.copy()

        for k in list(args.keys()):
            v = args[k]
            if type(v) is list:
                if len(v) > 0:
                    args[k] = args[k][0]
                else:
                    args[k] = ""

        # Detect if they're using the above slash-separated parameters..
        # If they are, then remove those parameters from the query string.
        # If not, don't remove anything.
        split = string.split('/')
        if len(split) > 1:
            for st in split:
                b = st.split('_')
                if len(b) == 2:
                    if b[0] in ['size']:
                        args[b[0]] = b[1]
                        string = re.sub("/" + st,'',string)

        # Ensure we have something to hash!
        if string is None:
                string = self.request.remote_ip


        # Detect if the user has passed in a flag to ignore extensions.
        # Pass this along to to Robohash obj later on.

        ignoreext = args.get('ignoreext','false').lower() == 'true'

        # Split the size variable in to sizex and sizey
        if "size" in args:
                sizex,sizey = args['size'].split("x")
                sizex = int(sizex)
                sizey = int(sizey)
                if sizex > 4096 or sizex < 0:
                    sizex = 300
                if sizey > 4096 or sizey < 0:
                    sizey = 300

        # Create our Robohashing object
        r = Robohash(string,hashcount=16)

        # We're going to be returning the image directly, so tell the browser to expect a binary.
        self.set_header("Content-Type", "image/" + format)
        self.set_header("Cache-Control", "public,max-age=31536000")

        # Build our Robot.
        r.assemble(roboset="apes",format=format,sizex=sizex,sizey=sizey)

        # Print the Robot to the handler, as a file-like obj
        if r.format != 'datauri':
            r.img.save(self,format=r.format)
        else:
            # Or, if requested, base64 encode first.
            fakefile = io.BytesIO()
            r.img.save(fakefile,format='PNG')
            fakefile.seek(0)
            b64ver = base64.b64encode(fakefile.read())
            b64ver = b64ver.decode('utf-8')
            self.write("data:image/png;base64," + str(b64ver))

def main():
        tornado.options.parse_command_line()
        # timeout in seconds
        timeout = 10
        socket.setdefaulttimeout(timeout)

        settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
        "cookie_secret": "9b90a85cfe46cad5ec136ee44a3fa332",
        "login_url": "/login",
        "xsrf_cookies": True,
        }

        application = tornado.web.Application([
                (r'/(crossdomain\.xml)', tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__),
                "static/")}),
                (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(os.path.dirname(__file__),
                "static/")}),
                (r"/", MainHandler),
                (r"/(.*)", ImgHandler),
        ], **settings)

        http_server = tornado.httpserver.HTTPServer(application,xheaders=True)
        http_server.listen(options.port)

        print("The Oven is warmed up - Time to make some Robots! Listening on port: " + str(options.port))
        tornado.ioloop.IOLoop.instance().start()
if __name__ == "__main__":
        main()