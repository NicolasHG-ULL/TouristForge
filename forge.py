import numpy as np
import pandas as pd
from tqdm import tqdm

def forge_guests(data, dist, rules):
    """
    Generate class distributions based on the provided data and distributions.

    Args:
        data: The data used to generate the distributions.
        dist: The normalized distribution definitions for the classes.
        rules: A dictionary that defines how each variable affects consumption.

    Returns:
        A DataFrame containing synthetic guest data.
    """
    
    hotel = data.iloc[0]['Hotel']
    
    chunks = []  # List to accumulate chunks

    for _, row in tqdm(data.iterrows(), total=data.shape[0], desc=f"{hotel}: Processing Rows"):
        pax = row['Pax']
        consumption_per_pax = row['Consumo de eletricidad por Pax']
        month = row['Mes']
        year = row['Año']
        season = row['Estación']

        # Create a list to store the stay days of each guest
        stay_days = []
        total_days = 0
        while total_days < pax:
            days = np.random.randint(1, 8)
            stay_days.append(days)
            total_days += days
        if total_days > pax:
            stay_days[-1] -= total_days - pax

        n_guests = len(stay_days)

        # Temporary list for rows
        temp_rows = []

        for _ in range(n_guests):
            new_row = {
                'Mes': month,
                'Año': year,
                'Hotel': hotel,
                'Estación': season,
                'Dias de estancia': stay_days.pop(0)
            }

            # Iterate over the first-level keys in the distribution dictionary
            for key in dist:
                # Check if the current distribution key has a condition
                if 'condicion' in dist[key]:
                    # Assuming the condition is based on an attribute already in new_row
                    # For example, if the condition is on 'Sexo', we must have 'sex' in new_row
                    condition_key = dist[key]['condicion'] # Get the condition key
                    condition_value = new_row[condition_key]  # Get the value from new_row

                    # Use the condition to choose the correct probabilities
                    probabilities = dist[key]['probabilidades'][condition_value]
                    selected_value = np.random.choice(list(probabilities.keys()), p=list(probabilities.values()))
                else:
                    # No condition, use the probabilities directly
                    probabilities = dist[key]['probabilidades']
                    selected_value = np.random.choice(list(probabilities.keys()), p=list(probabilities.values()))

                # Add the selected value to new_row
                new_row[key] = selected_value
            
            # Calculate consumption and add it to the row
            new_row = forge_consumption(new_row, consumption_per_pax, rules)
            new_row_df = pd.DataFrame([new_row])
            
            # Append the row to the temporary list
            temp_rows.append(new_row_df)

        # Concatenate the temporary rows into a chunk
        chunk_df = pd.concat(temp_rows, ignore_index=True)
        chunks.append(chunk_df)

    # Concatenate all chunks into a final DataFrame
    forged_df = pd.concat(chunks, ignore_index=True)
    return forged_df

def forge_consumption(guest, mean_consumption, rules):
    """
    Calculate consumption adjustments based on the provided guest information and rules.

    Args:
        guest: A pandas Series containing the guest's data (e.g., 'Sexo', 'Nacionalidad', etc.).
        mean_consumption: The average consumption value from the original data.
        rules: A dictionary that defines how each variable affects consumption.

    Returns:
        A pandas Series containing the guest's information along with the adjusted consumption values.
    """

    # Initialize adjustment variable
    adjustment = 0

    # Iterate over the rules to apply adjustments
    for feature, effect_dict in rules.items():
        # Get the value of the current feature from the guest data, ensuring it's a scalar
        feature_value = guest[feature] if feature in guest else None  # Get the scalar value directly
        
        # Update adjustment based on the rules, defaulting to 0 if the feature value is None or not found
        adjustment += effect_dict[feature_value] if feature_value is not None else 0

    # Calculate the adjusted consumption
    average_consumption = mean_consumption * (1 + adjustment)

    # Generate a random increase within ±2.5% of the base average consumption
    random_increase = np.random.uniform(-0.025, 0.025) * average_consumption

    # Adjust the average consumption
    average_consumption += random_increase
    
    # Add the 'Consumo medio' and 'Consumo total' to the guest dictionary
    guest['Consumo medio'] = average_consumption
    guest['Consumo total'] = average_consumption * guest['Dias de estancia']  

    return guest


