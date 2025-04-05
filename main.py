import tornado.ioloop
import tornado.web
from tornado.log import enable_pretty_logging, app_log, access_log, gen_log
import logging
import os
import json
import subprocess
import glob
import psutil

port = 8080 # for GCP Cloud Run

# log_file = os.environ.get('LOG_FILE')
# qmk_dir = os.environ.get('QMK_DIR')

# if log_file:
#     handler = logging.FileHandler(log_file)
#     enable_pretty_logging()
#     app_log.addHandler(handler)
#     access_log.addHandler(handler)
#     gen_log.addHandler(handler)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        print(psutil.disk_usage("/"))
        self.write("Hello, I am Tornado.")


class RouteHandler(tornado.web.RequestHandler):
    def post(self):
        
        print(self.request)
        print(self.request.body)
        print(psutil.disk_usage("/"))

        subprocess.run([
            "java",
            "-jar",
            "freerouting-2.0.1.jar",
            "--gui.enabled=false",
            "-de", 
            DSN_FILE_PATH,
            "-do",
            OUT_FILE_PATH,
            "-mp",
            "1000"
        ])
        
        DSN_FILE_PATH = '/opt/input.dsn'
        OUT_FILE_PATH = '/opt/output.ses'
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)
        
        print(glob.glob('/opt/*'))
        
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=output.ses')
        self.write(open(OUT_FILE_PATH, 'rb').read())
        
        os.remove(DSN_FILE_PATH)
        os.remove(OUT_FILE_PATH)


class BottomRouteHandler(tornado.web.RequestHandler):
    def post(self):
        
        print(self.request)
        print(self.request.body)
        print(psutil.disk_usage("/"))
        
        DSN_FILE_PATH = '/opt/input.dsn'
        RULE_FILE_PATH = '/opt/bottom.rules'
        OUT_FILE_PATH = '/opt/output.ses'
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)
        
        subprocess.run([
            "java",
            "-jar",
            "freerouting-2.0.1.jar",
            "--gui.enabled=false",
            "-de", 
            DSN_FILE_PATH,
            "-do",
            OUT_FILE_PATH,
            "-dr",
            RULE_FILE_PATH
        ])
        
        print(glob.glob('/opt/*'))
        
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=output.ses')
        self.write(open(OUT_FILE_PATH, 'rb').read())
        
        os.remove(DSN_FILE_PATH)
        os.remove(OUT_FILE_PATH)


class BottomRouteExGndHandler(tornado.web.RequestHandler):
    def post(self):
        
        print(self.request)
        print(self.request.body)
        print(psutil.disk_usage("/"))
        
        DSN_FILE_PATH = '/opt/input.dsn'
        RULE_FILE_PATH = '/opt/bottom.rules'
        OUT_FILE_PATH = '/opt/output.ses'
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)
        
        subprocess.run([
            "java",
            "-jar",
            "freerouting-2.0.1.jar",
            "--gui.enabled=false",
            "-de", 
            DSN_FILE_PATH,
            "-do",
            OUT_FILE_PATH,
            "-dr",
            RULE_FILE_PATH,
            "-inc",
            "GND0,GND1,GND2,GND3,GND4,GND5,GND6,GND7"
        ])
        
        print(glob.glob('/opt/*'))
        
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=output.ses')
        self.write(open(OUT_FILE_PATH, 'rb').read())
        
        os.remove(DSN_FILE_PATH)
        os.remove(OUT_FILE_PATH)


def make_app():
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/getroute/", RouteHandler),
        (r"/getroutebottom/", BottomRouteHandler),
        (r"/getroutebottomexceptgnd/", BottomRouteExGndHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
