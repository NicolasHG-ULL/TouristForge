import streamlit as st
import pandas as pd

def show_experiment_info(experiment_info):
    """
    Muestra la información del experimento en formato tabular a partir de un JSON cargado.
    
    Args:
        experiment_info (dict): Diccionario con la información del experimento.
    """
    try:
        # Desglosar los datos en tablas
        st.subheader("Información del Experimento")
        general_info = {
            "ID del Experimento": experiment_info["experiment_id"],
            "Fecha": experiment_info["experiment_date"],
            "Archivo de Datos Original": experiment_info["input_data_file"],
            "Archivo de Datos Forjados": experiment_info["forged_data_file"],
            "Descripción": experiment_info["experiment_description"]
        }
        st.dataframe(
            pd.DataFrame(general_info.items(), columns=["Detalle", "Información"]),
            hide_index=True,
            use_container_width=True
            )

        # Mostrar versiones de librerías
        st.subheader("Versiones de Librerías")
        library_versions = pd.DataFrame(
            experiment_info["library_versions"].items(),
            columns=["Librería", "Versión"]
        )
        st.dataframe(library_versions,
            hide_index=True,
            use_container_width=True
            )

        # Mostrar parámetros del experimento
        st.subheader("Parámetros del Experimento")
        experiment_parameters = pd.DataFrame(
            experiment_info["experiment_parameters"].items(),
            columns=["Parámetro", "Valor"]
        )
        st.dataframe(experiment_parameters,
            hide_index=True,
            use_container_width=True
            )

        # Mostrar detalles del procesamiento de datos
        st.subheader("Procesamiento de Datos")
        data_processing = pd.DataFrame(
            experiment_info["data_processing"].items(),
            columns=["Proceso", "Detalle"]
        )
        st.dataframe(data_processing,
            hide_index=True,
            use_container_width=True
            )
    
    except KeyError as e:
        st.error(f"Clave faltante en el JSON: {e}")
    except Exception as e:
        st.error(f"Error al procesar la información: {e}")


def show_eliminated_vars(eliminated_vars):
    # Procesar el JSON para convertir la parte de "correlation" en un DataFrame
    correlation_data = []
    for var, details in eliminated_vars.get('correlation', {}).items():
        for correlated_var in details['correlated_with']:
            correlation_data.append({'Variable eliminada': var, 'Correlated With': correlated_var})
    
    correlation_df = pd.DataFrame(correlation_data)

    # Procesar la parte de "VIF" en un DataFrame
    vif_data = []
    for var, vif in eliminated_vars.get('VIF', {}).items():
        vif_data.append({'Variable eliminada': var, 'VIF': vif['VIF']})
    
    vif_df = pd.DataFrame(vif_data)

    # Mostrar la tabla de eliminaciones por correlación
    st.subheader("Eliminaciones por Correlación")
    st.dataframe(correlation_df, hide_index=True, use_container_width=True)

    # Mostrar la tabla de eliminaciones por VIF
    st.subheader("Eliminaciones por VIF")
    st.dataframe(vif_df, hide_index=True, use_container_width=True)

def show_sources(source_data):
    # Mostrar las distribuciones
    st.subheader("Distribuciones")
    st.json(source_data.get("distributions", {}))  # Mostrar solo distribuciones, por si está vacío

    # Mostrar las reglas
    st.subheader("Reglas")
    st.json(source_data.get("rules", {}))  # Mostrar solo reglas, por si está vacío