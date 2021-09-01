from xml.dom import minidom
import json



class Config():

    def __init__(self):
        """
        Clase que lee archivo de configuracion y devuelve el documento
        """
        with open("/home/cristian/Desktop/webservice/web-service/Config/InferenceModelConfig.json", "r") as json_file:
            self.Model = json.load(json_file)
        #doc=minidom.parse("./Config/InferenceModelConfig.xml")#Lee XML
        #self.Model=doc.getElementsByTagName("Model")#Guarda un XmlNodeList del Hastag "Model"