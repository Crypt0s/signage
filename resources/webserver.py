#!/usr/bin/python
import multiprocessing
import ctypes
import web
import shutil
import giflib
import sys
import pdb

class ForkedPdb(pdb.Pdb):
    """A Pdb subclass that may be used
    from a forked multiprocessing child

    """
    def interaction(self, *args, **kwargs):
        _stdin = sys.stdin
        try:
            sys.stdin = open('/dev/stdin')
            pdb.Pdb.interaction(self, *args, **kwargs)
        finally:
            sys.stdin = _stdin

urls = (
    '/', 'index',
    '/upload', 'upload',
    '/message', 'message',
)

class index:
    def GET(self):
        return open("resources/static/index.html",'r').read()

class upload:
    def GET(self):
        raise web.seeother('/')

    def POST(self):
        """ Handle web upload """
        i = web.input(name=[])
        upload = i['file']

        # check to make sure that the gif file magic is there.
        if upload.index("GIF89") != 0:
            return "INVALID GIF!"

        # save and make sure that the gif is 64x64 pixels
        open("/tmp/current.gif",'w').write(upload)
        giflib.resize("/tmp/current.gif")

        # copy it to the web folder as current.gif
        shutil.copyfile("/tmp/current.gif","resources/web/current.gif")
        return web.seeother("/")

class message:

    # send the current message unless we're setting the current message.
    def GET(self):
        try:
            message = web.input(name=[])
        except Exception,e:
            print str(e)
            message = None
        if message == None or message.values() == [[]]:
            return web.ctx.app_stack[0].value.value
        else:
            return self.process_message(web.input(name=[]))

    # process a sent message
    def POST(self):
        return self.process_message(web.input(name=[]))

    def process_message(self, i):
        message = i['message']
        print dir(web.ctx.app_stack[0])
        web.ctx.app_stack[0].set_value(message)
        return "set message %s" % message

# extends the web.py application class to provide some extra functionality needed to transfer data between the sign process and the webserver process
class SignApplication(web.application, object):
    def __init__(self, urls, globals, shared_value):
        self.value = shared_value
        # inherit all methods
        super(SignApplication,self).__init__(urls, globals)

    def set_value(self, value):
        self.value.value = value
        return True

    def get_value(self):
        #print "myval: " + str(self.value)
        return self.value

    def run(self):
        print "GGGGGGGG"
        super(SignApplication,self).run()
        print "thing"


# factory method - uses globals and the url paths defined in the start of the file to build application
def get_webserver(shared_value):
    app = SignApplication(urls, globals(), shared_value)
    return app

if __name__ == "__main__":
    print "standalone mode"
    get_webserver().run()
