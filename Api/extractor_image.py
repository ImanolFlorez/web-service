import os
import json
import base64
import logging
from cv2 import cv2
from PIL import Image
from .log import Logs
from .debug import Debugs
from .database import SQLiteConnection
from pdf2image import convert_from_path
from .config import Config

class Imag():

    def __init__(self):
        self.Log=Logs()
        self.Debug=Debugs()
        self.pdf_dir_path = None
        self.pdf_name = None
        self.JsonConfig=Config()
        sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
        conn = sqlite.db_connection()
        sqlite.create_flag_table(conn)
        self.width = int(sqlite.select_flag(conn,"WIDTH")[2])
        self.height =int(sqlite.select_flag(conn,"HEIGHT")[2])
        self.num_pages = int(sqlite.select_flag(conn,"NUM_PAG")[2])
        self.out_image=sqlite.select_flag(conn,"OUT_IMAGE")[2]
        conn.close()

    def num_contours(self, img_path: str) -> int:
        """
        Recibe una imagen y devuelve el número de contornos dentro de ella.\n
        Argumentos:\n
        img_path: ruta de la imagen a la que se le quiere encontrar los contornos.\n
        Retorna:\n
        Número de contornos que contiene la imagen.
        """
        try:
            image = cv2.imread(img_path) # Lee imagen con opencv.
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)# Convierte la imagen a escala de grises.
            _, binary = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV) # Binariza la imagen, es decir, la convierte a B&W.
            contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)# Encuentra los contornos.
            return len(contours) # Retorna el número de contornos encontrados.
        except Exception as e:
            logging.error('Parsing Not Succefully num_contours: '+str(e))

    def resize_image(self, img_path: str, index: int):
        """
        Redimensiona el tamaño de una imagen.\n
        Argumentos:\n
        img_path: ruta de la imagen que se desea redimensionar.\n
        index: número de la página del PDF que se está procesando actualmente.\n
        Retorna:\n
        Tupla con la imagen redimensionada y el nombre.
        """
        try:
            img = Image.open(img_path) # Lee la imagen
            resized_image = img.resize((self.width, self.height)) # Se redimensiona la imagen.
            temp_name = os.path.join("/".join(img_path.split("/")[:-1]), self.pdf_name.split(".")[0]) # Se crea un nombre general para las imagenes
            resized_image_name = os.path.join(f'{temp_name}_{index}.{self.out_image}') # Se le concatena el indice para identificar cada página.
            resized_image.save(resized_image_name,self.out_image) # Se guarda la imagen
            return resized_image, resized_image_name # Se retorna la imagen y el nombre de la imagen.
        except Exception as e:
            logging.error('Parsing Not Succefully resize_image: '+str(e))

    def encode_image(self, img_path: str) -> str:
        """
        Convierte una imagen a bytes.\n
        Argumentos:\n
        img_path: ruta de la imagen que se desea convertir a bytes.\n
        Retorna:\n
        Bytes del archivo en base64.
        """
        try:
            with open(img_path, "rb") as img_decode: #Abre la Imagen
                bit_enconded_img = base64.encodebytes(img_decode.read()) #Codifica la imagen en Base64
                return bit_enconded_img.decode("ascii") #Retorna la imagen codificada
        except Exception as e:
            logging.error('Parsing Not Succefully encode_image: '+str(e))
            return None

    def parse(self,path,name) -> json:
        """
        Retorna un json con el nombre y los bytes de las páginas del documento PDFs redimensionadas.
        """
        logging.info('Parsing Pipeline Image: ')
        self.pdf_dir_path=path
        self.pdf_name=name
        output_json = []
        try:
            # Se convierten las páginas especificadas del PDF a imagenes.
            images_from_path = convert_from_path(self.pdf_dir_path, fmt=f'{self.out_image}', last_page=self.num_pages, output_folder=self.Log.Dir_Img)
            for i, image in enumerate(images_from_path):
                number_of_contours = self.num_contours(image.filename)# Se calcula el número de contornos para cada imagen.
                if number_of_contours > 5:# Si el número de contornos es mayor a 5 significa que la imagen no está en blanco.
                    _, res_img_name = self.resize_image(image.filename, i)# Se redimensiona la imagen
                    output_dict = {"img_name": res_img_name.split("/")[-1], "img_bytes": self.encode_image(res_img_name)}#Llena el diccionario
                    output_json.append(output_dict)#Agrega el diccionario a la lista
                    self.Debug.Debug(2,res_img_name,res_img_name.split("/")[-1])#Envia el la imagen para crear una copia
                else: # Si la imagen está en blanco, se crea un diccionario con el nombre de la imagen y los bytes vacios.
                    temp_name = os.path.join("/".join(image.filename.split("/")[:-1]), self.pdf_name.split(".")[0])# Se guarda el nombre de la imagen.
                    img_name = f"{temp_name}_{i}.png"
                    output_dict = {"img_name": img_name.split("/")[-1], "img_bytes": None}#Llena el diccionario
                    output_json.append(output_dict)#Agrega el diccionario a la lista
                    logging.warning(f'Pipeline Imagen: la imagen {img_name.split("/")[-1]} esta vacia') 
            self.Debug.Debug(1,output_json,"Pipeline_Image.json")#Envia el resultado para crear un JSON
            os.remove(image.filename)
            return output_json # Se retorna un JSON.
        except Exception as e:
            logging.error('Parsing Not Succefully parse: '+str(e))
            return {"error": str(e)}