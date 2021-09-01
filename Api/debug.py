import os
import json
import shutil
import time
import logging
import numpy as np
from .database import SQLiteConnection
from .config import Config
from .time_zones import Timezone

class Debugs():
    
    def __init__(self):
        """
        Clase que almacena los resultados de cada proceso en un directorio para supervisarlos
        solo se activa si el modo DEBUG es Verdadero
        """
        self.localtime=Timezone()
        self.JsonConfig=Config()
        sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
        conn = sqlite.db_connection() #Se conecta a la BD
        sqlite.create_flag_table(conn) #Crea la tabla FLAGS si no existe
        self.DEBUG = int(sqlite.select_flag(conn,"DEBUG")[2])#Devuelve el valor del DEBUG
        self.log=self.localtime.localDatetime.strftime("%Y")+self.localtime.localDatetime.strftime("%m")+self.localtime.localDatetime.strftime("%d")+sqlite.select_flag(conn,"LOG")[2]#Devuelve el valor del LOG
        conn.close() #Cierra la conexion existente 

    def Debug(self,id:int,data,name):
        """
        Crea un directorio con el No. de peticion
        y almacena en el los resultados de cada proceso que realiza el sistema
        """
        try:
            if self.DEBUG!=0:#Si el modo DEBUG es True
                os.makedirs(os.path.join(self.JsonConfig.Model["Debugs"], "debugs",self.localtime.localDatetime.strftime("%Y"),self.localtime.localDatetime.strftime("%m"),self.localtime.localDatetime.strftime("%d"),self.log), exist_ok=True)#Crea el directorio que tiene con el No. Peticion
                if id==1:#Si el ID es 1 creara un JSON con el dato enviado
                    with open(os.path.join(self.JsonConfig.Model["Debugs"], "debugs",self.localtime.localDatetime.strftime("%Y"),self.localtime.localDatetime.strftime("%m"),self.localtime.localDatetime.strftime("%d"),self.log,name), 'w',encoding='utf8') as file:
                        json.dump(data, file, indent=4,ensure_ascii=False,cls=NumpyEncoder)
                        logging.info(f'Se ha creado {name} para llevar un registro del proceso')
                        file.close()
                elif id==2:#Si el ID es 2 creara una copia fisica del fichero enviado
                    shutil.copy(data,os.path.join(self.JsonConfig.Model["Debugs"],"debugs",self.localtime.localDatetime.strftime("%Y"),self.localtime.localDatetime.strftime("%m"),self.localtime.localDatetime.strftime("%d"),self.log,name))
                    logging.info(f'Se ha creado {name} para llevar un registro del proceso')
        except Exception as e:
            logging.warning(f'No se pudo crear el registro porque se presento el siguiente error: {str(e)}')

class NumpyEncoder(json.JSONEncoder):
    """ Custom encoder for numpy data types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):

            return int(obj)

        elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)

        elif isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}

        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()

        elif isinstance(obj, (np.bool_)):
            return bool(obj)

        elif isinstance(obj, (np.void)): 
            return None

        return json.JSONEncoder.default(self, obj)