import numpy as np
import pandas as pd
import calendar
from tqdm import tqdm

def forge_guests(data, dist, rules):
    hotel = data.iloc[0]['Hotel']
    chunks = []

    for _, row in tqdm(data.iterrows(), total=data.shape[0], desc=f"{hotel}: Processing Rows"):
        pax = row['Pax']
        consumption_per_pax = row['Consumo de eletricidad por Pax']
        month = row['Mes']
        year = row['Año']
        season = row['Estación']

        # 0. Asegurar que 'ocupacion_habitacion' está en dist
        if 'ocupacion_habitacion' not in dist:
            dist['ocupacion_habitacion'] = {
                "probabilidades": {"1": 1.0}
            }

        # 1. Separar variables compartidas y no compartidas
        # IMPORTANTE: excluir 'ocupacion_habitacion' de las individuales para que no se re-muestree por huésped
        compartidas = {k: v for k, v in dist.items() if v.get('compartido_por_habitacion', False)}
        individuales = {k: v for k, v in dist.items()
                        if not v.get('compartido_por_habitacion', False) and k != 'ocupacion_habitacion'}

        # 2. Generar habitaciones y asignar huéspedes
        huespedes = []
        id_huesped_counter = 1
        id_habitacion_counter = 1
        pax_restante = pax

        while pax_restante > 0:
            # Determinar ocupación de habitación (se toma de dist)
            opciones_keys = list(dist['ocupacion_habitacion']['probabilidades'].keys())
            opciones_probs = list(dist['ocupacion_habitacion']['probabilidades'].values())
            # np.random.choice con keys que son strings — convertir result a int
            n_ocupantes = int(np.random.choice(opciones_keys, p=opciones_probs))
            n_ocupantes = min(n_ocupantes, pax_restante)

            # 2B. Generar variables compartidas PARA LA HABITACIÓN (una sola vez)
            valores_compartidos = {}
            for key, info in compartidas.items():
                if 'condicion' in info:
                    cond_key = info['condicion']
                    # La condición se evalúa sobre la fila original o sobre valores previamente definidos de la habitación
                    # Para condiciones basadas en variables que también pueden ser compartidas, preferimos row si no existe aún
                    cond_value = row.get(cond_key) if cond_key in row.index else None
                    # Si la condicion depende de una variable base del dataset, usamos row; si depende de otra compartida se debería
                    # haber generado ya (pero en nuestro flujo compartidas se generan ahora)
                    if cond_value is None:
                        # last resort: try to use valores_compartidos (unlikely here)
                        cond_value = valores_compartidos.get(cond_key)
                    # ahora sample condicionada
                    probs_dict = info['probabilidades'][cond_value]
                    options = np.array(list(probs_dict.keys()))
                    probs = np.array(list(probs_dict.values()))
                    valores_compartidos[key] = np.random.choice(options, p=probs)
                else:
                    probs_dict = info['probabilidades']
                    options = np.array(list(probs_dict.keys()))
                    probs = np.array(list(probs_dict.values()))
                    valores_compartidos[key] = np.random.choice(options, p=probs)

            # === GENERAR dias_estancia y dia_inicio UNA vez por habitación ===
            ultimo_dia_mes = calendar.monthrange(year, month)[1]
            dias_estancia = np.random.randint(1, 8)  # mismo para todos los ocupantes de la habitación
            dia_inicio = np.random.randint(1, ultimo_dia_mes - dias_estancia + 2)

            # 3. Crear cada huésped en la habitación
            id_habitacion_str = f"{id_habitacion_counter:06d}"
            for _ in range(n_ocupantes):
                datos = {
                    "Mes": month,
                    "Año": year,
                    "Hotel": hotel,
                    "Estación": season,
                    "Dias de estancia": dias_estancia,
                    "Dia inicio": dia_inicio,
                    "id_huesped": f"{id_huesped_counter:06d}",
                    "id_habitacion": id_habitacion_str,
                    "ocupacion_habitacion": n_ocupantes
                }

                # Añadir variables compartidas (se copian iguales para todos los ocupantes)
                datos.update(valores_compartidos)

                # Generar variables individuales (excluyendo 'ocupacion_habitacion', ya puesta)
                for key, info in individuales.items():
                    if 'condicion' in info:
                        cond_key = info['condicion']
                        # priorizar los valores que ya están en datos (p.ej. nacionalidad compartida)
                        if cond_key in datos:
                            cond_value = datos[cond_key]
                        else:
                            # fallback a la fila (columnas base)
                            cond_value = row[cond_key]
                        probs_dict = info['probabilidades'][cond_value]
                        options = np.array(list(probs_dict.keys()))
                        probs = np.array(list(probs_dict.values()))
                        datos[key] = np.random.choice(options, p=probs)
                    else:
                        probs_dict = info['probabilidades']
                        options = np.array(list(probs_dict.keys()))
                        probs = np.array(list(probs_dict.values()))
                        datos[key] = np.random.choice(options, p=probs)

                # Ajuste de consumo
                adjustment = 0.0
                for feature, effect_dict in rules.items():
                    adjustment += effect_dict.get(datos.get(feature, ""), 0)
                avg_consumption = consumption_per_pax * (1 + adjustment)
                avg_consumption *= (1 + np.random.uniform(-0.025, 0.025))

                datos['Consumo medio'] = avg_consumption
                datos['Consumo total'] = avg_consumption * dias_estancia

                huespedes.append(datos)
                id_huesped_counter += 1

            pax_restante -= n_ocupantes
            id_habitacion_counter += 1

        # Concatenar todos los huéspedes generados para esta fila
        df = pd.DataFrame(huespedes)
        chunks.append(df)
        break  # Mantener para pruebas rápidas; quitar para procesar todo

    forged_df = pd.concat(chunks, ignore_index=True)
    return forged_df