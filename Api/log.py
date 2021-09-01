import os
import time
import shutil
import logging
from .database import SQLiteConnection
from .time_zones import Timezone
from .config import Config

class Logs():
    
    def __init__(self):
        self.localtime=Timezone()
        self.JsonConfig=Config()
        os.makedirs(os.path.join(self.JsonConfig.Model["TempFile"],"Temp"),exist_ok=True)
        self.RUTA=os.path.join(self.JsonConfig.Model["TempFile"],"Temp")
        os.makedirs(os.path.join(self.RUTA,"Dir_Img"),exist_ok=True)
        self.Dir_Img=os.path.join(self.RUTA,"Dir_Img")
        sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
        conn = sqlite.db_connection()
        sqlite.create_flag_table(conn)
        self.LogId=int(sqlite.select_flag(conn,"LOG")[2])
        self.log = self.localtime.localDatetime.strftime("%Y")+self.localtime.localDatetime.strftime("%m")+self.localtime.localDatetime.strftime("%d")+str(self.LogId)
        os.makedirs(os.path.join(self.JsonConfig.Model["Logs"], "logs", self.localtime.localDatetime.strftime("%Y"), self.localtime.localDatetime.strftime("%m"), self.localtime.localDatetime.strftime("%d")), exist_ok=True)
        logging.basicConfig(filename=os.path.join(self.JsonConfig.Model["Logs"], "logs", self.localtime.localDatetime.strftime("%Y"), self.localtime.localDatetime.strftime("%m"), self.localtime.localDatetime.strftime("%d"), f"{self.log}.log"),
            format='{levelname} [{asctime}] {message}',style='{',level=logging.INFO,)
        self.LogPath=os.path.join(self.JsonConfig.Model["Logs"], "logs", self.localtime.localDatetime.strftime("%Y"), self.localtime.localDatetime.strftime("%m"), self.localtime.localDatetime.strftime("%d"), f"{self.log}.log")
        conn.close()
        
    def refresh(self):
        print("Refresh")
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])
        shutil.rmtree(self.RUTA,ignore_errors=True)
        sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
        conn = sqlite.db_connection()
        sqlite.update_flag(conn,[str(self.LogId+1),"LOG"])
        conn.close()