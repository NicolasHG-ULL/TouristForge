# Proyecto TouristForge

## Descripción general

Este proyecto permite generar datos sintéticos de huéspedes, realizar análisis de consumo y visualizar los resultados en un dashboard.

El proyecto dispone de cuatro modos principales de operación:

* `forge_daily` → Genera datos sintéticos diarios a partir de un dataset base y distribuciones definidas en `dist.json`.
* `forge_hourly` → Genera consumo horario a partir de un ZIP diario previamente forjado.
* `modelling` → Permite analizar y modelar los datos generados.

### Dashboard

Para visualizar los resultados y análisis, se puede ejecutar el dashboard con:

```bash
python3 launch_dashboard.py
```

## Forjado de Datos Sintéticos - Diario

El módulo de forjado de datos permite **generar datasets sintéticos de huéspedes** a partir de un **dataset base de hoteles** y **distribuciones** definidas en `dist.json`.

Cada fila del dataset original se expande en varios huéspedes individuales respetando:

* **Número de huéspedes (`Pax`)** y **días de estancia (`Dias de estancia`)**.
* **Distribuciones condicionales y no condicionales** definidas en `dist.json`.
* **Reglas de consumo (`rules.json`)** que ajustan el consumo medio por huésped.
* **Variables compartidas por habitación**, que deben coincidir entre los huéspedes que comparten unidad.

La función principal utilizada internamente es:

```python
forge_guests(data: pd.DataFrame, dist: dict, rules: dict) -> pd.DataFrame
```

### Requisitos del dataset base

El dataset de entrada debe contener al menos estas columnas:

| Columna                             | Descripción                                           |
| :---------------------------------- | :---------------------------------------------------- |
| **Pax**                             | Número total de huéspedes de la fila                  |
| **Consumo de electricidad por Pax** | Consumo promedio por huésped                          |
| **Mes**                             | Mes de la estancia (1–12 o nombre)                    |
| **Año**                             | Año de la estancia                                    |
| **Estación**                        | Estación del año (invierno, primavera, verano, otoño) |

Estas columnas son necesarias tanto para calcular el número de huéspedes y días de estancia como para servir de **condicionante en distribuciones dependientes**.

#### Variables generadas automáticamente

Al generar los datos sintéticos, ciertas columnas **no deben aparecer en `dist.json`**, ya que se crean automáticamente:

* `id_huesped` → identificador único de cada huésped
* `id_habitacion` → identificador de la habitación asignada
* `Dias de estancia` → número de días que dura la estancia
* `Dia inicio` → día del mes en que comienza la estancia
* `Consumo medio` → consumo calculado por huésped según reglas
* `Consumo total` → consumo total (Consumo medio × Dias de estancia)

### Distribuciones (`dist.json`)

Las distribuciones definen cómo se generan las variables sintéticas. Existen tres tipos:

#### 1. Variables sin condición

Se asignan según una probabilidad global.

#### 2. Variables condicionadas

Dependen de otra columna (base o sintética).

**Ejemplo:**

```json
"nacionalidad": {
  "condicion": "Estación",
  "probabilidades": {
    "invierno": {"España": 0.15, "Reino Unido": 0.30, "Alemania": 0.30, "Francia": 0.10, "Italia": 0.1, "Otros": 0.05},
    "verano":  {"España": 0.35, "Reino Unido": 0.15, "Alemania": 0.15, "Francia": 0.15, "Italia": 0.25, "Otros": 0.05}
  }
}
```

#### 3. Variables compartidas por habitación

Algunas variables deben ser iguales para todos los huéspedes que comparten habitación.

Para ello se añade el campo:

```json
"compartido_por_habitacion": true
```

**Ejemplo típico:**

* `nacionalidad`
* `tipo_habitacion`

**Ejemplo completo:**

```json
"nacionalidad": {
  "condicion": "Estación",
  "compartido_por_habitacion": true,
  "probabilidades": {
    "invierno": {"España": 0.2, "Alemania": 0.3, "Reino Unido": 0.3, "Italia": 0.1, "Otros": 0.1}
  }
}
```

Si una habitación tiene ocupación 2, 3 o 4, estos huéspedes recibirán el mismo valor para cualquier variable donde este campo sea `true`.

> ⚠️ Nota: Las variables compartidas se generan antes que las individuales. Por ello, **una variable compartida no puede estar condicionada a una variable individual**, solo puede depender de columnas del dataset base o de otras variables compartidas que ya se hayan generado.

#### 4. Variable obligatoria: `ocupacion_habitacion`

Define cuántos huéspedes se asignan a una misma habitación.

```json
"ocupacion_habitacion": {
  "probabilidades": {
    "1": 0.75,
    "2": 0.175,
    "3": 0.05,
    "4": 0.025
  }
}
```

Esta variable determina cuántas filas se generan por cada habitación y agrupa a los huéspedes que compartirán valores comunes.

**Notas sobre las probabilidades:**

