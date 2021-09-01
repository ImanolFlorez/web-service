import logging
import numpy as np
from numpy.core.fromnumeric import transpose
import pandas as pd
import os
import json
from .log import Logs
from .database import SQLiteConnection
from .config import Config

class decision_maker():

    def __init__(self):
        try:
            self.Log=Logs()
            self.JsonConfig=Config()
            sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
            conn = sqlite.db_connection()
            cur = conn.cursor()
            # Se pregunta si las tablas 'Areas' y 'Parameters' existen.
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('Areas', 'Parameters')")
            tables = np.array(cur.fetchall()).flatten().tolist()
            if 'Areas' not in tables and 'Parameters' not in tables:
                # Si 'Areas' y 'Parameters' no están en los resultados del query anterior quiere decir
                # que no han sido creadas, por lo tanto, se pcede a crearlas.
                sqlite.create_area_table(conn)
                sqlite.create_parameters_table(conn)
                # Inserta los parametros en la tabla de de parametros
                sqlite.insert_parameter(conn, ["porc_conf", 0])
                sqlite.insert_parameter(conn, ["marg_err", 1])
            conn.close()
        except Exception as i:
            logging.error('Decision Maker: Error '+str(i))

    def select_candidates(self,results: pd.DataFrame, ppv_mat: pd.DataFrame ) -> pd.DataFrame:
        # Obtenemos los indices, en este caso son los modelos que tenemos (red neuronal, metadatos, texto)
        search_index = results.index
        # Calculamos un nuevo DataFrame en el cual los valores será el producto de las probabilidades por su PPV correspondiente
        weight_df = pd.DataFrame()
        logging.info('----------------------------------Multiplicamos la probabilidad por su PPV Correspondiente')
        weight_df = results * ppv_mat.loc[search_index]
        logging.info(f'\n {weight_df} \n \n \n')

        # Obtenemos los mayores de cada columna
        logging.info('----------------------------------Obtenemos los maximos de cada columna')
        highest_scores = np.array(weight_df.describe().loc["max"])
        logging.info(f'\n {highest_scores} \n \n \n')
        # Obtenemos las posiciones de los mayores
        rows, cols = np.where(weight_df == highest_scores)
        # Por la naturaleza del metodo nos devuelve las posiciones ordenadas por filas, se necesitan ordenadas
        # por columnas, entonces se convierten en un diccionario donde las llaves serán las columnas y los
        # valores serán las filas
        dict_row_col = {}
        for i in range(len(cols)):
            dict_row_col[cols[i]] = rows[i]
        # Ordenamos las llaves del diccionario
        sorted_keys = sorted(dict_row_col)
        # Creamos dos listas para obtener nuestras posiciones ordenadas por columnas
        r, c = [], []
        for k in sorted_keys:
            r.append(dict_row_col[k])
            c.append(k)
        # Obtenemos los valores de las probabilidades correspondientes a los mayores puntajes
        res = {}
        for i in range(len(rows)):
            columns = results.columns.tolist()
            res[columns[i]] = results.iloc[r[i], c[i]]

        sorted_values = sorted(res, key=res.get, reverse=True)
        output = {}
        for k in sorted_values:
            output[k] = res[k]
        logging.info(output)
        output = pd.DataFrame(data=output, index=["0"])
        logging.info(output.columns.values)
        logging.info('----------------------------------Retornamos Las probabilidades ya procesadas en el PPV')
        return output

    def read_confusion_matrix(self,path, labels=[]):
        try:
            # Si se envia el parametro 'labels' singifica que es la matriz
            # de confusión de la red neuronal
            if labels:
                conf_mat = pd.read_csv(path, names=labels)
                conf_mat.index = labels
            else:
                # Las matrices de confusión del modelo de texto y metadatos
                conf_mat = pd.read_csv(path)
            
            logging.info(f'\n {conf_mat} \n \n \n')
            return conf_mat
        except Exception as e:
            logging.error(f'Read Matrix confusion: {e}')

    def get_diagonal(self,conf_mat, box=""):
        logging.info('----------------------------------Obteniendo Diagonal Matriz Confusion Dividido por la Suma de su Columnas')
        res = np.array(conf_mat.apply(lambda x: x/sum(x))).diagonal()
        if box == "nn":
            logging.info(f'\n {res} \n \n \n')
            return res.reshape((1, res.size))
        logging.info(f'\n {res} \n \n \n')
        return res

    def read_results(self,path, index_label):
        res_df = pd.read_csv(path)
        res_df.index=[index_label]
        res_df = res_df.drop([".pred_class"], axis=1)
        res_df.rename(columns=lambda x: x.split("_")[-1], inplace=True)
        return res_df




    @staticmethod
    def get_unique_elements(self,elements: list)-> set:
        """
        Recibe una lista con las posibles categorías arrojadas por los modulos\n
        de clasificación y retorna un conjuto de las categorias sin repetidos.\n
        Parametros:\n
        elements: lista que contiene las posibles categorías.\n
        Retorna:\n
        Un conjunto que contiene las categorías sin repetir\n
        """
        try:
            uniques = set()# Se instancia un conjunto vacio
            for element in elements:# Se recorren los elementos de la lista
                uniques.update(element.keys())# Se agregan las llaves de los elementos de la lista al conjunto
            return uniques
        except Exception as i:
            logging.error('Decision Maker get_unique_elements: Error '+str(i))

    def add_area_to_db(self,areas: list):
        """
        Recibe una lista con las posibles áreas y verifica cuales no se encuentran en la base
        de datos SQLite y las agrega.\n
        Parametros:\n
        areas: lista con las posibles áreas predichas por los modulos de clasificación.
        """
        try:
            sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
            conn = sqlite.db_connection()
            # Vuelve los registros devueltos por la base de datos en un arreglo de Numpy
            # y solo toma la segunda columna que posee el nombre de las áreas.
            areas_in_db = np.array(sqlite.select_all_area(conn))
            if not areas_in_db.size:
                # Si la tabla está vacia agrega todas las categorias
                for element in areas:
                    sqlite.insert_area(conn, element)
            else:
                # Si la tabla no está vacia verifica si hay algún elemento nuevo y lo agrega
                for element in areas:
                    if element not in areas_in_db[:,1]:
                        sqlite.insert_area(conn, element)
            conn.close()
        except Exception as i:
            logging.error('Decision Maker add_area_to_db: Error '+str(i))

    def first_filter(self,inputs: pd.DataFrame) -> dict:
        """
        Verifica si un porcentaje de las posibles áreas es mayor o igual a un porcentaje de
        confiabilidad alojado en la base de datos.
        Parametros:\n
        inputs: DataFrame con las salidas de los módulos de clasificación.
        Retorna:\n
        Un valor booleano indicando si se debe aplicar el segundo filtro.
        Un diccionario indicando el área de clasificación que decidió y
        el porcentaje de confiabilidad.
        Un valor booleano indicando si los valores pasaron el porcentaje de confiabilidad.
        """
        try:
            sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
            conn = sqlite.db_connection()
            percentage = sqlite.select_parameter(conn, "porc_conf")[2]# Obtiene el porcentaje de confiabilidad de la base de datos SQLite.
            conn.close() #Cierra la conexion existente
            indexes = np.where(inputs >= percentage)# Obtiene las posiciones de los valores mayores o iguales al porcentaje de confianza
            indexes = list(zip(indexes[0], indexes[1]))# Crea una lista con las posiciones
            if len(indexes) == 0:# Si no hay ningun valor mayor o igual al procentaje de confianza (lista vacia)
                return True, inputs, False
            elif len(indexes) == 1:# Si solo existe un valor mayor o igual al procentaje de confianza (un elemento en la lista)
                return False, {"decision":{"area": str(inputs.iloc[inputs.values >= percentage].index[0]),
                        "porc_conf": inputs.iloc[indexes[0]],"fiable": True}, "others": [] ,"message":True }, True
            else:# Si hay más de un valor mayor o igual al procentaje de confianza (más de un elemento en la lista)
                return True, inputs.iloc[inputs.values >= percentage], True
        except Exception as i:
            logging.error('Decision Maker first_filter: Error '+str(i))

    def second_filter(self,inputs: pd.DataFrame, passed_threshold: bool)-> dict:
        """
        Obtiene el promedio de los porcentajes de aquellas áreas que superen el primer
        filtro. Con el promedio mayor se definirá un rango de la siguiente forma:\n
        rango = [promedio mayor - marg_error, promedio mayor]\n
        Devolverá aquel valor que se encuentre dentro del rango, en caso de ser más de uno,
        devolverá todos los valor dentro del rango y el usuario debe escoger el área que mejor
        considere.\n
        Parametros:\n
        inputs: DataFrame con las áreas que pasaron el primer filtro.
        passed_threshold: indica si el input superó o no el umbral del primer filtro.
        Retorna:\n
        Área(s) que se encuentre(n) dentro rango definido.
        """
        try:
            # Crea un DataFrame con una única columna que contiene el promedio de la áreas
            avg_inputs = pd.DataFrame(inputs.mean(axis=1), index=inputs.index, columns=["avg"])
            sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
            conn = sqlite.db_connection()
            err_marg = sqlite.select_parameter(conn, "marg_err")[2]
            conn.close()
            allowed_range = [float(avg_inputs.max() - err_marg), float(avg_inputs.max())]# Calcula el rango
            in_range_df = avg_inputs.query(f"{allowed_range[0]} <= avg <= {allowed_range[1]}")# Aquellos valores del DataFrame que estén dentro del rango
            in_range_df = in_range_df.sort_values(by="avg", ascending=False)# Ordena los porcentajes de manera descendiente
            if (in_range_df.shape[0] == 1):# Si solo un valor existe dentro del rango
                return {"decision":{"area": in_range_df.index[0], "porc_conf": in_range_df.iloc[0, 0],"fiable": passed_threshold},
                    "others": [],"message":True}
            else:
                output_list = []
                d = {"decision": {"area": in_range_df.index[0], "porc_conf": in_range_df.iloc[0, 0],"fiable": passed_threshold},
                    "others": output_list,"message":True}
                for i, avg in enumerate(in_range_df["avg"][1:], start=1):
                    inner_dict = {"area": in_range_df.index[i], "porc_conf": avg,"fiable": passed_threshold}
                    output_list.append(inner_dict)
                d["others"] = output_list
                return d
        except Exception as i:
            logging.error('Decision Maker second_filter: Error '+str(i))
            return None

    def decision(self,inputs: pd.DataFrame)-> dict:
        """
        Recibe un DataFrame que contiene las salidas de los respectivos
        modulos de clasificación: texto, metadatos e imágenes; y determina
        a que categoría pertenece.\n
        Parametros:\n
        inputs: DataFrame con las salidas de los modulos de clasificación.\n
        Retorna:\n
        Un diccionario indicando el área de clasificación que decidió y
        el porcentaje de confiabilidad.
        """
        try:
            # Inserta aquellas áreas que no se encuentren en la base de datos.
            self.add_area_to_db(list(inputs.index))
            apply_second_filter, results, threshold = self.first_filter(inputs)
            # Verifica si el resultado del primer filtro es igual al dataframe
            # que se recibió como parametro inicialmente.
            # threshold = inputs.equals(results)
            if apply_second_filter:
                results = self.second_filter(results, threshold)
            # Actualiza la columna 'timesChosen' del área seleccionada
            sqlite = SQLiteConnection(os.path.join(self.JsonConfig.Model["RootDir"],"database.db"))
            conn = sqlite.db_connection()
            timesChosen = sqlite.select_area(conn, results["decision"]["area"])[2] + 1
            sqlite.update_area(conn, [timesChosen, results["decision"]["area"]])
            conn.close()
            logging.info('Decision Maker : Succefully')
            return results
        except Exception as i:
            logging.error('Decision Maker decision: Error '+str(i))
            return {"decision":None,"message":False}

    def input(self,MTI,Model):
        # Abre el archivo .JSON con la información de los modelos.
        with open(self.JsonConfig.Model["PathPPV"], "r") as json_file:
            models = json.load(json_file)
        logging.info("----------------------------------EJECUTANDO PPV")
        # Se recibe como parametro
        name =  Model['Name']
        path_dic = {"nn": False, "tx": False, "md": False}
        try:
            if models[name]:
            # Buscamos la red neuronal, el modelo de texto y el de metadatos
                if models[name]["neural_network"]:
                    nn = models[name]["neural_network"]
                    conf_mat_nn_path = nn["confusion_matrix"]
                    if conf_mat_nn_path:
                        path_dic["nn"] = True
                if models[name]["text_model"]:
                    conf_mat_tx_path = models[name]["text_model"]["confusion_matrix"]
                    if conf_mat_tx_path:
                        path_dic["tx"] = True
                if models[name]["metadata_model"]:
                    conf_mat_md_path = models[name]["metadata_model"]["confusion_matrix"]
                    if conf_mat_md_path:
                        path_dic["md"] = True
        
            ppv_array = []

            # Matriz de confusión NN
            if path_dic["nn"]:
                logging.info('----------------------------------Leyendo Matriz Confusion Modelo Imagen')
                conf_mat_nn = self.read_confusion_matrix(conf_mat_nn_path, nn["labels"])
                ppv_mat_nn = self.get_diagonal(conf_mat_nn, "nn")
                ppv_df_nn = pd.DataFrame(ppv_mat_nn, columns=nn["labels"], index=["neural_network"])
            # Matriz de confusión Texto
            if path_dic["tx"]:
                logging.info('----------------------------------Leyendo Matriz Confusion Modelo Texto........')
                conf_mat_tx = self.read_confusion_matrix(conf_mat_tx_path)
                ppv_array.append(self.get_diagonal(conf_mat_tx))
            # Matriz de confusión Metadata
            if path_dic["md"]:
                logging.info('----------------------------------Leyendo Matriz Confusion Modelo Metadato........')
                conf_mat_md = self.read_confusion_matrix(conf_mat_md_path)
                ppv_array.append(self.get_diagonal(conf_mat_md))


            if path_dic["tx"] and path_dic["md"]:
                ppv_df_tm = pd.DataFrame(ppv_array, columns=conf_mat_md.columns, index=["text", "metadata"])
            elif path_dic["tx"]:
                ppv_df_tm = pd.DataFrame(ppv_array, columns=conf_mat_tx.columns, index=["text"])
            elif path_dic["md"]:
                ppv_df_tm = pd.DataFrame(ppv_array, columns=conf_mat_md.columns, index=["metadata"])
            
            logging.info('----------------------------------Uniendo Diagonales de las Matrices de los modelos Obtenidos')
            if ppv_array:
                if path_dic["nn"]:
                    ppv_df = pd.concat([ppv_df_nn, ppv_df_tm]).fillna(float(0))
                else:
                    ppv_df = ppv_df_tm
            else:
                if path_dic["nn"]:
                    ppv_df = ppv_df_nn
            logging.info(f'\n {ppv_df} \n \n \n')    
            cols = ppv_df.columns.tolist()
            cols.sort()
            ppv_df = ppv_df[cols]
            logging.info('----------------------------------Ordenando las Matrices')
            logging.info(f'\n {ppv_df} \n \n \n')
            df_data = []

                # Se recibe como parametro


            logging.info('----------------------------------Leyendo Resultados Obtenidos por los Modelos')
            logging.info(MTI)    
            if MTI["Image"]:
                nn_dict_res = {}
                for i, probs in enumerate(MTI["Image"]):
                    nn_dict_res[nn["labels"][i]]=probs
                nn_res_df = pd.DataFrame(data=nn_dict_res, index=["neural_network"])
                logging.info(f'Resultado Modelo Imagen:\n {nn_res_df} \n \n \n')
                df_data.append(nn_res_df)



                # Se recibe como parametro
                #md_res_path = "/home/cristian/Desktop/webservice/web-service/debugs/55/resultados_metadata_clasificador_areas.csv"
            if MTI["Metadata"]:
                md_res_path=MTI["Metadata"]
                md_res_df = self.read_results(md_res_path, "metadata")
                logging.info(f'Resultado Modelo Metadata:\n {md_res_df} \n \n \n')
                df_data.append(md_res_df)

            # Se recibe como parametro
            #tx_res_path = "/home/cristian/Desktop/webservice/web-service/debugs/55/resultados_texto_clasificador_areas.csv"
            if MTI["Text"]:
                tx_res_path=MTI["Text"]
                tx_res_df = self.read_results(tx_res_path, "text")
                logging.info(f'Resultado Modelo Texto:\n {tx_res_df} \n \n \n')
                df_data.append(tx_res_df)

            logging.info('----------------------------------Concatenando Resultados')
            results_df = pd.concat(df_data).fillna(float(0))
            logging.info(results_df)
            cols = results_df.columns.tolist()
            cols.sort()
            results_df = results_df[cols]
            logging.info('----------------------------------Ordenando Los Resultados')
            results_proc_ppv=self.select_candidates(results_df, ppv_df).transpose()
            logging.info(f'\n {results_proc_ppv} \n \n \n')
            results_proc_ppv=self.RemoveLabels(results_proc_ppv.transpose(),name)
            logging.info(f'\n {results_proc_ppv}')
            return self.decision(results_proc_ppv)
        except Exception as i:
            logging.error('Decision Maker: Error '+str(i))
            return {"decision":None,"message":False}



    def RemoveLabels(self, Dataframe: pd.DataFrame,Model) -> pd.DataFrame:
        TypeModel=self.JsonConfig.Model['Models'][Model]['Supervision']['type']
        Labels=self.JsonConfig.Model['Models'][Model]['Supervision']['labels']
        logging.info(f'Json Configuracion labels: {Labels}')
        LabelsDataframe=Dataframe.columns.values
        logging.info(f'Dataframe Colums: {LabelsDataframe}')
        if TypeModel == "Qualification":
            if Labels:
                for labelpd in LabelsDataframe:
                    if not labelpd in Labels:
                        Dataframe=Dataframe.drop([labelpd], axis=1)
        return Dataframe.transpose()


        
