from obj.bout import Bout, BoutStatus
from obj.boutrecorder import BoutRecorder
from utils.ss_conf import Config
import time 
from threading import Thread

c = Config()

def main():
    while True:
        b = Bout(url=c.saltyurl)
        if b.is_valid() and b.get_status() is BoutStatus.OPEN:
            try:
                c.log.debug(c.banner)
                stop = False
                br = BoutRecorder(b)
                c.log.info(f'RECORDING: {b.p1name} vs {b.p2name}  -> {br.quality} :: {br.raw_path}')
                thread = Thread(target=br.record, args =(lambda : stop, ))
                thread.start()

                b = Bout(url=c.saltyurl)
                while (b.get_status() is not BoutStatus.RED_WIN) and (b.get_status() is not BoutStatus.BLUE_WIN):
                    b = Bout(url=c.saltyurl)
                    c.log.debug(f'RECORDING: {b.p1name} vs {b.p2name} -> {br.quality} :: {br.raw_path}')
                    time.sleep(1)
                stop = True
                c.log.info(f'DONE: {b.p1name} vs {b.p2name}  -> {br.quality} :: {br.mp4_path}')
                c.log.debug(c.banner)
            except Exception as e:
                c.log.critical(e)
        else:
            c.log.debug(f'INVALID {b.__dict__}')
            time.sleep(c.sleep)

if __name__ == "__main__":
    main()