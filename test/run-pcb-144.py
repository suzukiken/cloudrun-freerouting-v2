import logging
import urllib.request
import urllib.error
import secrets

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DSN_FILE = "pcb_rm.dsn"
SESSION_FILE = "pcb.ses"


def main():
    dsn_data = open(DSN_FILE, "r").read()

    FREEROUTING_CLOUDRUN_URL = "https://freerouting-68523936656.asia-northeast1.run.app"
    FREEROUTING_CLOUDRUN_URL = "https://freeroutingv1-68523936656.asia-northeast1.run.app"
    url = f"{FREEROUTING_CLOUDRUN_URL}/getroutebottom/"
    url = f"{FREEROUTING_CLOUDRUN_URL}/getroutebottomvertical/"

    route_request = urllib.request.Request(
        url=url,
        data=dsn_data.encode(),
        method="POST"
    )

    route_response = urllib.request.urlopen(route_request)

    session_data = route_response.read().decode("utf-8")

    open(SESSION_FILE, "w").write(session_data)

if __name__ == "__main__":
    main()