* Cada conjunto de probabilidades debe sumar 1.
* Si las probabilidades no suman 1, se **normalizan automáticamente** durante el forjado de datos.
* Durante la ejecución, se muestra información en consola indicando qué variables han sido normalizadas y sus valores ajustados.
* Esta regla aplica tanto para variables simples, condicionadas, como para compartidas por habitación.

### Reglas de consumo (`rules.json`)

Las reglas modifican el consumo medio del huésped aplicando ajustes multiplicativos:

$$ \text{Consumo medio} = \text{Consumo base} \times (1 + \text{ajuste}) $$

Además:

* Se añade ruido aleatorio por huésped, el valor por defecto es **±5%**, pero es modificable.
* Los ajustes se aplican en cascada según las variables generadas.
* Después de aplicar todas las reglas y generar los huéspedes, se normaliza el consumo total para que la suma de todos los huéspedes coincida con el consumo real del dataset original. Esto introduce un **factor de normalización** aplicado a cada `Consumo medio` y `Consumo total`.

**Interpretación del factor de normalización:**

* Factor ≈ 1 → las reglas están balanceadas y no alteran significativamente el consumo total.
* Factor > 1 → las reglas redujeron demasiado el consumo, se incrementa para ajustarlo.
* Factor < 1 → las reglas aumentaron demasiado el consumo, se reduce para ajustarlo.

**Ejemplo de reglas:**

```json
{
  "nacionalidad": {
    "Alemania": 0.15,
    "Reino Unido": 0.12,
    "Francia": 0.1,
    "España": -0.1,
    "Italia": -0.1,
    "Otros": 0
  },
  "sexo": {
    "Mujer": 0.05,
    "Hombre": -0.03
  },
  "uso_instalaciones": {
    "Si": 0.1,
    "No": -0.1
  },
  "tipo_habitacion": {
    "Suite": 0.2,
    "Estándar": -0.2
  }
}
```

### Uso básico

```bash
python3 main.py --mode forge_daily --data mi_dataset.csv --dist dist.json --rules rules.json
```

**Parámetros:**

* `--mode forge_daily` → activa el módulo de forjado
* `--data` → ruta del CSV base
* `--dist` → JSON con distribuciones
* `--rules` → JSON con reglas de consumo

### Salida

El forjado genera automáticamente en `data/forged/daily`:

* `forged_XXXX.csv` – Dataset sintético resultante.
* `dist_XXXX.json` – Distribuciones utilizadas.
* `rules_XXXX.json` – Reglas aplicadas.
* `daily_XXXX.zip` – Contenedor con los tres archivos anteriores.
* `info_XXXX.json` – Información adicional de la generación, incluyendo:

  * `num_guests` – Número de huéspedes generados.
  * `noise_daily` – Ruido aplicado.
  * `normalization_info` – Factor aplicado para ajustar el consumo total al dataset original.

`XXXX` corresponde al siguiente índice disponible en la carpeta `data/forged/daily`, determinado automáticamente para evitar sobrescribir archivos existentes.

---

### Forjado de Datos Sintéticos — Horario

Esta sección permite generar **datos de consumo por hora** a partir de un **dataset diario forjado** (`forge_daily`) y unos **perfiles horarios** definidos en un archivo JSON.

Cada fila del dataset diario se expande en **una fila por día de estancia** del huésped, y cada fila diaria se divide en **24 horas** siguiendo un perfil horario:

* Se utiliza el **Consumo total** de todos los días de estancia de cada huésped para asignar el consumo diario.

  * Recordatorio: `Consumo total = Consumo medio × Dias de estancia`
* Cada día tiene un consumo ligeramente aleatorio (ruido controlado por parámetro) para que no todos los días sean idénticos, pero **la suma total por huésped se mantiene igual que en los datos diarios**.
* El consumo diario se distribuye entre las 24 horas según el perfil horario seleccionado para cada huésped, heredando de forma implícita la variabilidad del consumo diario.

#### Archivo de perfiles horarios

Los perfiles horarios se definen en un JSON con la siguiente estructura:

```json
{
  "morning_active": {
    "descripcion": "High consumption in morning hours, low at night",
    "probabilidades": [0.08, 0.08, 0.04, 0.04, 0.04, 0.04, 0.08, 0.08, 0.08, 0.08, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04]
  },
  ...
}
```

**Notas:**

* Cada lista de `probabilidades` debe tener exactamente 24 elementos, uno por hora.
* La suma de los valores en cada perfil debe ser 1.

  * Si no suman 1, se **normalizan automáticamente** durante la ejecución.
  * La normalización genera mensajes en consola indicando el nombre del perfil y la acción realizada.
* El valor de **ruido diario** es configurable, por defecto ±5%, y afecta la variabilidad entre días de un mismo huésped.

#### Uso básico

```bash
python3 main.py --mode forge_hourly --daily_index 1 --profiles hourly_profiles.json
```

**Parámetros:**

