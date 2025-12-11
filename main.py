import argparse
import os
import pandas as pd
import json
import zipfile
from datetime import datetime

from multiprocessing import Pool, cpu_count

from utils.aux import  generate_dictionaries, normalize_df, normalize_probabilities, redistribute_importance
from utils.correlation import calculate_correlation
from utils.theorical_importance import calculate_theorical_importance

from forge import forge_guests
from modelling import train_and_evaluate_models

from utils.paths import RESULTS_DIR,DATASET_PATH,DIST_DAILY_PATH,RULES_PATH,FORGED_DAILY_PATH,FORGED_HOURLY_PATH,DIST_HOURLY_PATH,PREFIX_DAILY,PREFIX_HOURLY
from utils.io import save_daily_to_zip, save_hourly_to_zip, save_experiment_results

ONE_HOTEL = 'Costa Adeje Gran Hotel'
CORR_THRESHOLD=0.8
VIF_THRESHOLD=10

def forge_and_save(args):
    """
    Generates and saves a synthetic guest dataset.

    This function processes a single set of input arguments to generate
    a forged guest DataFrame using `forge_guests` and saves it as a
    daily ZIP file. It is designed to be used both for sequential
    execution and as a target function for parallel execution with
    `multiprocessing.Pool.map`.

    Args:
        args (tuple): A tuple containing (hotel_df, distribution, rules, index)
            - hotel_df (pd.DataFrame): DataFrame filtered for a single hotel.
            - distribution (dict): Daily distribution for this iteration.
            - rules (dict): Consumption adjustment rules.
            - index (int): Index used to name the output ZIP.
    """
    hotel_df, dist, rules = args
    
    # Normalize distibution probabilities
    norm_dist = normalize_probabilities(dist)

    # Forge the guest DataFrame based on the current distribution
    forged_df = forge_guests(hotel_df, norm_dist, rules)
    
    # Save the forged DataFrame and distribution to a ZIP file
    save_daily_to_zip(forged_df, dist, rules, folder=FORGED_DAILY_PATH, prefix=PREFIX_DAILY)

def main(args):

    ### FORGE SECTION -- DAILY

    if(args.mode == 'forge' or args.mode == 'forge_parallel'):
        data_df = pd.read_csv(os.path.join(DATASET_PATH, args.data))
        
        with open(os.path.join(DIST_DAILY_PATH, args.dist), 'r') as file:
            distributions = json.load(file)

        with open(os.path.join(RULES_PATH, args.rules), 'r') as file:
            rules = json.load(file)

        ### Synthetic data

        # Filter the DataFrame for a specific hotel
        hotel_df = data_df[data_df['Hotel'] == ONE_HOTEL]  # Just one hotel

        if(args.mode == 'forge'):
            args_list = [hotel_df, distributions, rules]
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
        zip_filename = os.path.join(FORGED_DAILY_PATH, f"TouristForge_{args.index:04d}.zip")
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
            'forged_data_file': os.path.join('forged', f"{PREFIX_DAILY}{args.index:04d}.zip"),
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
        choices=['forge', 'forge_parallel', 'forge_hourly', 'modelling'],
        type=str,
        help="Available modes: forge (daily), forge_parallel (daily, multi-core), forge_hourly (hourly consumption), modelling."
    )
    parser.add_argument("--data", type=str, default="default.csv", help="Specifies the name of the CSV file located in the 'data/dataset' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument("--dist", type=str, default="default.json", help="Specifies the name of the JSON file containing data daily distributions located in the 'data/dist/daily' folder. Defaults to 'default.json' if not provided.")
    parser.add_argument("--rules", type=str, default="default.json", help="Specifies the name of the JSON file containing consumption rules located in the 'data/rules' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument("--profiles", type=str, default="default.json", help="Specifies the name of the JSON file containing hourly consumption profiles located in the 'data/dist/hourly' folder. Defaults to 'default.csv' if not provided.")
    parser.add_argument(
        "--daily_index",
        type=int,
        default=1,
        help="Index of the daily forged ZIP (e.g., 1 → TouristForge_0001.zip) used as input for the hourly forge."
    )
    parser.add_argument("--index", type=int, default=1, help="Specifies the index of the Zip file to be used for modeling. The file should be located in the 'data/forged/daily' folder. Defaults to index 1 if not provided.")
    args = parser.parse_args()

    main(args)