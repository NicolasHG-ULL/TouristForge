import pandas as pd
import numpy as np


def forge_hourly_consumption(
    forged_daily_df: pd.DataFrame,
    hourly_profiles: dict,
    noise_daily: float = 0.1
) -> pd.DataFrame:
    """
    Generate hourly consumption data from daily forged data using predefined
    hourly consumption profiles.

    The total consumption per guest is preserved. Daily variability is introduced
    by slightly varying the daily consumption while keeping the overall total
    constant. Hourly values strictly follow the selected profile.

    Args:
        forged_daily_df (pd.DataFrame): Daily forged guest dataset.
        hourly_profiles (dict): Hourly profiles dictionary. Each profile must
            contain a 'probabilidades' list of 24 values summing to 1.
        noise_daily (float): Relative noise applied to daily consumption
            distribution across the stay.

    Returns:
        pd.DataFrame: Hourly dataset with one row per guest per day and
        columns h0–h23.
    """

    hourly_rows = []

    # Assign a profile to each guest if not already present
    if 'profile_id' not in forged_daily_df.columns:
        forged_daily_df = forged_daily_df.copy()
        profile_ids = list(hourly_profiles.keys())
        forged_daily_df['profile_id'] = np.random.choice(
            profile_ids, size=len(forged_daily_df)
        )

    for _, row in forged_daily_df.iterrows():

        stay_days = int(row['Dias de estancia'])
        total_consumption = row['Consumo total']

        # Get hourly profile
        profile = np.array(
            hourly_profiles[row['profile_id']]['probabilidades'],
            dtype=float
        )

        # Safety check (should already be normalized)
        profile = profile / profile.sum()

        # Distribute total consumption across days with small variability
        daily_weights = np.ones(stay_days)
        daily_noise = np.random.uniform(
            -noise_daily, noise_daily, size=stay_days
        )
        daily_weights = daily_weights * (1 + daily_noise)
        daily_weights = daily_weights / daily_weights.sum()

        daily_consumptions = total_consumption * daily_weights

        for day_offset, daily_consumption in enumerate(daily_consumptions):

            hourly_consumption = daily_consumption * profile

            hourly_row = {
                'id_huesped': row['id_huesped'],
                'id_habitacion': row['id_habitacion'],
                'dia': int(row['Dia inicio']) + day_offset,
                'mes': row['Mes'],
                'año': row['Año'],
                'Hotel': row['Hotel'],
            }

            for h in range(24):
                hourly_row[f'h{h}'] = hourly_consumption[h]

            hourly_rows.append(hourly_row)

    return pd.DataFrame(hourly_rows)