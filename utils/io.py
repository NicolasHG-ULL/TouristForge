import os
import json
import pandas as pd
import zipfile
import joblib

from utils.paths import RESULTS_DIR, FORGED_DAILY_PATH, FORGED_HOURLY_PATH
from utils.paths import RESULTS_PREFIX, PREFIX_DAILY_ZIP, PREFIX_HOURLY_ZIP, PREFIX_DIST_JSON, PREFIX_RULES_JSON, PREFIX_FORGED_CSV

def get_next_index(path, prefix="", ext="", is_dir=False):
    """
    Returns the next available numerical index based on existing files or directories
    in a specified folder.

    This is useful to automatically generate sequential filenames or directory names,
    avoiding overwriting existing data.

    Args:
        path (str): Path to the folder where files or directories are checked.
        prefix (str): Expected prefix of the files or directories (e.g., 'daily_' or 'results_').
        ext (str): Expected file extension (e.g., '.zip'). Leave empty for directories.
        is_dir (bool): If True, searches for directories; if False, searches for files.

    Returns:
        int: The next available index (starting at 1 if no matching items exist).
    """
    os.makedirs(path, exist_ok=True)

    items = os.listdir(path)
    numbers = []

    for name in items:
        full_path = os.path.join(path, name)

        if is_dir and not os.path.isdir(full_path):
            continue
        if not is_dir and not os.path.isfile(full_path):
            continue

        if not name.startswith(prefix):
            continue

        if ext and not name.endswith(ext):
            continue

        try:
            num = name.replace(prefix, "").replace(ext, "")
            numbers.append(int(num))
        except ValueError:
            continue

    return max(numbers) + 1 if numbers else 1

def load_daily_zip(folder, index):
    """
    Load a forged **daily** ZIP file containing CSV, distributions JSON, and rules JSON.

    Args:
        folder (str): Path to the folder where the ZIPs are stored.
        index (int): Index of the ZIP file (used in naming).

    Returns:
        tuple: (forged_df, dist_dict, rules_dict)
    """
    zip_filename = os.path.join(folder, f"{PREFIX_DAILY_ZIP}{index:04d}.zip")
    csv_filename = f"{PREFIX_FORGED_CSV}{index:04d}.csv"
    dist_filename = f"{PREFIX_DIST_JSON}{index:04d}.json"
    rules_filename = f"{PREFIX_RULES_JSON}{index:04d}.json"

    with zipfile.ZipFile(zip_filename, 'r') as z:
        with z.open(csv_filename) as f:
            forged_df = pd.read_csv(f)
        with z.open(dist_filename) as f:
            dist_dict = json.load(f)
        with z.open(rules_filename) as f:
            rules_dict = json.load(f)

    print(f"[INFO] Loaded ZIP: {zip_filename}, internal CSV: {csv_filename}")
    return forged_df, dist_dict, rules_dict

def save_daily_to_zip(dataframe, dist, rules, folder=FORGED_DAILY_PATH):
    """
    Save a forged daily dataset in a ZIP file along with its distributions and rules.

    Each ZIP file will contain:
        - CSV with daily guest data.
        - JSON with the distributions used.
        - JSON with the consumption rules applied.

    Args:
        dataframe (pd.DataFrame): Forged daily guest data.
        dist (dict): Distributions used to forge the data.
        rules (dict): Consumption rules applied to guests.
        index (int): ZIP index (for consistent file naming).

    Notes:
    - CSV and JSON files are deleted after creating the ZIP.
    - The ZIP is saved in the `FORGED_DAILY_PATH` folder.
    - The ZIP name follows the pattern `daily_XXXX.zip`.
    """

    daily_index = get_next_index(
        path=FORGED_DAILY_PATH,
        prefix=PREFIX_DAILY_ZIP,
        ext=".zip",
        is_dir=False
    )

    # Create filenames using the specified format
    csv_filename = os.path.join(folder, f"{PREFIX_FORGED_CSV}{daily_index:04d}.csv")
    dist_filename = os.path.join(folder,f"{PREFIX_DIST_JSON}{daily_index:04d}.json")
    rules_filename = os.path.join(folder,f"{PREFIX_RULES_JSON}{daily_index:04d}.json")
    zip_filename = os.path.join(folder,f"{PREFIX_DAILY_ZIP}{daily_index:04d}.zip")

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
        zip_file.write(csv_filename, arcname=f"forged_{daily_index:04d}.csv")
        # Write Dist JSON file to the ZIP without the directory structure
        zip_file.write(dist_filename, arcname=f"dist_{daily_index:04d}.json")
        # Write Rules JSON file to the ZIP without the directory structure
        zip_file.write(rules_filename, arcname=f"rules_{daily_index:04d}.json")

    # Optionally, remove the individual files after zipping
    os.remove(csv_filename)
    os.remove(dist_filename)
    os.remove(rules_filename)

    print(f"[INFO] Guardado ZIP diario: {zip_filename}")


