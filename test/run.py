import logging
import urllib.request
import urllib.error
import json
import os
import time

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# コンソールハンドラーの設定
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DSN_FILE = "gndonly_routed.dsn"
SESSION_FILE = "gndonly_routed.ses"

def main():
    dsn_data = open(DSN_FILE, "r").read()

    FREEROUTING_CLOUDRUN_URL = "https://freeroutingv2-68523936656.asia-northeast1.run.app"
    # FREEROUTING_CLOUDRUN_URL = "http://localhost:8080"
    url = f"{FREEROUTING_CLOUDRUN_URL}/route/?version=2.0.1" # getrouted
    print(url)

    route_request = urllib.request.Request(
        url=url,
        data=dsn_data.encode(),
        method="POST"
    )

    count = 5

    while True:

        try:
            route_response = urllib.request.urlopen(route_request)
            logger.info(route_response)
        except urllib.error.URLError as e:
            logger.error(e.reason)
            return

        if route_response.getheader("Content-Type") == "application/json":
            response_dict = json.loads(route_response.read())
            logger.info(response_dict)
            logger.info(response_dict["success"])
        elif route_response.getheader("Content-Type") == "application/octet-stream":
            session_data = route_response.read().decode("utf-8")
            print(f"session_data: {session_data}")
            open(SESSION_FILE, "w").write(session_data)
            size = os.path.getsize(SESSION_FILE)
            logger.info(f"os.path.getsize(output_ses): {size}")
            # ファイルI/Oの安定化
            with open(SESSION_FILE, 'rb+') as f:
                f.flush()
                os.fsync(f.fileno())
            time.sleep(0.1)
            self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Disposition', 'attachment; filename=output.ses')
            self.set_header('Content-Length', size)
            with open(SESSION_FILE, 'rb') as f:
                self.write(f.read())
        else:
            logger.error("Content-Type is not application/json or application/octet-stream")
            return

        count -= 1
        if count == 0:
            break


if __name__ == "__main__":
    main()


