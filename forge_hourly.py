import pandas as pd
import numpy as np

def forge_hourly_consumption(forged_daily_df: pd.DataFrame, hourly_profiles: dict, noise: float = 0.05) -> pd.DataFrame:
    """
    Generate hourly consumption data for each guest based on daily forged data
    and predefined hourly profiles.

    Args:
        forged_daily_df (pd.DataFrame): Daily forged guest data.
        hourly_profiles (dict): Normalized hourly consumption profiles.
        noise (float): Optional relative noise to vary daily consumption slightly.

    Returns:
        pd.DataFrame: Hourly dataset with columns: id_huesped, id_habitacion, dia, mes, año, h0-h23, Hotel, etc.
    """
    hourly_rows = []
    
    # Assign a profile ID to each guest if not present
    if 'profile_id' not in forged_daily_df.columns:
        forged_daily_df = forged_daily_df.copy()
        profile_ids = list(hourly_profiles.keys())
        forged_daily_df['profile_id'] = np.random.choice(profile_ids, size=len(forged_daily_df))
    
    for _, row in forged_daily_df.iterrows():
        profile = np.array(hourly_profiles[row['profile_id']]['probabilidades'], dtype=float)
        
        for day_offset in range(int(row['Dias de estancia'])):
            daily_consumption = row['Consumo medio']
            hourly_consumption = daily_consumption * profile

            # Apply small random noise to each hour
            hourly_noise = np.random.uniform(-noise, noise, size=24)
            hourly_consumption = hourly_consumption * (1 + hourly_noise)

            # Adjust to ensure sum matches Consumo medio
            hourly_consumption = hourly_consumption / hourly_consumption.sum() * daily_consumption

            # Create row dict
            hourly_row = {
                'id_huesped': row['id_huesped'],
                'id_habitacion': row['id_habitacion'],
                'dia': int(row['Dia inicio']) + day_offset,
                'mes': row['Mes'],
                'año': row['Año'],
                'Hotel': row['Hotel'],
            }
            # Add hourly columns
            for h in range(24):
                hourly_row[f'h{h}'] = hourly_consumption[h]
            
            hourly_rows.append(hourly_row)
    
    hourly_df = pd.DataFrame(hourly_rows)
    return hourly_df