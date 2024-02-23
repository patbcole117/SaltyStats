from obj.bout import Bout, BoutStatus
from obj.boutrecorder import BoutRecorder
from utils.ss_conf import Config
import time 
from threading import Thread
import requests
import json


c = Config()

def main():
    while True:
        time.sleep(c.sleep)
        try:
            data = requests.get(c.saltyurl)
        except Exception as e:
            c.log.error(e)
        if data.content is not None:
            bout = Bout(saltydata=json.loads(data.content))
            c.log.debug(f'bout.__dict__: {bout.__dict__}')
            status = bout.get_status()
            if status == BoutStatus.OPEN:
                try:
                    c.log.debug(c.banner)
                    stop = False
                    br = BoutRecorder(bout)
                    c.log.info(f'RECORDING: {bout.p1name} vs {bout.p2name}  -> {br.quality} :: {br.raw_path}')
                    thread = Thread(target=br.record, args =(lambda : stop, ))
                    thread.start()

                    data = requests.get(c.saltyurl)
                    bout = Bout(saltydata=json.loads(data.content))
                    while (bout.get_status() is not BoutStatus.RED_WIN) and (bout.get_status() is not BoutStatus.BLUE_WIN):
                        data = requests.get(c.saltyurl)
                        bout = Bout(saltydata=json.loads(data.content))
                        c.log.debug(f'RECORDING: {bout.p1name} vs {bout.p2name} -> {br.quality} :: {br.raw_path}')
                        time.sleep(1)
                    stop = True
                    c.log.info(f'DONE: {bout.p1name} vs {bout.p2name}  -> {br.quality} :: {br.mp4_path}')
                    c.log.debug(c.banner)
                except Exception as e:
                    c.log.critical(e)
            else:
                c.log.debug(f'INVALID {bout.__dict__}')
                time.sleep(c.sleep)

if __name__ == "__main__":
    main()