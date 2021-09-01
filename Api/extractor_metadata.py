import json
import logging
from .log import Logs
from .debug import Debugs

class Metadata(object):
    
    def __init__(self):
        self.Log=Logs()
        self.Debug=Debugs()

    def json_validation(self,json_data: json)-> tuple:
        """
        Recibe un JSON e intenta 'parsearlo' para verificar si es valido o no.\n
        Argumentos:\n
        json_data: JSON a ser validado.\n
        Retorna:\n
        Una tupla (dict, bool) con el JSON 'parseado' como diccionario y True o False.
        Si el JSON es valido, lo retornará parseado como un diccionario de Python y True,
        sino, imprimirá el mensaje de error y retornará un diccionario vacio y False.
        """
        logging.info('Parsing Pipeline Metadata')
        try:
            data = json.loads(json_data)# Intenta 'parsear' el JSON a un diccionario de Python
            if not data:# Si el JSON está vacio
                logging.warning('Json Validation: JSON is empty.')
                self.Debug.Debug(1,{},"Data.json")#Envia el resultado para crear una copia para el modo DEBUG
                return {}, False
            else: 
                logging.info('Json Validation: Succefully')
                self.Debug.Debug(1,data,"Data.json")#Envia el resultado para crear una copia para el modo DEBUG
                return data, True
        except json.decoder.JSONDecodeError as e:
            logging.error("Error Json Validation: " + str(e) + "\033[0m")
            self.Debug.Debug(1,{},"Data.json")#Envia el resultado para crear una copia para el modo DEBUG
            return {}, False