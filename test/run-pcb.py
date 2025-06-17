import logging
import urllib.request
import urllib.error
import secrets

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DSN_FILE = "pcb_rm.dsn"
RULES_FILE = "pcb.rules"
SESSION_FILE = "pcb.ses"
MP_VALUE = 1000
FREEROUTING_VERSION = "201"

def main(mp_value=MP_VALUE, freerouting_version=FREEROUTING_VERSION):
    dsn_data = open(DSN_FILE, "r").read()
    rules_data = open(RULES_FILE, "r").read()

    # ランダムなboundaryを生成
    boundary = f"----WebKitFormBoundary{secrets.token_hex(16)}"
    data = []
    data.append(f"--{boundary}")
    data.append('Content-Disposition: form-data; name="dsn"; filename="pcb.dsn"')
    data.append("Content-Type: text/plain")
    data.append("")
    data.append(dsn_data)
    data.append(f"--{boundary}")
    data.append('Content-Disposition: form-data; name="rules"; filename="pcb.rules"')
    data.append("Content-Type: text/plain")
    data.append("")
    data.append(rules_data)
    data.append(f"--{boundary}--")
    data.append("")

    body = "\r\n".join(data)

    FREEROUTING_CLOUDRUN_URL = "https://freeroutingv2-68523936656.asia-northeast1.run.app"
    url = f"{FREEROUTING_CLOUDRUN_URL}/{freerouting_version}/getrouted/?mp={mp_value}"

    route_request = urllib.request.Request(
        url=url,
        data=body.encode(),
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
    )

    route_response = urllib.request.urlopen(route_request)

    session_data = route_response.read().decode("utf-8")

    open(SESSION_FILE, "w").write(session_data)

if __name__ == "__main__":
    main()

