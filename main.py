import argparse
import os
import pandas as pd
import json
import zipfile
from datetime import datetime
import joblib

from multiprocessing import Pool, cpu_count

from utils.aux import  generate_dictionaries, normalize_df, normalize_probabilities, redistribute_importance
from utils.correlation import calculate_correlation
from utils.theorical_importance import calculate_theorical_importance

from forge import forge_guests
from modelling import train_and_evaluate_models

ONE_HOTEL = 'Costa Adeje Gran Hotel'
RESULTS_DIR = 'results'
CORR_THRESHOLD=0.8
VIF_THRESHOLD=10

DATASET_PATH = 'data/dataset'
DIST_PATH = 'data/dist'
RULES_PATH = 'data/rules'
FORGED_PATH = 'data/forged'

def save_to_zip(dataframe, dist, rules, index):
    # Create filenames using the specified format
    csv_filename = os.path.join(FORGED_PATH, f"forged_{index:04d}.csv")
    dist_filename = os.path.join(FORGED_PATH,f"dist_{index:04d}.json")
    rules_filename = os.path.join(FORGED_PATH,f"rules_{index:04d}.json")
    zip_filename = os.path.join(FORGED_PATH,f"TouristForge_{index:04d}.zip")

    # Save the DataFrame to a CSV file
    dataframe.to_csv(csv_filename, index=False)

    # Save the distribution dictionary to a JSON file
    with open(dist_filename, 'w') as json_file:
        json.dump(dist, json_file)

    # Save the rules dictionary to a JSON file
    with open(rules_filename, 'w') as json_file:
        json.dump(rules, json_file)

    # Create a ZIP file containing both files
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        # Write CSV file to the ZIP without the directory structure
        zip_file.write(csv_filename, arcname=f"forged_{index:04d}.csv")
        # Write Dist JSON file to the ZIP without the directory structure
        zip_file.write(dist_filename, arcname=f"dist_{index:04d}.json")
        # Write Rules JSON file to the ZIP without the directory structure
        zip_file.write(rules_filename, arcname=f"rules_{index:04d}.json")

    # Optionally, remove the individual files after zipping
    os.remove(csv_filename)
    os.remove(dist_filename)
    os.remove(rules_filename)

def forge_and_save(args):
    """
    Procesa los archivos de entrada y sintetiza un dataset
    """
    hotel_df, dist, rules, index = args
    
    # Normalize distibution probabilities
    norm_dist = normalize_probabilities(dist)

    # Forge the guest DataFrame based on the current distribution
    forged_df = forge_guests(hotel_df, norm_dist, rules)
    
    # Save the forged DataFrame and distribution to a ZIP file
    save_to_zip(forged_df, dist, rules, index)

def save_modelling_results(info, model_storage, importances_df, eliminated_vars):
    ## CREAR DIRECTORIO

    # Contar cuántos directorios existen en 'results/'
    existing_dirs = [d for d in os.listdir(RESULTS_DIR) if os.path.isdir(os.path.join(RESULTS_DIR, d))]
    # Obtener el número del próximo directorio
    next_dir_number = len(existing_dirs) + 1
    # Formatear el nombre del nuevo directorio con ceros a la izquierda
    new_dir_name = f"results_{next_dir_number:04d}"
    # Crear el nuevo directorio
    new_dir_path = os.path.join(RESULTS_DIR, new_dir_name)
    os.makedirs(new_dir_path)
    subdirs = ['info', 'scaler', 'model', 'importance']
    for subdir in subdirs:
        os.makedirs(os.path.join(new_dir_path, subdir))

    ## GUARDAR INFO
    # Ruta del directorio 'info' dentro de 'results_XXXX'
    info_dir = os.path.join(new_dir_path, 'info')
    info['experiment_id'] = f"exp_{next_dir_number:04d}"

    # Guardar 'info' como JSON
    with open(os.path.join(info_dir, 'info.json'), 'w') as f_info:
        json.dump(info, f_info, indent=4)

    # Guardar 'eliminated_vars' como JSON
    with open(os.path.join(info_dir, 'eliminated_vars.json'), 'w') as f_eliminated_vars:
        json.dump(eliminated_vars, f_eliminated_vars, indent=4)

    # Guardar 'error_metrics' como JSON
    with open(os.path.join(info_dir, 'error_metrics.json'), 'w') as f_errors:
        json.dump(model_storage['error_metrics'], f_errors, indent=4)

    ## GUARDAR SCALER Y MODELS

    # Guardar scalers en el directorio 'scaler'
    scaler_dir = os.path.join(new_dir_path, 'scaler')
    for scaler_name, scaler in model_storage['scalers'].items():
        scaler_filename = os.path.join(scaler_dir, f'{scaler_name}.pkl')
        joblib.dump(scaler, scaler_filename)
        
    # Guardar modelos en el directorio 'model'
    model_dir = os.path.join(new_dir_path, 'model')
    for model_name, model in model_storage['models'].items():
        model_filename = os.path.join(model_dir, f'{model_name}.pkl')
        joblib.dump(model, model_filename)

    ## GUARDAR IMPORTANCES
    importance_dir = os.path.join(new_dir_path, 'importance')
    importances_df.to_csv(os.path.join(importance_dir, f"importance.csv"), index=False)

    print(f"Se han guardado correctamente toda la información realcionada con el experimento exp_{next_dir_number:04d}")

