from utils.ss_conf import Config
import os  
import subprocess  
import datetime  
import streamlink

CHUNK_SIZE = 8192
c = Config()

class BoutRecorder:  
  
    def __init__(self, bout):  
        self.ffmpeg_path = c.ffmpeg_path
        self.path = c.conf["REC"]["ROOT_PATH"]
        self.quality = c.conf["REC"]["QUALITY"]
        self.streamname = c.conf["REC"]["STREAM"]

        self.filename = bout.p1name + "-vs-" + bout.p2name + "-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
        self.raw_path = os.path.join(c.root_path, self.filename) + ".stream"
        self.mp4_path = os.path.join(c.root_path, self.filename) + ".mp4"
        self.stream_fd = streamlink.streams(self.streamname)[self.quality].open()
        self.file_fd = open(self.raw_path, "ab")
        
    def record(self, stop):
        try:
            while True:
                self.file_fd.write(self.stream_fd.read(CHUNK_SIZE))
                if stop():
                     break
        except Exception as e:
             c.log.critical(e)
        finally:
             self.file_fd.close()
             self.stream_fd.close()
             self.ffmpeg_streamfile()

    def ffmpeg_streamfile(self):
        c.log.debug(f'BEGIN FFMPEG PROCESSING {self.raw_path}')
        if(os.path.exists(self.raw_path) is True):  
            try:
                if c.log_level == "DEBUG":  
                    subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-i', self.raw_path, '-c', 'copy', self.mp4_path])
                else:
                    subprocess.call([self.ffmpeg_path, '-err_detect', 'ignore_err', '-hide_banner', '-loglevel', 'error', '-i', self.raw_path, '-c', 'copy', self.mp4_path])
                os.remove(self.raw_path)
            except Exception as e:  
                c.log.critical(e)  
        else:  
            c.log.error("FFMPEG CANNOT LOCATE STREAM FILE.")
    
    