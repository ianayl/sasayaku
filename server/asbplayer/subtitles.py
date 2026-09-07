import requests
import base64
from server.utils import gen_diag
from server.utils.config import CONFIG

def send_subtitles(srt_path: str):
    """ Reads SRT file and sends it to asbplayer webserver. """
    diag = gen_diag("subs")
    
    url = CONFIG("asbplayer.server_url", "http://127.0.0.1:8766")
    endpoint = url + "/asbplayer/load-subtitles"
    try:
        with open(srt_path, 'rb') as f:
            srt_payload = base64.b64encode(f.read()).decode('utf-8')
        
        req = {
            "files": [{
                "name": srt_path,
                "base64": srt_payload
            }]
        }
        res = requests.post(endpoint, json=req)
        
        if res.status_code == 200:
            diag.info(f"sent {srt_path} to {endpoint}")
        else:
            diag.error(f"Got {res.status_code} from {endpoint}")
            diag.error(f"Response: {res.text}")
        
    except FileNotFoundError as e:
        diag.error(f"SRT file not found {srt_path}")
    except Exception as e:
        diag.error(f"Uncaught error {e}")
