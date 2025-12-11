import numpy as np

##### TODO: edit function to adapt the new json format
def generate_dictionaries(distribution):
    # Initialize an empty list to store all the generated dictionaries
    dictionaries = []

    # Iterate over all combinations using nested loops
    for sex_index in range(len(distribution["sexo"]["Hombre"])):
        # Use the same index for all seasons in "nacionalidad"
        for nationality_index in range(len(distribution["nacionalidad"]["invierno"]["España"])):
            for age_index in range(len(distribution["edad"]["Menor de 16 años"])):
                for room_type_index in range(len(distribution["tipo_habitacion"]["España"]["Estándar"])):
                    for facility_use_index in range(len(distribution["uso_instalaciones"]["Suite"]["Si"])):
                        for travel_index in range(len(distribution["viaje"]["Negocios"])):
                            for share_room_index in range(len(distribution["comparte_habitacion"]["Si"])):
                                # Create a new dictionary for the current combination
                                current_combination = {
                                    "sexo": {
                                        "Hombre": distribution["sexo"]["Hombre"][sex_index],
                                        "Mujer": distribution["sexo"]["Mujer"][sex_index]
                                    },
                                    "nacionalidad": {
                                        # Use the same index for all seasons
                                        "invierno": {
                                            "España": distribution["nacionalidad"]["invierno"]["España"][nationality_index],
                                            "Reino Unido": distribution["nacionalidad"]["invierno"]["Reino Unido"][nationality_index],
                                            "Alemania": distribution["nacionalidad"]["invierno"]["Alemania"][nationality_index],
                                            "Francia": distribution["nacionalidad"]["invierno"]["Francia"][nationality_index],
                                            "Italia": distribution["nacionalidad"]["invierno"]["Italia"][nationality_index],
                                            "Otros": distribution["nacionalidad"]["invierno"]["Otros"][nationality_index]
                                        },
                                        "primavera_verano": {
                                            "España": distribution["nacionalidad"]["primavera_verano"]["España"][nationality_index],
                                            "Reino Unido": distribution["nacionalidad"]["primavera_verano"]["Reino Unido"][nationality_index],
                                            "Alemania": distribution["nacionalidad"]["primavera_verano"]["Alemania"][nationality_index],
                                            "Francia": distribution["nacionalidad"]["primavera_verano"]["Francia"][nationality_index],
                                            "Italia": distribution["nacionalidad"]["primavera_verano"]["Italia"][nationality_index],
                                            "Otros": distribution["nacionalidad"]["primavera_verano"]["Otros"][nationality_index]
                                        },
                                        "otoño": {
                                            "España": distribution["nacionalidad"]["otoño"]["España"][nationality_index],
                                            "Reino Unido": distribution["nacionalidad"]["otoño"]["Reino Unido"][nationality_index],
                                            "Alemania": distribution["nacionalidad"]["otoño"]["Alemania"][nationality_index],
                                            "Francia": distribution["nacionalidad"]["otoño"]["Francia"][nationality_index],
                                            "Italia": distribution["nacionalidad"]["otoño"]["Italia"][nationality_index],
                                            "Otros": distribution["nacionalidad"]["otoño"]["Otros"][nationality_index]
                                        }
                                    },
                                    "edad": {
                                        "Menor de 16 años": distribution["edad"]["Menor de 16 años"][age_index],
                                        "De 16 a 24 años": distribution["edad"]["De 16 a 24 años"][age_index],
                                        "De 25 a 30 años": distribution["edad"]["De 25 a 30 años"][age_index],
                                        "De 31 a 45 años": distribution["edad"]["De 31 a 45 años"][age_index],
                                        "De 46 a 60 años": distribution["edad"]["De 46 a 60 años"][age_index],
                                        "Mayores de 60 años": distribution["edad"]["Mayores de 60 años"][age_index]
                                    },
                                    "tipo_habitacion": {
                                        "España": {
                                            "Estándar": distribution["tipo_habitacion"]["España"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["España"]["Suite"][room_type_index]
                                        },
                                        "Reino Unido": {
                                            "Estándar": distribution["tipo_habitacion"]["Reino Unido"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["Reino Unido"]["Suite"][room_type_index]
                                        },
                                        "Alemania": {
                                            "Estándar": distribution["tipo_habitacion"]["Alemania"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["Alemania"]["Suite"][room_type_index]
                                        },
                                        "Francia": {
                                            "Estándar": distribution["tipo_habitacion"]["Francia"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["Francia"]["Suite"][room_type_index]
                                        },
                                        "Italia": {
                                            "Estándar": distribution["tipo_habitacion"]["Italia"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["Italia"]["Suite"][room_type_index]
                                        },
                                        "Otros": {
                                            "Estándar": distribution["tipo_habitacion"]["Otros"]["Estándar"][room_type_index],
                                            "Suite": distribution["tipo_habitacion"]["Otros"]["Suite"][room_type_index]
                                        }
                                    },
                                    "uso_instalaciones": {
                                        "Suite": {
                                            "Si": distribution["uso_instalaciones"]["Suite"]["Si"][facility_use_index],
                                            "No": distribution["uso_instalaciones"]["Suite"]["No"][facility_use_index]
                                        },
                                        "Estándar": {
                                            "Si": distribution["uso_instalaciones"]["Estándar"]["Si"][facility_use_index],
                                            "No": distribution["uso_instalaciones"]["Estándar"]["No"][facility_use_index]
                                        }
                                    },
                                    "viaje": {
                                        "Negocios": distribution["viaje"]["Negocios"][travel_index],
                                        "Placer": distribution["viaje"]["Placer"][travel_index]
                                    },
                                    "comparte_habitacion": {
                                        "Si": distribution["comparte_habitacion"]["Si"][share_room_index],
                                        "No": distribution["comparte_habitacion"]["No"][share_room_index]
                                    }
                                }

                                # Add the current combination to the list
                                dictionaries.append(current_combination)

    # Return the list of generated dictionaries
    return dictionaries

def normalize_probabilities(dist):
    """
    Normalize probability distributions in the given dictionary.
    Works for daily distributions (dicts) and hourly profiles (lists of 24 values).

    - If a profile already sums to 1, it is left unchanged.
    - If a profile does not sum to 1, a warning is printed and it is normalized.
    """
    for key in dist:
        probs = dist[key].get('probabilidades', None)
        if probs is None:
            continue

        if isinstance(probs, dict):
            # Handle possible conditions
            if 'condicion' in dist[key]:
                for condition_key in probs:
                    total = sum(probs[condition_key].values())
                    if not np.isclose(total, 1.0):
                        print(f"[WARNING] Profile '{key}' condition '{condition_key}' does not sum to 1 ({total}). Normalizing automatically.")
                        if total > 0:
                            probs[condition_key] = {k: v / total for k, v in probs[condition_key].items()}
            else:
                total = sum(probs.values())
                if not np.isclose(total, 1.0):
                    print(f"[WARNING] Profile '{key}' does not sum to 1 ({total}). Normalizing automatically.")
                    if total > 0:
                        dist[key]['probabilidades'] = {k: v / total for k, v in probs.items()}

        elif isinstance(probs, list):
            total = sum(probs)
            if not np.isclose(total, 1.0):
                print(f"[WARNING] Profile '{key}' does not sum to 1 ({total}). Normalizing automatically.")
                if total > 0:
                    dist[key]['probabilidades'] = [v / total for v in probs]

        else:
            raise TypeError(f"Unknown type for 'probabilidades' in {key}: {type(probs)}")
    
    return dist

def redistribute_importance(eliminated_vars, df):
    # Verificar que la primera columna es 'Feature'
    if df.columns[0] != 'Feature':
        raise ValueError("La primera columna del DataFrame debe ser 'Feature'.")

    # Hacer una copia del DataFrame para evitar modificar el original
    df = df.copy()

    # Obtener las columnas numéricas, excluyendo 'Feature'
    numeric_cols = df.columns[1:]

    # Lista para almacenar las columnas que serán eliminadas
    columns_to_remove = []

    # Variabels eliminadas por correlacion
    for col, info in eliminated_vars['correlation'].items():
        # Verificar si la variable eliminada está en el DataFrame
        if col in df['Feature'].values:
            # Sumar los valores de la columna eliminada a las columnas correlacionadas
            for correlated_col in info.get('correlated_with', []):
                if correlated_col in df['Feature'].values:
                    # Sumar los valores de las columnas numéricas
                    for numeric_col in numeric_cols:
                        # Usar .loc de manera explícita
                        df.loc[df['Feature'] == correlated_col, numeric_col] += df.loc[df['Feature'] == col, numeric_col].values[0]

            # Agregar a la lista de columnas a eliminar
            columns_to_remove.append(col)

    # Variabels eliminadas por VIF
    for col, info in eliminated_vars['VIF'].items():
        # Verificar si la variable eliminada está en el DataFrame
        if col in df['Feature'].values:
            # Agregar a la lista de columnas a eliminar
            columns_to_remove.append(col)

    # Eliminar las columnas que se marcaron para ser eliminadas
    df = df[~df['Feature'].isin(columns_to_remove)]

    # Actualizar las columnas numéricas después de la eliminación
    numeric_cols = df.columns[1:]

    return df

def normalize_df(df):
    # Copiar el DataFrame para evitar modificar el original
    df_normalized = df.copy()
    
    # Iterar sobre las columnas, omitiendo la primera
    for col in df_normalized.columns[1:]:
        column_sum = df_normalized[col].sum()
        if column_sum != 0:  # Evitar división por cero en columnas de suma cero
            df_normalized[col] = df_normalized[col] / column_sum
    
    return df_normalized
