import os
import pandas as pd
import sqlite3

# Función para obtener los directorios de resultados
def get_results_directories(base_path="results"):
    """Obtiene los nombres de directorios dentro de 'results'."""
    try:
        return sorted([d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))])
    except FileNotFoundError:
        return []

# Función genérica para cargar un CSV desde una ruta específica
def load_csv(file_path):
    """Carga un archivo CSV desde una ruta especificada."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        return None

import json

def load_json(file_path):
    """
    Carga un archivo JSON y devuelve su contenido como un diccionario.
    
    Args:
        file_path (str): Ruta al archivo JSON.
    
    Returns:
        dict: Contenido del archivo JSON como un diccionario.
    
    Raises:
        FileNotFoundError: Si el archivo no existe.
        json.JSONDecodeError: Si el archivo no es un JSON válido.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError as e:
        raise FileNotFoundError(f"El archivo {file_path} no existe.") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"El archivo {file_path} no contiene un JSON válido.") from e

def get_db_connection(db_path: str):
    return sqlite3.connect(db_path)