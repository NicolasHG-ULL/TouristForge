import pandas as pd

def calculate_theorical_importance(rules, distribution, df):
    """
    Calculates the theoretical importance for each individual value based on the provided rules.

    :param rules: Dictionary with the impacts (rules) for each individual value of the variables.
    :param distribution: Dictionary of distributions to calculate the probabilities of each value.
    :param df: DataFrame in case any variable is not in the distribution and needs to be calculated from the DataFrame.
    :return: Dictionary with the calculated importance for each individual value.
    """
    importances = {}

    for category, category_impact in rules.items():
        # Get the probability of the current category using the calculate_probability function
        category_probability = calculate_probability(category, distribution, df)

        for value, impact in category_impact.items():
            # Check if the probability is a list (i.e., if it's conditional)
            if isinstance(category_probability[value], list):
                # If it's a list, multiply the rule by each probability and sum the results
                importance = sum(abs(impact) * prob for prob in category_probability[value])
            else:
                # If it's not conditional, just multiply the impact by the unique probability
                importance = abs(impact) * category_probability[value]
            
            # Store the calculated importance in the dictionary using the value as the key
            importances[f"{category}_{value}"] = importance

    importance_df = pd.DataFrame(list(importances.items()), columns=['Feature', 'Theoretical_Importance'])

    return importance_df

def calculate_probability(category, distribution, df):
    """
    Calculates the probability for each value of a given category, considering possible conditioning.

    :param category: The category to calculate the probability for (e.g., 'nationality').
    :param distribution: Dictionary of distributions to look up the probabilities.
    :param df: DataFrame in case the category is not in the distributions.
    :return: Dictionary with the probabilities for each value, as lists of probabilities if they are conditional.
    """
    if category in distribution:
        category_dist = distribution[category]
        
        # Check if it's a conditioned distribution
        if 'condicion' in category_dist:
            # Get the probability of the condition
            condition = category_dist['condicion']
            condition_probability = calculate_probability(condition, distribution, df)

            # Structure to store the combined probability
            combined_probability = {}

            # For each value of the category, get the conditioned probabilities
            for condition_value, condition_p in condition_probability.items():
                for value, prob in category_dist['probabilidades'][condition_value].items():
                    # Multiply the probability of the condition by the specific probability of the value
                    if value not in combined_probability:
                        combined_probability[value] = []

                    # Check if 'condition_p' is a list
                    if isinstance(condition_p, list):
                        # If it's a list, multiply each element of 'condition_p' with the probability
                        for _, prob_condition in enumerate(condition_p):
                            combined_probability[value].append(prob * prob_condition)
                    else:
                        # If it's not a list, multiply directly
                        combined_probability[value].append(prob * condition_p)

            return combined_probability
        
        else:
            # If it's not conditioned, return the probability directly
            return category_dist['probabilidades']
    else:
        # If the category is not in the distribution, calculate the probability from the DataFrame
        return calculate_probability_from_df(category, df)


def calculate_probability_from_df(column, df):
    """
    Calculates the probability of unique values in a DataFrame column.

    :param column: Name of the column for which the distribution is calculated.
    :param df: DataFrame containing the data.
    :return: Dictionary with unique values of the column as keys and their proportion as values.
    """
    # Calculate the frequency of each unique value in the column
    count = df[column].value_counts()
    total = len(df)  # Total number of rows

    # Calculate the distribution by dividing each count by the total
    distribution = {value: frequency / total for value, frequency in count.items()}
    
    return distribution