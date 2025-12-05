import pandas as pd
import os
import argparse

import plotly.graph_objects as go


def main(args):

    importance = pd.read_csv(os.path.join('results', f"importance_{args.index:04d}.csv"))

    # Eliminar la columna 'p_value' si existe
    if 'P_value' in importance.columns:
        importance = importance.drop(columns=['P_value'])

    # Crear un gráfico de barras
    fig1 = go.Figure()

    # Iterar sobre todas las columnas, excepto 'Feature'
    for col in importance.columns:
        if col != 'Feature':
            fig1.add_trace(go.Bar(
                x=importance['Feature'],
                y=importance[col],
                name=col.replace('_', ' '),  # Cambiar '_' por espacios en los nombres
            ))

    # Actualizar el diseño del gráfico
    fig1.update_layout(
        title='Comparación de Importancias y Correlación',
        xaxis_title='Features',
        yaxis_title='Importancia',
        barmode='group'  # Agrupar las barras
    )

    # Mostrar el gráfico
    fig1.show()


    
    # Crear un DataFrame para almacenar los errores relativos
    error_relative_df = pd.DataFrame()
    error_relative_df['Feature'] = importance['Feature']
    
    # Calcular el error relativo (en porcentaje) respecto a Theorical_Importance
    for col in importance.columns:
        if col not in ['Feature', 'Theoretical_Importance', 'Correlation']:
            error_relative_df[f"{col}"] = (
                (importance[col] - importance['Theoretical_Importance']).abs() / importance['Theoretical_Importance']
            ) * 100  # Multiplicar por 100 para convertir a porcentaje
    
    # Gráfico del error relativo respecto a Theorical_Importance
    fig2 = go.Figure()
    for col in error_relative_df.columns[1:]:  # Excluir la columna 'Feature'
        if col != 'Feature':
            fig2.add_trace(go.Bar(
                x=error_relative_df['Feature'],
                y=error_relative_df[col],
                name=col.replace('_', ' ')
            ))

    fig2.update_layout(
        title='Error Relativo (%) de Importancias con Respecto a Theorical Importance',
        xaxis_title='Features',
        yaxis_title='Error Relativo (%)',
        barmode='group'
    )
    fig2.show()

    # Calcular el error relativo (en porcentaje) respecto a Correlation
    error_relative_df = pd.DataFrame()
    error_relative_df['Feature'] = importance['Feature']
    
    for col in importance.columns:
        if col not in ['Feature', 'Theoretical_Importance', 'Correlation']:
            error_relative_df[f"{col}"] = (
                (importance[col] - importance['Correlation']).abs() / importance['Correlation']
            ) * 100  # Multiplicar por 100 para convertir a porcentaje
    
    # Gráfico del error relativo respecto a Correlation
    fig3 = go.Figure()
    for col in error_relative_df.columns[1:]:  # Excluir la columna 'Feature'
        if col != 'Feature':
            fig3.add_trace(go.Bar(
                x=error_relative_df['Feature'],
                y=error_relative_df[col],
                name=col.replace('_', ' ')
            ))

    fig3.update_layout(
        title='Error Relativo (%) de Importancias con Respecto a Correlation',
        xaxis_title='Features',
        yaxis_title='Error Relativo (%)',
        barmode='group'
    )
    fig3.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--index", type=int, default=1, help="Specifies the index of the Zip file to be used for ploting. The file should be located in the 'data' folder. Defaults to index 1 if not provided.")
    args = parser.parse_args()

    main(args)