import tornado.ioloop
import tornado.web
from tornado.log import enable_pretty_logging, app_log, access_log, gen_log
import logging
import os
import json
import subprocess
import glob
import psutil
import re

port = 8080 # for GCP Cloud Run

# log_file = os.environ.get('LOG_FILE')
# qmk_dir = os.environ.get('QMK_DIR')

# if log_file:
#     handler = logging.FileHandler(log_file)
#     enable_pretty_logging()
#     app_log.addHandler(handler)
#     access_log.addHandler(handler)
#     gen_log.addHandler(handler)

def get_jar_version(path):
    if path and re.search(r'/201/?', path):
        return "freerouting-2.0.1.jar"
    elif path and re.search(r'/210/?', path):
        return "freerouting-2.1.0.jar"
    return "freerouting-2.1.0.jar"

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        print(psutil.disk_usage("/"))
        self.write("Hello, I am Tornado.")


class BottomRouteHandler(tornado.web.RequestHandler):
    def post(self):
        
        print(self.request)
        print(self.request.body)
        print(psutil.disk_usage("/"))
        
        DSN_FILE_PATH = '/opt/input.dsn'
        RULE_FILE_PATH = '/opt/bottom.rules'
        OUT_FILE_PATH = '/opt/output.ses'
        
        jar_version = get_jar_version(self.request.path)
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)
        
        subprocess.run([
            "java",
            "-jar",
            jar_version,
            "--gui.enabled=false",
            "-de", 
            DSN_FILE_PATH,
            "-do",
            OUT_FILE_PATH,
            "-mp",
            "1000"
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
        
        jar_version = get_jar_version(self.request.path)
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)
        
        subprocess.run([
            "java",
            "-jar",
            jar_version,
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


class BottomRouteExcludeSpecifiedHandler(tornado.web.RequestHandler):
    def post(self):
        
        print(self.request)
        print(self.request.body)
        print(psutil.disk_usage("/"))

        ignore_param = self.get_argument('ignore', '')
        ignore_list = ignore_param.split(',') if ignore_param else []

        print(ignore_list)
        
        DSN_FILE_PATH = '/opt/input.dsn'
        RULE_FILE_PATH = '/opt/ignore.rules'
        OUT_FILE_PATH = '/opt/output.ses'
        
        jar_version = get_jar_version(self.request.path)
        
        if self.request.body:
            with open(DSN_FILE_PATH, 'wb') as f_ref:
                f_ref.write(self.request.body)

        command = [
            "java",
            "-jar",
            jar_version,
            "--gui.enabled=false",
            "-de", 
            DSN_FILE_PATH,
            "-do",
            OUT_FILE_PATH,
            "-dr",
            RULE_FILE_PATH,
            "-inc",
            ",".join(ignore_list)
        ]

        print(' '.join(command))
        
        subprocess.run(command)
        
        print(glob.glob('/opt/*'))
        
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=output.ses')
        self.write(open(OUT_FILE_PATH, 'rb').read())
        
        os.remove(DSN_FILE_PATH)
        os.remove(OUT_FILE_PATH)


def make_app():
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/getroutebottom/", BottomRouteHandler),
        (r"/getroutebottomexceptgnd/", BottomRouteExGndHandler),
        (r"/getroutebottomexceptspecified/", BottomRouteExcludeSpecifiedHandler),
        (r"/201/getroutebottom/", BottomRouteHandler),
        (r"/210/getroutebottom/", BottomRouteHandler),
        (r"/201/getroutebottomexceptgnd/", BottomRouteExGndHandler),
        (r"/210/getroutebottomexceptgnd/", BottomRouteExGndHandler),
        (r"/201/getroutebottomexceptspecified/", BottomRouteExcludeSpecifiedHandler),
        (r"/210/getroutebottomexceptspecified/", BottomRouteExcludeSpecifiedHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
