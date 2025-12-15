import numpy as np

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
