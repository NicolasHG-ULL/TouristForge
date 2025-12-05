import pandas as pd
from scipy.stats import pointbiserialr


def filter_data(data_df, eliminated_vars):
    """
    Elimina las columnas del DataFrame según el diccionario de eliminated_vars.

    Parameters:
    - data_df (pd.DataFrame): El DataFrame que contiene los datos.
    - eliminated_vars (dict): Diccionario con las variables a eliminar. Las claves son los nombres de las columnas.

    Returns:
    - pd.DataFrame: El DataFrame filtrado sin las columnas eliminadas.
    """
    # Hacer una copia del DataFrame para evitar modificar el original
    filtered_df = data_df.copy()

    # Recorrer las claves del diccionario (columnas a eliminar)
    for col in eliminated_vars.keys():
        # Verificar si la columna está en el DataFrame
        if col in filtered_df.columns:
            # Eliminar la columna
            filtered_df.drop(columns=[col], inplace=True)
    
    return filtered_df



# Función para codificar las variables en one-hot
def one_hot_encode(data):
    
    categorical_features = ['sexo','nacionalidad','edad','tipo_habitacion','uso_instalaciones','viaje','comparte_habitacion']

    # Convert categorical variables to dummy variables (one-hot encoding)
    data_encoded = pd.get_dummies(data, columns=categorical_features, drop_first=False)
    
    return data_encoded

# Función para calcular la importancia
def pointbiserialr_correlation(data):
    
    consumo_medio = data['Consumo medio']

    # Filtrar solo las columnas que son binarias (solo contienen 0 y 1)
    binary_columns = data.columns[(data.isin([0, 1]).all()) & (data.nunique() == 2)]

    # Lista para almacenar los resultados
    results = []

    # Calcular la correlación punto-biserial para cada columna binaria
    for column in binary_columns:
        correlation, p_value = pointbiserialr(data[column], consumo_medio)
        # Almacenar el resultado en una lista
        results.append({
            'Feature': column,
            'Correlation': abs(correlation),
            #'P_value': p_value
        })

    # Crear un DataFrame a partir de la lista de resultados
    results_df = pd.DataFrame(results)

    # Normalizar la columna de correlación para que su suma sea 1
    total_corr = results_df['Correlation'].sum()
    
    # Solo normalizar si la suma total no es cero
    if total_corr > 0:
        results_df['Correlation'] = results_df['Correlation'] / total_corr


    return results_df

def calculate_correlation(forged_data_df, eliminated_vars=None):

    encoded_data = one_hot_encode(forged_data_df)

    if(eliminated_vars):
        encoded_data = filter_data(encoded_data, eliminated_vars)

    # Calcular la importancia de las variables usando Pearson
    correlation_df = pointbiserialr_correlation(encoded_data)

    #print(correlation_df)

    # Guardar el DataFrame como un archivo CSV
    #correlation_df.to_csv(os.path.join('results', f"correlation_{SERIAL_NUMBER}.csv"), index=False)

    return correlation_df