* `--mode forge_hourly` → activa el módulo de forjado horario
* `--daily_index` → índice del ZIP diario forjado a usar como base (por ejemplo, `1` → `daily_0001.zip`)
* `--profiles` → archivo JSON con los perfiles horarios

#### Salida

El forjado horario genera automáticamente en `data/forged/hourly`:

* `hourly_XXXX.csv` – Dataset sintético horario
* `hourly_XXXX.zip` – Contenedor ZIP con el dataset horario y el archivo de perfiles usado
* `info_XXXX.json` – Información adicional sobre el forjado (archivo diario de origen, número de huéspedes, fecha de generación, ruido aplicado, etc.)

`XXXX` corresponde al siguiente índice disponible en la carpeta `data/forged/hourly`, determinado automáticamente para evitar sobrescribir archivos existentes.

## Modelado de consumo (`modelling`)

La sección de **modelling** permite entrenar y evaluar modelos de regresión sobre los datos sintéticos diarios generados con la fase de `forge_daily`. Se centra en predecir el **consumo medio de electricidad por huésped**.

### Flujo de trabajo

1. **Cargar los datos sintéticos diarios**

   ```python
   forged_data_df, forged_dist, rules = load_daily_zip(FORGED_DAILY_PATH, daily_index)
   forged_df = forged_data_df[forged_data_df['Hotel'] == ONE_HOTEL]
   ```

   * `forged_df` contiene los huéspedes de un hotel específico.
   * Se puede filtrar por hotel si el ZIP contiene varios hoteles.

2. **Preparar las variables**

   * Variables numéricas: `Dias de estancia`.
   * Variables categóricas: `sexo`, `nacionalidad`, `edad`, `tipo_habitacion`, `uso_instalaciones`, `viaje`, `comparte_habitacion`.
   * Se aplica **one-hot encoding** a todas las variables categóricas.
   * Se eliminan valores `NaN` o infinitos, y se escalan las variables numéricas.

3. **Eliminación de variables multicolineales**

   * **Correlación alta:** Se eliminan variables cuya correlación absoluta supere `corr_threshold` (por defecto 0.8).
   * **VIF alto:** Se eliminan variables con VIF (`Variance Inflation Factor`) superior a `vif_threshold` (por defecto 10).

4. **Entrenamiento de modelos**
   Se entrenan varios modelos de regresión para estimar el `Consumo medio`:

   * Random Forest
   * AdaBoost
   * Ridge
   * Lasso
   * Bayesian Ridge
   * XGBoost

5. **Evaluación**

   * Se calcula RMSE y MAE sobre un conjunto de prueba (80/20 split).
   * Se extraen **importancias de características** de cada modelo:

     * `feature_importances_` para RandomForest, AdaBoost, XGBoost.
     * Valor absoluto de `coef_` para Ridge, Lasso, BayesianRidge.

6. **Combinación con información teórica y correlaciones**

   * Las importancias se pueden comparar con las derivadas de las reglas (`rules.json`) y distribuciones (`dist.json`) para obtener una visión teórica del efecto de cada variable.
   * Se normalizan y combinan las importancias en un DataFrame final (`importance_combined_normalized`) que se guarda junto con los modelos entrenados.

### Entradas

| Argumento        | Tipo        | Descripción                                                              |
| ---------------- | ----------- | ------------------------------------------------------------------------ |
| `forged_df`      | `DataFrame` | Datos sintéticos diarios de huéspedes para un hotel.                     |
| `corr_threshold` | `float`     | Umbral de correlación para eliminar variables altamente correlacionadas. |
| `vif_threshold`  | `float`     | Umbral de VIF para eliminar variables multicolineales.                   |

### Salidas

| Retorno           | Tipo        | Descripción                                                      |
| ----------------- | ----------- | ---------------------------------------------------------------- |
| `importance_df`   | `DataFrame` | Importancia de cada variable para cada modelo.                   |
| `eliminated_vars` | `dict`      | Variables eliminadas por alta correlación o VIF.                 |
| `model_storage`   | `dict`      | Modelos entrenados, escaladores y métricas de error (RMSE, MAE). |

### Ejemplo de uso

```python
from modelling import train_and_evaluate_models

importance_df, eliminated_vars, model_storage = train_and_evaluate_models(forged_df)

print(importance_df.head())
print(eliminated_vars)
print(model_storage['error_metrics'])
```

### Notas importantes

* Las variables categóricas deben estar correctamente codificadas; el one-hot encoding se realiza dentro de la función.
* El DataFrame `forged_df` debe contener al menos las columnas utilizadas en el forjado: `Dias de estancia`, `sexo`, `nacionalidad`, `edad`, `tipo_habitacion`, `uso_instalaciones`, `viaje`, `comparte_habitacion`, `Consumo medio`.
* Se recomienda revisar los `eliminated_vars` para comprender qué variables se descartan y por qué.
* Las importancias combinadas pueden ser comparadas con las reglas definidas en `rules.json` para validar la coherencia del modelo con el dataset sintético.