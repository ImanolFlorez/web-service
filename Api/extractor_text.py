import re
import fitz
import pyocr
import logging
import pytesseract
from .log import Logs
from collections import Counter
from .debug import Debugs
from tika import parser as tika_parser, language
from pdf2image import convert_from_path

# Excepción lanzada cuando falla un parseo
class NotParsedError(Exception):
    pass

class Parser(object):
    
    def __init__(self):
        self.Log=Logs()
        self.Debug=Debugs()
        

    # Sanity check
    @staticmethod
    def sanity_check(extracted_text):
        if extracted_text is None:
            raise NotParsedError("Empty text")
        # Comprueba que la longitud del texto no sea cero
        if len(extracted_text) < 1:
            raise NotParsedError("Empty text")
        # Comprueba numero de caracteres diferentes quitando caracteres de espaciado
        space = re.compile(r"\s+")
        letter_count = Counter(list(space.sub('', extracted_text)))
        if len(letter_count) <= 1:
            raise NotParsedError("Empty text")

    # Parsea un documento con PyMuPDF
    
    def parse_with_pymupdf(self,file_path: str) -> dict:
        try:
            logging.info('Parsing with PyMuPDF')
            pages = []
            doc = fitz.open(file_path)
            for page_num in range(doc.pageCount):
                d = {}
                text = doc.getPageText(page_num)
                pages.append(text)
            doc.close()
            full_text = "\n".join(pages)
            Parser.sanity_check(full_text)
            return {"parser": "PyMuPDF", "text": full_text,"pages": str(len(pages))}
        except Exception as e:
            raise NotParsedError(str(e))


    # Usa un OCR para extraer texto de las páginas de un PDF escaneado. Primero convierte el
    # documento en imágenes, una por página, y después aplica el OCR sobre cada imagen/página.
    # - Requiere `poppler`: `$ sudo apt install poppler-utils`
    def parse_with_ocr(self,file_path: str) -> dict:
        logging.info('Parsing with OCR')
        try:
            pages = []
            images_from_path = convert_from_path(file_path,output_folder=self.Log.RUTA)
            for image in images_from_path:
                text = pyocr.get_available_tools()[0].image_to_string(image,builder=pyocr.builders.TextBuilder())
                pages.append(text)
            full_text = "\n".join(pages)
            Parser.sanity_check(full_text)
            return {"parser": "OCR", "text": full_text[:16384],
                        "pages": str(len(pages))}
        except Exception as e:
            raise NotParsedError(str(e))


    # Parsea un documento con Apache Tika
    def parse_with_tika(self,file_path: str) -> dict:
        try:
            logging.info('Parsing with Tika')
            parsed = tika_parser.from_file(file_path)
            full_text = parsed["content"]
            logging.info(language.from_buffer(full_text))
            logging.info(full_text)
            status = parsed["status"]
            if status != 200:
                logging.warning('Apache Tika raised status {}.'.format(status))
                raise NotParsedError("Apache Tika raised status {}.".format(status))
            Parser.sanity_check(full_text)
            if "Page-Count" in parsed["metadata"]:
                return {"parser": "Tika", "text": full_text[:16384],
                        "pages": parsed["metadata"]["Page-Count"]}
            elif "Slide-Count" in parsed["metadata"]:
                return {"parser": "Tika", "text": full_text[:16384],
                        "pages": parsed["metadata"]["Slide-Count"]}
            else:
                return {"parser": "Tika", "text": full_text[:16384],
                        "pages": "1"}
        except Exception as e:
            raise NotParsedError(str(e))


    # Parsea un fichero.
    # Args:
    #     file_path: Ruta del fichero que se quiere parsear.
    #     real_file_name: Nombre original del fichero.
    # Returns:
    #     Un diccionario con 3 campos:
    #     * document: nombre del documento
    #     * parser: nombre del parser usado
    #     * text: texto del documento
    def parse(self, file_path: str, real_file_name: str, File: str) -> dict:
        logging.info('Parsing Pipeline Text')
        result = {}
        logging.info('Parsing file {} '.format(real_file_name))
        # Si es un fichero PDF probamos varias opciones hasta tener algo
        if real_file_name.lower().endswith(".pdf"):
            try:
                result = self.parse_with_pymupdf(file_path)
            except NotParsedError as e1:
                logging.info('Parsing with PyMuPDF was not successful.')
                if str(e1) == "Empty text":
                    try:
                        result = self.parse_with_ocr(file_path)
                    except NotParsedError as e2:
                        logging.info('Parsing with OCR was not successful.')
                        if str(e2) == "Empty text":
                            try:
                                result = self.parse_with_tika(file_path)
                            except NotParsedError as e3:
                                logging.info('Parsing with Tika was not successful.')
                                if str(e3) == "Empty text":
                                    result={"parser": "", "text": "","pages":""}
                                else:
                                    raise e3
                        else:
                            raise e2
                else:
                    raise e1
        else:
            try:
                result = self.parse_with_tika(file_path)
            except NotParsedError as e:
                logging.info('Parsing with Tika was not successful.')
                if str(e) == "Empty text":
                    result={"parser": "", "text": "","pages":""}
                else:
                    raise e
        result["document"] = real_file_name
        if File!=None:
            result["code"] = File["Code"]
            result["path"] = File["path"]
            result["name"] = File["path"].split('\\')[-1].split('.')[0]
        else:
            result["code"]=""
            result["path"]=""
            result["name"] = ""
        if result["pages"]=="":
            result["pages"]="1"
        self.Debug.Debug(1,result,"Pipeline_Text.json")
        return result