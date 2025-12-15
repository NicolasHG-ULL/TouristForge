import argparse
import os
import pandas as pd
import json
import zipfile
from datetime import datetime

from multiprocessing import Pool, cpu_count

from utils.aux import  normalize_df, normalize_probabilities, redistribute_importance
from utils.correlation import calculate_correlation
from utils.theorical_importance import calculate_theorical_importance

from forge_daily import forge_daily_consumption
from forge_hourly import forge_hourly_consumption
from modelling import train_and_evaluate_models

from utils.paths import DATASET_PATH, FORGED_DAILY_PATH, DIST_DAILY_PATH, RULES_PATH, FORGED_HOURLY_PATH, DIST_HOURLY_PATH
from utils.paths import PREFIX_DAILY_ZIP, PREFIX_HOURLY_ZIP, PREFIX_FORGED_CSV, PREFIX_DIST_JSON, PREFIX_RULES_JSON
from utils.io import load_daily_zip, save_daily_to_zip, save_hourly_to_zip, save_experiment_results

ONE_HOTEL = 'Costa Adeje Gran Hotel'
CORR_THRESHOLD=0.8
VIF_THRESHOLD=10

def main(args):

    ### FORGE SECTION -- DAILY

    if(args.mode == 'forge_daily'):
        data_df = pd.read_csv(os.path.join(DATASET_PATH, args.data))
        
        with open(os.path.join(DIST_DAILY_PATH, args.dist), 'r') as file:
            distributions = json.load(file)

        with open(os.path.join(RULES_PATH, args.rules), 'r') as file:
            rules = json.load(file)

        ### Synthetic data
        noise_daily = 0.05

        # Filter the DataFrame for a specific hotel
        hotel_df = data_df[data_df['Hotel'] == ONE_HOTEL]  # Just one hotel

        # Normalizar distribuciones
        norm_dist = normalize_probabilities(distributions)

        # Forjar datos sintéticos diarios
        forged_df = forge_daily_consumption(hotel_df, norm_dist, rules, noise_daily)

        info = {
            'daily_index': os.path.join(FORGED_DAILY_PATH, f"{PREFIX_DAILY_ZIP}{args.daily_index:04d}.zip"),
            'num_guests': len(forged_df['id_huesped'].unique()),
            'total_stay_days': int(forged_df['Dias de estancia'].sum()),
            'dist_file': args.dist,
            'rules_file': args.rules,
            'date_generated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'noise_daily': noise_daily,
        }

        # Guardar resultados en ZIP
        save_daily_to_zip(forged_df, distributions, rules, info, folder=FORGED_DAILY_PATH)


    ### FORGE SECTION -- hourly
    if(args.mode == 'forge_hourly'):
        forged_data_df, _, _ = load_daily_zip(FORGED_DAILY_PATH, args.daily_index)

        with open(os.path.join(DIST_HOURLY_PATH, args.profiles), 'r') as file:
            profiles = json.load(file)
        
        for key, profile in profiles.items():
            if len(profile['probabilidades']) != 24:
                raise ValueError(f"Hourly profile '{key}' must have 24 probabilities, got {len(profile['probabilidades'])}.")

        norm_dist = normalize_probabilities(profiles)

        noise_daily = 0.1
        forged_hourly_df = forge_hourly_consumption(forged_data_df, norm_dist, noise_daily)

        info = {
            'forged_daily_index': os.path.join(FORGED_DAILY_PATH, f"{PREFIX_DAILY_ZIP}{args.daily_index:04d}.zip"),
            'profiles_file': os.path.join(DIST_HOURLY_PATH, args.profiles),
            'num_guests': len(forged_hourly_df['id_huesped'].unique()),
            'num_rows': len(forged_hourly_df),
            'date_generated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'noise_daily': noise_daily,
        }

        save_hourly_to_zip(forged_hourly_df, profiles, info, FORGED_HOURLY_PATH)



    ### MODELLING SECTION

    if(args.mode == 'modelling'):
        
        # Load forged daily data from ZIP using the new utility function
        forged_data_df, forged_dist, rules = load_daily_zip(FORGED_DAILY_PATH, args.daily_index)

        # Load the original dataset
        data_df = pd.read_csv(os.path.join(DATASET_PATH, args.data))

        print(f"[INFO] Using daily forged ZIP index: {args.daily_index}")

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
            'forged_data_file': os.path.join('forged', 'daily', f"{PREFIX_DAILY_ZIP}{args.daily_index:04d}.zip"),
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
    
        save_experiment_results(info, model_storage, importance_combined_normalized, eliminated_vars)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--mode',
        choices=['forge_daily', 'forge_daily_parallel', 'forge_hourly', 'modelling'],
        type=str,
        help="Available modes: forge (daily), forge_hourly (hourly consumption), modelling."
    )
    parser.add_argument("--data", type=str, default="default.csv", help="Specifies the name of the CSV file located in the 'data/dataset' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument("--dist", type=str, default="default.json", help="Specifies the name of the JSON file containing data daily distributions located in the 'data/dist/daily' folder. Defaults to 'default.json' if not provided.")
    parser.add_argument("--rules", type=str, default="default.json", help="Specifies the name of the JSON file containing consumption rules located in the 'data/rules' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument("--profiles", type=str, default="default.json", help="Specifies the name of the JSON file containing hourly consumption profiles located in the 'data/dist/hourly' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument(
    "-i",
    "--daily_index",
    type=int,
    default=1,
    help="Index of the daily forged ZIP to be used as input. "
         "For example, 1 → TouristForge_0001.zip. "
         "Used by hourly forge and modelling modes."
    )
    args = parser.parse_args()

    main(args)