def save_hourly_to_zip(hourly_df: pd.DataFrame, distributions: dict, info: dict, folder=FORGED_HOURLY_PATH, prefix=PREFIX_HOURLY_ZIP):
    """
    Save the hourly forged dataset to a ZIP file along with its distributions and metadata.

    Each ZIP will contain:
        - CSV with hourly guest data.
        - JSON with the hourly distributions used.
        - JSON with metadata info.

    Args:
        hourly_df (pd.DataFrame): Hourly forged guest data.
        distributions (dict): Hourly distributions used.
        info (dict): Metadata information about the generation.
        folder (str): Folder to save the ZIP.
        prefix (str): Prefix for the ZIP file name (e.g., 'hourly_').
    """

    # Determine next available index for ZIP
    hourly_index = get_next_index(path=folder, prefix=prefix, ext=".zip", is_dir=False)

    # Filenames
    csv_filename = os.path.join(folder, f"{PREFIX_FORGED_CSV}{hourly_index:04d}.csv")
    dist_filename = os.path.join(folder, f"{PREFIX_DIST_JSON}{hourly_index:04d}.json")
    info_filename = os.path.join(folder, f"info_{hourly_index:04d}.json")
    zip_filename = os.path.join(folder, f"{prefix}{hourly_index:04d}.zip")

    # Save individual files
    hourly_df.to_csv(csv_filename, index=False)
    with open(dist_filename, 'w') as f:
        json.dump(distributions, f, indent=4)
    with open(info_filename, 'w') as f:
        json.dump(info, f, indent=4)

    # Create ZIP
    with zipfile.ZipFile(zip_filename, 'w') as zip_file:
        zip_file.write(csv_filename, arcname=os.path.basename(csv_filename))
        zip_file.write(dist_filename, arcname=os.path.basename(dist_filename))
        zip_file.write(info_filename, arcname=os.path.basename(info_filename))

    # Remove individual files after zipping
    os.remove(csv_filename)
    os.remove(dist_filename)
    os.remove(info_filename)

    print(f"[INFO] Saved hourly ZIP: {zip_filename}")

def save_experiment_results(info, model_storage, importances_df, eliminated_vars):
    """
    Save the complete results of a modelling experiment in a new directory.

    Generated directory structure:
        results_XXXX/
            ├─ info/               -> JSON with info, metrics, and deleted variables
            ├─ scaler/             -> Pickle files with the scalers used
            ├─ model/              -> Pickle files with the trained models
            └─ importance/         -> CSV with combined variable importance

    Args:
        info (dict): Dictionary with general information about the experiment.
        model_storage (dict): Dictionary with trained models and scalers.
        importances_df (pd.DataFrame): DataFrame with combined variable importance.
        eliminated_vars (list): List of variables eliminated during modelling.

    Notes:
    - The directory index is calculated automatically.
    - Use `RESULTS_DIR` and `RESULTS_PREFIX` to name the folder.
    """
    ## CREAR DIRECTORIO

    # Obtener el número del próximo directorio
    results_index = get_next_index(
        path=RESULTS_DIR,
        prefix="results_",
        is_dir=True
    )
    # Formatear el nombre del nuevo directorio con ceros a la izquierda
    new_dir_name = f"{RESULTS_PREFIX}{results_index:04d}"
    # Crear el nuevo directorio
    new_dir_path = os.path.join(RESULTS_DIR, new_dir_name)
    os.makedirs(new_dir_path)
    subdirs = ['info', 'scaler', 'model', 'importance']
    for subdir in subdirs:
        os.makedirs(os.path.join(new_dir_path, subdir))

    ## GUARDAR INFO
    # Ruta del directorio 'info' dentro de 'RESULTS_PREFIX_XXXX'
    info_dir = os.path.join(new_dir_path, 'info')
    info['experiment_id'] = f"exp_{results_index:04d}"

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

    print(f"Se han guardado correctamente toda la información realcionada con el experimento exp_{results_index:04d}")