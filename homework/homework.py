#
# En este dataset se desea pronosticar el precio de vhiculos usados. El dataset
# original contiene las siguientes columnas:
#
# - Car_Name: Nombre del vehiculo.
# - Year: Año de fabricación.
# - Selling_Price: Precio de venta.
# - Present_Price: Precio actual.
# - Driven_Kms: Kilometraje recorrido.
# - Fuel_type: Tipo de combustible.
# - Selling_Type: Tipo de vendedor.
# - Transmission: Tipo de transmisión.
# - Owner: Número de propietarios.
#
# El dataset ya se encuentra dividido en conjuntos de entrenamiento y prueba
# en la carpeta "files/input/".
#
# Los pasos que debe seguir para la construcción de un modelo de
# pronostico están descritos a continuación.
#
#
# Paso 1.
# Preprocese los datos.
# - Cree la columna 'Age' a partir de la columna 'Year'.
#   Asuma que el año actual es 2021.
# - Elimine las columnas 'Year' y 'Car_Name'.
#
#
# Paso 2.
# Divida los datasets en x_train, y_train, x_test, y_test.
#
#
# Paso 3.
# Cree un pipeline para el modelo de clasificación. Este pipeline debe
# contener las siguientes capas:
# - Transforma las variables categoricas usando el método
#   one-hot-encoding.
# - Escala las variables numéricas al intervalo [0, 1].
# - Selecciona las K mejores entradas.
# - Ajusta un modelo de regresion lineal.
#
#
# Paso 4.
# Optimice los hiperparametros del pipeline usando validación cruzada.
# Use 10 splits para la validación cruzada. Use el error medio absoluto
# para medir el desempeño modelo.
#
#
# Paso 5.
# Guarde el modelo (comprimido con gzip) como "files/models/model.pkl.gz".
# Recuerde que es posible guardar el modelo comprimido usanzo la libreria gzip.
#
#
# Paso 6.
# Calcule las metricas r2, error cuadratico medio, y error absoluto medio
# para los conjuntos de entrenamiento y prueba. Guardelas en el archivo
# files/output/metrics.json. Cada fila del archivo es un diccionario con
# las metricas de un modelo. Este diccionario tiene un campo para indicar
# si es el conjunto de entrenamiento o prueba. Por ejemplo:
#
# {'type': 'metrics', 'dataset': 'train', 'r2': 0.8, 'mse': 0.7, 'mad': 0.9}
# {'type': 'metrics', 'dataset': 'test', 'r2': 0.7, 'mse': 0.6, 'mad': 0.8}
#

import pandas as pd
import gzip
import json
import os
import zipfile
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, median_absolute_error

# Paso 1: Preprocesamiento del dataset
def transformar_datos(df):
    copia = df.copy()
    copia['Age'] = 2021 - copia['Year']
    copia = copia.drop(columns=['Year', 'Car_Name'])
    return copia

# Paso 2: Separar variables dependientes e independientes
def dividir_dataset(df):
    objetivo = df['Present_Price']
    caracteristicas = df.drop(columns=['Present_Price'])
    return caracteristicas, objetivo

# Paso 3: Crear pipeline de procesamiento y modelo
def construir_flujo():
    cat_vars = ['Fuel_Type', 'Selling_type', 'Transmission']
    num_vars = ['Selling_Price', 'Driven_kms', 'Owner', 'Age']

    transformador = ColumnTransformer(
        transformers=[
            ('categoricas', OneHotEncoder(), cat_vars),
            ('numericas', MinMaxScaler(), num_vars)
        ]
    )

    modelo = Pipeline([
        ('transformador', transformador),
        ('selector', SelectKBest(f_regression)),
        ('modelo_lineal', LinearRegression())
    ])
    
    return modelo

# Paso 4: Búsqueda de hiperparámetros óptimos
def ajustar_modelo(flujo, X_entrenamiento, y_entrenamiento):
    grid_params = {
        'selector__k': [4, 5, 6, 7, 8, 9, 10, 11],
        'modelo_lineal__fit_intercept': [True, False],
    }

    validador = GridSearchCV(
        flujo,
        param_grid=grid_params,
        cv=10,
        scoring='neg_mean_absolute_error',
        n_jobs=-1
    )

    validador.fit(X_entrenamiento, y_entrenamiento)
    return validador

# Paso 5: Guardar modelo entrenado
def guardar_modelo(objeto, ruta_salida):
    with gzip.open(ruta_salida, 'wb') as archivo:
        pd.to_pickle(objeto, archivo)

# Paso 6: Calcular métricas de desempeño
def evaluar_modelo(modelo, X_entrenamiento, y_entrenamiento, X_prueba, y_prueba):
    resultados = []

    pred_train = modelo.predict(X_entrenamiento)
    resultados.append({
        'type': 'metrics',
        'dataset': 'train',
        'r2': r2_score(y_entrenamiento, pred_train),
        'mse': mean_squared_error(y_entrenamiento, pred_train),
        'mad': median_absolute_error(y_entrenamiento, pred_train)
    })

    pred_test = modelo.predict(X_prueba)
    resultados.append({
        'type': 'metrics',
        'dataset': 'test',
        'r2': r2_score(y_prueba, pred_test),
        'mse': mean_squared_error(y_prueba, pred_test),
        'mad': median_absolute_error(y_prueba, pred_test)
    })

    return resultados

def exportar_metricas(diccionarios, ruta):
    with open(ruta, 'w') as salida:
        for fila in diccionarios:
            salida.write(json.dumps(fila) + '\n')

# Función principal
def ejecutar_modelo():
    os.makedirs("files/models", exist_ok=True)
    os.makedirs("files/output", exist_ok=True)
    
    with zipfile.ZipFile('files/input/train_data.csv.zip', 'r') as zf_train:
        nombre_train = zf_train.namelist()[0]
        with zf_train.open(nombre_train) as archivo:
            datos_train = pd.read_csv(archivo)

    with zipfile.ZipFile('files/input/test_data.csv.zip', 'r') as zf_test:
        nombre_test = zf_test.namelist()[0]
        with zf_test.open(nombre_test) as archivo:
            datos_test = pd.read_csv(archivo)

    datos_train = transformar_datos(datos_train)
    datos_test = transformar_datos(datos_test)

    X_train, y_train = dividir_dataset(datos_train)
    X_test, y_test = dividir_dataset(datos_test)

    flujo_modelo = construir_flujo()
    modelo_entrenado = ajustar_modelo(flujo_modelo, X_train, y_train)

    guardar_modelo(modelo_entrenado, 'files/models/model.pkl.gz')
    evaluaciones = evaluar_modelo(modelo_entrenado, X_train, y_train, X_test, y_test)
    exportar_metricas(evaluaciones, 'files/output/metrics.json')

if __name__ == "__main__":
    ejecutar_modelo()
