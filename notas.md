## Fórmulas Teóricas

## Fórmula de Importancia de Sexo

La fórmula de **Importancia de Sexo** se expresa como:

$$
\text{Importancia de Sexo} = P(\text{Hombre}) \times |\text{Impacto (Hombre)}| + P(\text{Mujer}) \times |\text{Impacto (Mujer)}|
$$


## Fórmula de Importancia de Alemania

La fórmula de **Importancia de Alemania** se expresa como:

$$
\text{Importancia de Alemania} = \sum_{\text{estación}} P(\text{estación}) \times P(\text{Alemania} | \text{estación}) \times |\text{Impacto (Alemania)}|
$$


## Fórmula de Importancia de Suite

La fórmula de **Importancia de Suite** se expresa como:

$$
\text{Importancia de Suite} = \sum_{\text{nacionalidad}} P(\text{nacionalidad}) \times P(\text{Suite} | \text{nacionalidad}) \times |\text{Impacto (Suite)}|
$$


## Fórmula de Importancia

La fórmula de **Importancia(Sí)** se expresa como:

$$
\text{Importancia(Sí)} = \sum_{\text{tipo\_habitacion}} \left( P(\text{tipo\_habitacion}) \times P(\text{Sí} | \text{tipo\_habitacion}) \times |\text{impacto(Sí)}| \right)
$$


## Error relativo

$$
\text{Error\ Relativo} = \left( \frac{|\text{Valor\ 1} - \text{Valor\ 2}|}{|\text{Valor\ 2}|} \right) \times 100
$$


## Factor de inflación de la varianza
Umbrales:   0,8 para la correlación
            10 para FIV


## Casos especiales
3001: probabilidades condicionadas; 90% de huéspedes alemanes
3002: probabilidades condicionadas; el peso de Alemán igual a la suma del resto
4000: probabilidades no condicionadas; 
4001: probabilidades no condicionadas; 90% de huéspedes alemanes
4002: probabilidades no condicionadas; el peso de Alemán igual a la suma del resto

Calculo del error RMSE y MAE
Nuevos modelos XGBoost y NaiveBayes