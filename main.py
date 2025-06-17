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
import tempfile
import time
import run_command
import shutil

# Cloud Runのログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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


class GetRoutedHandler(tornado.web.RequestHandler):
    def post(self):
        logger.info(self.request)
        logger.info(psutil.disk_usage("/"))

        ignore_param = self.get_argument('ignore', '')
        ignore_list = ignore_param.split(',') if ignore_param else []

        mp_param = self.get_argument('mp', '')

        logger.info(ignore_list)
        
        DSN_FILE_PATH = '/opt/input.dsn'
        RULE_FILE_PATH = '/opt/input.rules'
        OUT_FILE_PATH = '/opt/output.ses'
        
        jar_version = get_jar_version(self.request.path)

        # マルチパートフォームデータからファイルを取得
        if self.request.files:
            if 'dsn' in self.request.files:
                with open(DSN_FILE_PATH, 'wb') as f_ref:
                    f_ref.write(self.request.files['dsn'][0]['body'])
            
            if 'rules' in self.request.files:
                with open(RULE_FILE_PATH, 'wb') as f_ref:
                    f_ref.write(self.request.files['rules'][0]['body'])

        logger.info(self.request.files['dsn'][0]['body'])
        logger.info(self.request.files['rules'][0]['body'])

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
        ]

        if mp_param:
            command.append("-mp")
            command.append(mp_param)

        if ignore_list:
            command.append("-inc")
            command.append(",".join(ignore_list))

        logger.info(' '.join(command))

        cp = subprocess.run(command, encoding='utf-8', stdout=subprocess.PIPE)

        logger.info(cp.stdout)
        logger.info(glob.glob('/opt/*'))
        logger.info(f"os.path.getsize(OUT_FILE_PATH): {os.path.getsize(OUT_FILE_PATH)}")
        
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=output.ses')
        self.set_header('Content-Length', os.path.getsize(OUT_FILE_PATH))
        self.write(open(OUT_FILE_PATH, 'rb').read())
        
        os.remove(DSN_FILE_PATH)
        os.remove(RULE_FILE_PATH)
        os.remove(OUT_FILE_PATH)


class RouteHandler(tornado.web.RequestHandler):
    def post(self):
        version = self.get_argument('version', '2.0.1')
        logger.info(version)

        try:
            # リクエストボディからDSNファイルの内容を取得
            dsn_content = self.request.body
            if not dsn_content:
                self.set_status(400)
                self.write(json.dumps({
                    "success": False,
                    "error": "DSNファイルが送信されていません"
                }, ensure_ascii=False))
                return
            
            # 一時ファイルにDSN内容を保存
            with tempfile.NamedTemporaryFile(suffix='.dsn', delete=False) as temp_dsn:
                temp_dsn.write(dsn_content)
                temp_dsn_path = temp_dsn.name
            
            try:
                start_time = time.time()
                tmp_dir = tempfile.mkdtemp()
                logger.info(f"一時ディレクトリを作成: {tmp_dir}")
                original_dsn = os.path.join(tmp_dir, "original.dsn")
                shutil.copy2(temp_dsn_path, original_dsn)
                output_ses = os.path.join(tmp_dir, "output.ses")
                success, timed_out, elapsed = run_command.run_freerouting(
                    original_dsn,
                    output_file=output_ses,
                    version=version,
                    max_passes=250,
                    timeout=300
                )
                logger.info(f"result: success={success}, timed_out={timed_out}, elapsed={elapsed}")
                
                if success and not timed_out:
                    size = os.path.getsize(output_ses)
                    logger.info(f"os.path.getsize(output_ses): {size}")
                    # ファイルI/Oの安定化
                    with open(output_ses, 'rb+') as f:
                        f.flush()
                        os.fsync(f.fileno())
                    time.sleep(0.1)
                    self.set_header('Content-Type', 'application/octet-stream')
                    self.set_header('Content-Disposition', 'attachment; filename=output.ses')
                    self.set_header('Content-Length', size)
                    with open(output_ses, 'rb') as f:
                        self.write(f.read())
                else:
                    self.set_header('Content-Type', 'application/json')
                    self.write(json.dumps({
                        "success": False,
                        "error": f"予期せぬエラーが発生しました1: Freerouting失敗またはタイムアウト"
                    }, ensure_ascii=False))
            finally:
                if os.path.exists(temp_dsn_path):
                    os.unlink(temp_dsn_path)
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)
        except Exception as e:
            self.set_header('Content-Type', 'application/json')
            self.write(json.dumps({
                "success": False,
                "error": f"予期せぬエラーが発生しました2: {str(e)}"
            }, ensure_ascii=False))


def make_app():
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/getrouted/", GetRoutedHandler),
        (r"/201/getrouted/", GetRoutedHandler),
        (r"/210/getrouted/", GetRoutedHandler),
        (r"/route/", RouteHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
