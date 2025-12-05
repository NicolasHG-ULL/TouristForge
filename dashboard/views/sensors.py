import datetime
import streamlit as st
import pandas as pd
import plotly.express as px

def get_sensor_entities(conn):
    query = """
    SELECT DISTINCT entity_id
    FROM states_meta
    WHERE entity_id LIKE 'sensor.%'
    ORDER BY entity_id;
    """
    return pd.read_sql(query, conn)

def get_sensor_history(conn, sensor_id, start_time=None, end_time=None):
    query = f"""
    SELECT s.last_updated_ts, s.state
    FROM states s
    JOIN states_meta sm ON s.metadata_id = sm.metadata_id
    WHERE sm.entity_id = ?
    AND s.state NOT IN ('unknown', 'unavailable')
    {f"AND s.last_updated_ts >= {start_time.timestamp()}" if start_time else ""}
    {f"AND s.last_updated_ts <= {end_time.timestamp()}" if end_time else ""}
    ORDER BY s.last_updated_ts;
    """
    df = pd.read_sql_query(query, conn, params=(sensor_id,))
    df['last_updated_ts'] = pd.to_datetime(df['last_updated_ts'], unit='s')
    df['state'] = pd.to_numeric(df['state'], errors='coerce')
    return df.dropna()

def calcular_rango(rango):
    ahora = datetime.datetime.now()
    hoy = ahora.date()

    if rango == "Última hora":
        start = ahora - datetime.timedelta(hours=1)
        end = ahora
    elif rango == "Hoy":
        start = datetime.datetime.combine(hoy, datetime.time.min)
        end = ahora
    elif rango == "Ayer":
        ayer = hoy - datetime.timedelta(days=1)
        start = datetime.datetime.combine(ayer, datetime.time.min)
        end = datetime.datetime.combine(ayer, datetime.time.max)
    elif rango == "Últimos 7 días":
        start = ahora - datetime.timedelta(days=7)
        end = ahora
    elif rango == "Últimos 14 días":
        start = ahora - datetime.timedelta(days=14)
        end = ahora
    elif rango == "Últimos 30 días":
        start = ahora - datetime.timedelta(days=30)
        end = ahora
    elif rango == "Último año":
        start = ahora - datetime.timedelta(days=365)
        end = ahora
    else:  
        start = None
        end = None

    return start, end

def mostrar_grafico_interactivo(df):
    fig = px.line(df, x=df.index, y="state", title="Histórico del sensor")
    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Valor",
        xaxis_rangeslider_visible=True,
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

def sensors_view(conn):
    st.title("Sensores de Home Assistant")

    sensor_df = get_sensor_entities(conn)
    sensor_list = sensor_df['entity_id'].tolist()

    if not sensor_list:
        st.warning("No se encontraron sensores.")
        return

    selected_sensor = st.selectbox("Selecciona un sensor", sensor_list)

    if selected_sensor:
        st.write(f"Histórico para: **{selected_sensor}**")

        opciones_rango = [
            "Última hora",
            "Hoy",
            "Ayer",
            "Últimos 7 días",
            "Últimos 14 días",
            "Últimos 30 días",
            "Último año",
            "Personalizado"
        ]
        rango_seleccionado = st.selectbox("Selecciona un rango de fechas", opciones_rango, index=4)

        if rango_seleccionado == "Personalizado":
            hoy = datetime.date.today()
            inicio_default = hoy - datetime.timedelta(days=7)
            date_range = st.date_input("Selecciona rango de fechas", [inicio_default, hoy])

            if len(date_range) != 2:
                st.warning("Por favor, selecciona ambas fechas del rango.")
                return

            start_date, end_date = date_range
            start_dt = datetime.datetime.combine(start_date, datetime.time.min)
            end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        else:
            start_dt, end_dt = calcular_rango(rango_seleccionado)

        history_df = get_sensor_history(conn, selected_sensor, start_dt, end_dt)

        if history_df.empty:
            st.info("Este sensor no tiene datos disponibles en el rango seleccionado.")
        else:
            df = history_df.set_index("last_updated_ts").sort_index()
            df.index = df.index.round('5min')
            df = df.groupby(df.index).mean()

            freq = "5min"

            min_fecha = df.index.min()
            max_fecha = df.index.max()

            inicio = max(start_dt, min_fecha)
            fin = min(end_dt, max_fecha)

            if inicio > fin:
                st.warning("No hay datos en el rango de fechas seleccionado.")
                return

            full_range = pd.date_range(start=inicio, end=fin, freq=freq)
            df = df.reindex(full_range)
            df.index.name = "timestamp"

            mostrar_grafico_interactivo(df)

            if df["state"].isna().any():
                st.warning("⚠️ Hay intervalos sin datos en este rango de tiempo.")