def main(args):

    ### FORGE SECTION

    if(args.mode == 'forge' or args.mode == 'forge_parallel'):
        data_df = pd.read_csv(os.path.join(DATASET_PATH, args.data))
        
        with open(os.path.join(DIST_PATH, args.dist), 'r') as file:
            distributions = json.load(file)

        with open(os.path.join(RULES_PATH, args.rules), 'r') as file:
            rules = json.load(file)

        ### Synthetic data

        # Filter the DataFrame for a specific hotel
        hotel_df = data_df[data_df['Hotel'] == ONE_HOTEL]  # Just one hotel

        if(args.mode == 'forge'):
            args_list = [hotel_df, distributions, rules, args.index]
            forge_and_save(args_list)

        elif(args.mode == 'forge_parallel'):

            # Generate the dictionaries
            distributions_list = generate_dictionaries(distributions)

            # Prepare arguments for each iteration
            args_list = [(hotel_df, dist, rules, index) for index, dist in enumerate(distributions_list, start=1)]

            # Use all the available cores
            num_procesos = cpu_count()

            # Create a processes pool and execute
            with Pool(num_procesos) as pool:
                pool.map(forge_and_save, args_list)

    ### MODELLING SECTION

    if(args.mode == 'modelling'):

        # Construct the zip file name and the internal csv file name
        zip_filename = os.path.join(FORGED_PATH, f"TouristForge_{args.index:04d}.zip")
        csv_filename = f"forged_{args.index:04d}.csv"
        dist_filename = f"dist_{args.index:04d}.json"
        rules_filename = f"rules_{args.index:04d}.json"

        data_df = pd.read_csv(os.path.join(DATASET_PATH, args.data))

        # Open the zip file and read the CSV and JSON files it contains
        with zipfile.ZipFile(zip_filename, 'r') as z:
            with z.open(csv_filename) as f:
                forged_data_df = pd.read_csv(f)
            with z.open(dist_filename) as f:
                forged_dist = json.load(f)  
            with z.open(rules_filename) as f:
                rules = json.load(f)

        print(f"Using file from zip: {zip_filename}, internal file: {csv_filename}")
        
        ## Case where the forged_df has only one hotel

        forged_df = forged_data_df[forged_data_df['Hotel'] == ONE_HOTEL]
        hotel_df = data_df[data_df['Hotel'] == ONE_HOTEL]

        importance_df, eliminated_vars, model_storage = train_and_evaluate_models(forged_df)
        correlation = calculate_correlation(forged_df, eliminated_vars)
        theorical_importance = calculate_theorical_importance(rules, forged_dist, hotel_df)

        updated_importance = redistribute_importance(eliminated_vars, theorical_importance)

        importance_combined = pd.merge(importance_df, updated_importance, on='Feature', how='inner')
        importance_combined = pd.merge(importance_combined, correlation, on='Feature', how='inner')

        importance_combined_normalized = normalize_df(importance_combined)

        # Build experiment information dictionary
        info = {
            'experiment_id': '',
            'experiment_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Fecha y hora del experimento
            'input_data_file': os.path.join('data', args.data),
            'forged_data_file': os.path.join('forged', f"TouristForge_{args.index:04d}.zip"),
            'experiment_description': "Generación y análisis de datos sintéticos de turistas.",
            'library_versions': {
                'scikit-learn': '1.5.2',
                'xgboost': '2.1.3',
                'pandas': '2.2.2'
            },
            'experiment_parameters': {
                'corr_threshold': CORR_THRESHOLD,
                'vif_threshold': VIF_THRESHOLD
            },
            'data_processing': {
                'missing_values': 'Eliminados',
                'scaling': 'Sí',
                'encoding': 'One-Hot'
            }
        }
    
        save_modelling_results(info, model_storage, importance_combined_normalized, eliminated_vars)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="default.csv", help="Specifies the name of the CSV file located in the 'data/dataset' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument("--dist", type=str, default="default.json", help="Specifies the name of the JSON file containing data distributions located in the 'data/dist' folder. Defaults to 'default.json' if not provided.")
    parser.add_argument("--rules", type=str, default="default.json", help="Specifies the name of the CSV file containing consumption rules located in the 'data/rules' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument(
        '--mode',
        choices=['forge', 'forge_parallel', 'modelling'],
        help="Specify the mode of operation. Choices are 'forge', 'forge_parallel', and 'modelling'."
    )
    parser.add_argument("--index", type=int, default=1, help="Specifies the index of the Zip file to be used for modeling. The file should be located in the 'data/forged' folder. Defaults to index 1 if not provided.")
    args = parser.parse_args()

    main(args)