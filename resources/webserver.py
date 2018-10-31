#!/usr/bin/python

import web
import shutil
import giflib

urls = (
    '/', 'index',
    '/upload', 'upload'
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

def run():
    app = web.application(urls, globals())
    app.run()
