import streamlit as st

from data_loader import get_results_directories, load_csv, load_json

from views.charts import show_importance_chart, show_error_chart
from views.tables import show_experiment_info, show_eliminated_vars, show_sources

# Interfaz de Streamlit
def main():
    # Cargar y mostrar el logo
    st.image("dashboard/static/logo.png", use_container_width=True)

    # Título de la aplicación
    st.title("Panel de Mandos del Experimento")
    
    # Menú lateral para elegir el directorio de experimentos
    st.sidebar.header("Selecciona un Experimento")
    experiment_dirs = get_results_directories()
    selected_experiment = st.sidebar.selectbox("Elige un directorio de experimento", experiment_dirs)

    # Menú lateral para seleccionar la sección
    st.sidebar.title("Opciones")
    selected_option = st.sidebar.radio("Selecciona una opción", ["Info", "Distribuciones y Reglas", "Error", "Variables Eliminadas", "Importancias"])

    if selected_experiment:
        if selected_option == "Info":
            data = load_json(f"results/{selected_experiment}/info/info.json")
            show_experiment_info(data)
        elif selected_option == "Distribuciones y Reglas":
            data = load_json(f"results/{selected_experiment}/info/source.json")
            show_sources(data)
        elif selected_option == "Error":
            data = load_json(f"results/{selected_experiment}/info/error_metrics.json")
            show_error_chart(data)
        elif selected_option == "Variables Eliminadas":
            data = load_json(f"results/{selected_experiment}/info/eliminated_vars.json")
            show_eliminated_vars(data)
        elif selected_option == "Importancias":
            data = load_csv(f"results/{selected_experiment}/importance/importance.csv")
            show_importance_chart(data)
    else:
        st.error("Vista no válida")

if __name__ == "__main__":
    main()
