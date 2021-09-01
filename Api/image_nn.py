import os
import torch
import logging
import json
from .config import Config
from torchvision import datasets, transforms

class ImageNN():
    """
    Clase para ejecutar los modelos de inferencia de imagenes.\n
    Atributos:\n
    model_path: ruta del modelo que se desea utilizar.
    img_dir: ruta del directorio donde se tienen las imagenes a predecir.
    """

    def __init__(self, model_path, img_dir,Model):
        self.JsonConfig=Config()
        with open(self.JsonConfig.Model["PathPPV"], "r") as json_file:
            models = json.load(json_file)
        
        dataset_mean = models[Model]["neural_network"]["dataset_mean"]
        dataset_std = models[Model]["neural_network"]["dataset_std"]
        data_transforms = {
            "Temp": transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(dataset_mean, dataset_std)
            ]),
        }
        self.img_dir = img_dir
        image_datasets = {x: datasets.ImageFolder(os.path.join(self.img_dir, x), data_transforms[x]) for x in ["Temp"]}
        self.model = torch.load(model_path)
        self.image_tensor = {x: torch.utils.data.DataLoader(image_datasets[x], batch_size=16, shuffle=True, num_workers=8) for x in ["Temp"]}

    def predict(self):
        predictions, real_labels, out_probs = [], [], []
        #predictions=[]
        #labels_1505 = ["1505.07.01.01.I", "1505.13.01.01.I", "1505.14.01.01.I", "1505.38.07.01.I", "1505.38.09.01.I"]
        sm = torch.nn.Softmax() # Definir la Softmax
        with torch.no_grad():
            for i, (inputs, labels) in enumerate(self.image_tensor['Temp']):
                # inputs = inputs.to(device)
                #labels = labels.to(device)
                outputs = self.model(inputs)
                _, preds = torch.max(outputs, 1)
                probabilities = sm(outputs) # Pasar valores de salida a la probabilidad usando la red Softmax
                predictions.extend(list(preds.tolist()))
                real_labels.extend(list(labels.tolist()))
                out_probs.extend(list(probabilities.tolist()))
                """logging.info(f"Predicciones")
                logging.info(predictions)
                logging.info("Probabilidades")
                logging.info("\t Lista que retorna")
                logging.info(out_probs)
                for i, prob in enumerate(out_probs):
                    logging.info(f"Posición {i} de la lista de probabilidades")
                    logging.info(prob)
                    logging.info(f"La suma de las probabilidades para la posición {i} es: {sum(prob)}")
                    logging.info(f"El mayor es: {max(prob)}")
                logging.info(f"Etiquetas reales")
                logging.info(real_labels)
                """
        return  out_probs[0]

"""if __name__ == "__main__":
    path = "/home/jose/trained_models_acuacar/1505/model_1.pkl"
    #img = "/home/jose/data_acuacar/1505/acuacar_1505/val/1505.07.01.01.I/CU1740960.tif"
    data_dir = "/home/jose/data_acuacar/server_backend_test"
    labels_1505 = ["1505.07.01.01.I", "1505.13.01.01.I", "1505.14.01.01.I", "1505.38.07.01.I", "1505.38.09.01.I"]
    inn = ImageNN(path, data_dir)
bvn
    print(labels_1505[inn.predict()[0]])"""