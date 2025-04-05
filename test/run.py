import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

FREEROUTING_CLOUDRUN_URL = "https://freeroutingv2-68523936656.asia-northeast1.run.app"

DSN_FILE = "intermediate.dsn"
SESSION_FILE = "intermediate.ses"

def main():

    dsn_data = open(DSN_FILE, "r").read()

    route_request = urllib.request.Request(
        url=FREEROUTING_CLOUDRUN_URL + "/getroutebottom/", data=dsn_data.encode(), method="POST"
    )

    route_response = urllib.request.urlopen(route_request)

    session_data = route_response.read().decode("utf-8")

    open(SESSION_FILE, "w").write(session_data)

if __name__ == "__main__":
    main()

