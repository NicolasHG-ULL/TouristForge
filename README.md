# Proyecto TouristForge

## Descripción general

Este proyecto permite generar datos sintéticos de huéspedes, realizar análisis de consumo y visualizar los resultados en un dashboard.  

El proyecto dispone de tres modos principales de operación:

- `forge` → Genera datos sintéticos a partir de un dataset base y distribuciones definidas en `dist.json`.  
- `forge_parallel` → Versión paralelizada para procesar grandes datasets más rápidamente.  
- `modelling` → Permite analizar y modelar los datos generados.

### Dashboard

Para visualizar los resultados y análisis, se puede ejecutar el dashboard con:

```bash
python3 launch_dashboard.py
```

## Forjado de Datos Sintéticos
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

## Requisitos del dataset base
El dataset de entrada debe contener al menos estas columnas:

| Columna | Descripción |
| :--- | :--- |
| **Pax** | Número total de huéspedes de la fila |
| **Consumo de eletricidad por Pax** | Consumo promedio por huésped |
| **Mes** | Mes de la estancia (1–12 o nombre) |
| **Año** | Año de la estancia |
| **Estación** | Estación del año (invierno, primavera, verano, otoño) |

Estas columnas son necesarias tanto para calcular el número de huéspedes y días de estancia como para servir de **condicionante en distribuciones dependientes**.

### Variables generadas automáticamente

Al generar los datos sintéticos, ciertas columnas **no deben aparecer en `dist.json`**, ya que se crean automáticamente:

- `id_huesped` → identificador único de cada huésped  
- `id_habitacion` → identificador de la habitación asignada  
- `Dias de estancia` → número de días que dura la estancia  
- `Dia inicio` → día del mes en que comienza la estancia  
- `Consumo medio` → consumo calculado por huésped según reglas  
- `Consumo total` → consumo total (Consumo medio × Dias de estancia)

## Distribuciones (`dist.json`)
Las distribuciones definen cómo se generan las variables sintéticas. Existen tres tipos:

### 1. Variables sin condición
Se asignan según una probabilidad global.

### 2. Variables condicionadas
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

### 3. Variables compartidas por habitación (nuevo)
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

#### Variable obligatoria: `ocupacion_habitacion`
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

## Reglas de consumo (`rules.json`)
Las reglas modifican el consumo medio del huésped aplicando ajustes multiplicativos:

$$ \text{Consumo medio} = \text{Consumo base} \times (1 + \text{ajuste}) $$

Además:
* Se añade ruido aleatorio **±2.5%** por huésped.
* Los ajustes se aplican en cascada según las variables generadas.

**Ejemplo:**
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

## Uso básico

```bash
python3 main.py --mode forge --data mi_dataset.csv --dist dist.json --rules rules.json --index 1
```

**Parámetros:**
* `--mode forge` → activa el módulo de forjado
* `--data` → ruta del CSV base
* `--dist` → JSON con distribuciones
* `--rules` → JSON con reglas de consumo
* `--index` → índice para los archivos de salida

## Salida
El forjado genera automáticamente en `data/forged`:

* `forged_XXXX.csv` – Dataset sintético resultante
* `dist_XXXX.json` – Distribuciones utilizadas
* `rules_XXXX.json` – Reglas aplicadas
* `TouristForge_XXXX.zip` – Contenedor con los tres archivos

`XXXX` es el índice definido por `--index`.