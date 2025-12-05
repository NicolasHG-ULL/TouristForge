import plotly.express as px
import pandas as pd
import streamlit as st

def show_importance_chart(df):
    # Verificar si la columna 'Feature' existe en el DataFrame
    if 'Feature' not in df.columns:
        st.error("La columna 'Feature' no está presente en el DataFrame.")
        return
    
    # Reestructurar el DataFrame para adaptarlo al gráfico de barras agrupadas
    # Usamos melt para que todas las columnas excepto 'Feature' se conviertan en una sola columna
    df_melted = df.melt(id_vars=['Feature'], var_name='Modelo', value_name='Importancia')

    # Crear gráfico de barras agrupadas
    fig = px.bar(df_melted, 
                 x='Feature', 
                 y='Importancia', 
                 color='Modelo', 
                 title="Gráfico de Importancia de Características",
                 labels={'Importancia': 'Importancia', 'Feature': 'Características', 'Modelo': 'Modelos'},
                 height=500)

    # Cambiar el modo de las barras a 'group' para que no estén apiladas, sino al lado
    fig.update_layout(barmode='group')

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
    
def show_error_chart(error_json):
    # Convertir el JSON a un DataFrame
    df = pd.DataFrame.from_dict(error_json, orient='index').reset_index()
    df.columns = ['Modelo', 'RMSE', 'MAE']

    # Usamos melt para convertir el DataFrame en un formato largo
    df_melted = df.melt(id_vars=['Modelo'], var_name='Error', value_name='Valor')

    # Crear el gráfico de barras
    fig = px.bar(df_melted, 
                 x='Modelo', 
                 y='Valor', 
                 color='Error', 
                 title="Errores por Modelo (RMSE y MAE)",
                 labels={'Valor': 'Valor del Error', 'Modelo': 'Modelos', 'Error': 'Tipo de Error'},
                 height=500)

    # Cambiar el modo de las barras a 'group' para que no estén apiladas, sino al lado
    fig.update_layout(barmode='group')

    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)