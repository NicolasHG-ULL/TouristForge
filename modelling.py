import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, AdaBoostRegressor
from sklearn.linear_model import Ridge, Lasso, BayesianRidge
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from statsmodels.stats.outliers_influence import variance_inflation_factor
import numpy as np

def train_and_evaluate_models(data, corr_threshold=0.8, vif_threshold=10):
    """
    Train multiple models to predict ‘Average consumption’, applying correlation thresholds and VIFs 
    to remove highly correlated and multicollinear features.

    Args:
        data: A DataFrame containing the dataset with features and the target variable ‘Average Consumption’.
        corr_threshold: Correlation threshold to remove highly correlated variables.
        vif_threshold: Variance Inflation Factor (VIF) threshold to remove multicollinear features.

    Returns:
        importance_df: DataFrame with the importance of the features for each trained model.
        eliminated_vars: Dictionary with the eliminated variables and the variables with which they are correlated or their VIF.
        model_storage: Dictionary with the trained models and the scalers used.
    """


    # Variables used to predict 'Consumo medio'
    features = ['Dias de estancia']
    categorical_features = ['sexo','nacionalidad','edad','tipo_habitacion','uso_instalaciones','viaje','comparte_habitacion']

    # Convert categorical variables to dummy variables (one-hot encoding)
    data_encoded = pd.get_dummies(data, columns=categorical_features, drop_first=False)

    # Convertir solo columnas booleanas a 0 y 1
    for col in data_encoded.columns:
        if data_encoded[col].dtype == 'bool':
            data_encoded[col] = data_encoded[col].astype(int)

    # Define X and y
    X = data_encoded[features + [col for col in data_encoded.columns if col.startswith(tuple(categorical_features))]]
    y = data_encoded['Consumo medio']

    # Make a copy of X to avoid the SettingWithCopyWarning
    X = X.copy()

    # Ensure there are no NaNs or infinite values
    if not np.isfinite(X).all().all():
        print("Cleaning data: replacing NaN and inf values.")
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        X.dropna(inplace=True)

    eliminated_vars = {'correlation': {}, 'VIF': {}}  # To track eliminated variables and their correlated variables

    # Remove highly correlated features based on correlation threshold
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    for col in upper.columns:
        if any(upper[col] > corr_threshold):
            # Find the most correlated feature
            correlated_with = upper.index[upper[col] > corr_threshold].tolist()
            eliminated_vars['correlation'][col] = {'correlated_with': correlated_with}
            print(f'Eliminating {col} due to high correlation with {correlated_with}')
            X.drop(col, axis=1, inplace=True)  # Drop the variable

    # Remove multicollinear features based on VIF threshold
    while True:
        vif = pd.DataFrame()
        vif['Variable'] = X.columns
        vif['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

        if vif['VIF'].max() > vif_threshold:
            max_vif_var = vif.sort_values(by='VIF', ascending=False).iloc[0]['Variable']
            print(f'Eliminating {max_vif_var} due to high VIF: {vif["VIF"].max()}')
            vif_value = vif.loc[vif['Variable'] == max_vif_var, 'VIF'].values[0]
            # Convertir a string, manejando el caso de Infinity
            if np.isinf(vif_value):
                vif_value = 'Infinity'
            eliminated_vars['VIF'][max_vif_var] = {'VIF': str(vif_value)}
            X.drop(max_vif_var, axis=1, inplace=True)  # Drop the variable
        else:
            break

    # Scale numerical variables
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()

    scaled_values = scaler_X.fit_transform(X[features])
    X.loc[:, features] = scaled_values.astype(np.int64)
    y = scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten()

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        'RandomForest': RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42),
        'AdaBoost': AdaBoostRegressor(n_estimators=100, random_state=42),
        'Ridge': Ridge(alpha=1.0, random_state=42),
        'Lasso': Lasso(alpha=0.1, random_state=42),
        #'NaiveBayes': GaussianNB(),  # Para clasificación, no regresión, pero puede adaptarse
        'BayesianRidge': BayesianRidge(),  # Alternativa bayesiana para regresión
        'XGBoost': xgb.XGBRegressor(n_estimators=100, random_state=42)
    }

    # Crear un DataFrame para almacenar las importancias
    importance_df = pd.DataFrame({'Feature': X.columns})

    # Diccionario para guardar los modelos y escaladores
    model_storage = {
        'models': {},
        'scalers': {'X_scaler': scaler_X, 'y_scaler': scaler_y},
        'error_metrics': {}
    }

    # Entrenar cada modelo y extraer las importancias
    for name, model in models.items():
        model.fit(X_train, y_train)

        # Guardar el modelo en el diccionario
        model_storage['models'][name] = model

        # Calculo de RMSE y MAE
        # Predicciones y valores reales
        y_pred = model.predict(X_test)
        y_true = y_test

        # Calcular RMSE y MAE
        rmse = root_mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)

        # Guardar en el diccionario de resultados
        model_storage['error_metrics'][name] = {'RMSE': rmse, 'MAE': mae}

        # Calculo de importancias
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_)  # Usamos el valor absoluto de los coeficientes
        else:
            importance = np.nan  # En caso de que el modelo no tenga importancias
        
        importance_df[name] = importance

    # Ordenar el DataFrame por la importancia del Random Forest
    importance_df = importance_df.sort_values(by='RandomForest', ascending=False)

    return importance_df, eliminated_vars, model_storage
