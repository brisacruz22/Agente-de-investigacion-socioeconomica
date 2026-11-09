# Sumaria ENAHO 2024 (módulo 34): las 163 variables por categoría

Total clasificado: 163 de 163 variables.

Generado desde `sumaria-2024.dta` (33,691 hogares). Los montos son **soles anuales por hogar** salvo las líneas de pobreza (soles mensuales por persona). Para comparar entre departamentos: monto / mieperho / 12 / ld.

«% > 0» = porcentaje de hogares (sin ponderar) con un monto positivo: dice qué tan común es cada fuente.

## 01 · Identificación del hogar y del marco

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `aÑo` | año de la encuesta | — |
| `mes` | mes de ejecucion de la encuesta | — |
| `conglome` | numero de conglomerado | — |
| `vivienda` | numero de seleccion de vivienda | — |
| `hogar` | numero secuencial del hogar | — |
| `nconglome` | numero de conglomerado (proveniente del marco) | — |
| `sub_conglome` | numero de subconglomerado (proveniente del marco) | — |

## 02 · Ubicación, estratos y factor de expansión

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ubigeo` | ubicacion geográfica | — |
| `dominio` | dominio geográfico | — |
| `estrato` | estrato geográfico | — |
| `estrsocial` | estrato socio-economico | — |
| `factor07` | factor de expansion anual proyecciones cpv-2007 | — |

## 03 · Composición del hogar

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `mieperho` | total de miembros del hogar | 100.0 |
| `totmieho` | total de personas en el hogar | 100.0 |
| `percepho` | total de perceptores de ingresos | 99.7 |

## 04 · Ingreso por trabajo: actividad principal

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ingbruhd` | ingreso bruto actividad principal monetaria (dependiente) | 51.8 |
| `ingnethd` | ingreso neto de la actividad principal monetario (dependiente) | 51.8 |
| `pagesphd` | ingreso por pago en especie de la actividad principal | 21.6 |
| `ingindhd` | ingreso por actividad principal independiente | 64.3 |
| `ingauthd` | ingreso por autoconsumo de la actividad principal independiente | 41.4 |

## 05 · Ingreso por trabajo: actividad secundaria y extraordinarios

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `insedthd` | ingreso bruto de la actividad secundaria dependiente | 9.5 |
| `insedlhd` | ingreso neto de la actividad secundaria dependiente | 9.5 |
| `paesechd` | ingreso pago en especie de la actividad secundaria dependiente | 4.5 |
| `ingseihd` | ingreso neto de la actividad secundaria independiente | 17.4 |
| `isecauhd` | ingreso por autoconsumo de la actividad secundaria independiente | 8.5 |
| `ingexthd` | ingresos extraordinarios por trabajo | 20.0 |

## 06 · Transferencias (privadas, públicas y del extranjero)

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ingtrahd` | ingreso por transferencias corrientes monetarias del pais | 55.8 |
| `ingtexhd` | ingreso por transferencias corrientes del extranjero | 1.1 |
| `ingtprhd` | ingreso por transferencia corrientes privada | 23.9 |
| `ingtpuhd` | ingreso por transferencia corrientes publica | 42.3 |
| `ingtpu01` | ingreso por transferencia corrientes  publica: juntos | 12.3 |
| `ingtpu02` | ingreso por transferencias corrientes  publicas otros | 13.1 |
| `ingtpu03` | ingreso por transferencias corrientes publicas: pension 65 | 10.6 |
| `ingtpu04` | ingreso por transferencias corrientes publicas: beca 18 | 0.4 |
| `ingtpu05` | ingreso por transferencias corrientes publicas: bono de gas | 16.5 |
| `ingtpu10` | ingreso por transferencias corrientes públicas bono electricidad | 0.1 |
| `ingtpu11` | ingreso por transferencias corrientes públicas bono niño | 0.0 |
| `ingtpu12` | ingreso por transferencias corrientes públicas bono onp para jubilados | 0.0 |
| `ingtpu13` | ingreso por transferencias corrientes públicas programa contigo | 1.4 |
| `ingtpu14` | ingreso por transferencias corrientes públicas bono yanapay | 0.0 |
| `ingtpu15` | ingreso por transferencias corrientes públicas asistencia economica por orfandad | 0.1 |
| `ingtpu16` | ingreso por transferencias corrientes públicas bono alimentario | 0.0 |

## 07 · Rentas de la propiedad y otros ingresos

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ingrenhd` | ingreso por rentas de la propiedad monetaria | 7.9 |
| `ingoexhd` | otros ingresos extraordinarios | 33.9 |

## 08 · Ingreso: agregados del hogar

…1 = bruto, …2 = neto. inghog2d es el ingreso neto total que usa el INEI.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ingmo1hd` | ingreso monetario (bruto) | 99.7 |
| `ingmo2hd` | ingreso monetario (neto) | 99.7 |
| `inghog1d` | ingreso bruto | 100.0 |
| `inghog2d` | ingreso neto total | 100.0 |

## 09 · Vivienda: alquiler, alquiler imputado y créditos

ia01hd (ingreso) y ga04hd (gasto) son el alquiler imputado de quien vive en vivienda propia: coinciden en el 99.7 % de los hogares. Se cuenta a ambos lados para que el propietario sea comparable con quien alquila.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ia01hd` | ingreso alquiler imputado de la vivienda | 91.1 |
| `ia02hd` | ingreso por transferencia de alquiler | 0.3 |
| `ig03hd1` | credito, compra casa, departamento | 0.2 |
| `ig03hd2` | credito, comprar terreno para vivienda | 0.4 |
| `ig03hd3` | credito mejoramiento y/o ampliacion de la vivienda | 2.3 |
| `ig03hd4` | credito,construccion de nueva vivienda | 0.4 |
| `ga03hd` | gasto por alquiler | 8.6 |
| `ga04hd` | gasto por alquiler imputado | 91.4 |

## 10 · Alimentos: detalle por lugar y forma de obtención

Detalle de alimentos por lugar (dentro o fuera del hogar, ollas comunes) y por forma (pagado o no). Comprobado: su suma no coincide con la de gru1*, así que no son dos vistas del mismo total. Antes de usarlos, revisar la metodología en ConstVarGasto-Metodologia actualizada.zip.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `sg23` | gastos por alimentos para consumir dentro del hogar | 3.0 |
| `sig24` | ingresos y gastos por alimentos para consumir en el hogar | 1.0 |
| `sg25` | gastos por alimentos consumidos fuera del hogar (menores de 14 años) | 10.2 |
| `sig26` | ingresos y gastos por alimentos consumidos fuera del hogar (menores de 14 años) | 7.9 |
| `sg27` | gastos por alimentos consumidos por ollas comunes | 0.2 |
| `sig28` | ingresos y gastos por alimentos consumidos por ollas comunes | 0.1 |
| `g05hd` | gastos por alimentos consumidos fuera del hogar - pago | 69.0 |
| `ig06hd` | ingresos y gastos por alimentos consumidos fuera del hogar-no pago | 10.4 |
| `g05hd1` | gastos por alimentos consumidos fuera del hogar en otro hogar- pago | 3.1 |
| `ig06hd1` | ingresos y gastos por alimentos consumidos fuera del hogar - otro hogar-no pago | 25.1 |
| `g05hd2` | gastos por alimentos consumidos fuera del hogar prepara sus alimentos - pago | 4.8 |
| `ig06hd2` | ingresos y gastos por alimentos consumidos fuera del hogar - prepara sus aliment | 3.8 |
| `g05hd3` | gastos por alimentos consumidos fuera del hogar prepara sus alim en su centro de | 0.0 |
| `ig06hd3` | ingresos y gastos por alimentos consumidos fuera del hogar - prepara sus aliment | 0.0 |
| `g05hd4` | gastos por alimentos consumidos fuera del hogar en el aula del centro educativo | 0.0 |
| `ig06hd4` | ingresos y gastos por alimentos consumidos fuera del hogar- aula de su centro ed | 0.0 |
| `g05hd5` | gastos por alimentos consumidos fuera del hogar a autoconsumo | 0.0 |
| `ig06hd5` | ingresos y gastos por alimentos consumidos fuera del hogar - autonsumo-no pago | 0.0 |
| `g05hd6` | gastos por alimentos consumidos fuera del hogar campamento - pago | 0.0 |
| `ig06hd6` | ingresos y gastos por alimentos consumidos fuera del hogar - campamento-no pago | 0.0 |

## 11.1 · Gasto grupo 1: alimentos

El sufijo indica la forma de obtención: …1hd pagado; …2hd autoconsumo o pago en especie; …3hd donación pública, privada u otra; gru14hd* son alimentos preparados.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru11hd` | grupo 1: alimentos - gasto | 99.0 |
| `gru12hd1` | grupo 1: alimentos - autoconsumo, autosuministro | 45.2 |
| `gru12hd2` | grupo 1: alimentos - pago en especie | 2.1 |
| `gru13hd1` | grupo 1: alimentos - donacion publica | 6.7 |
| `gru13hd2` | grupo 1: alimentos - donacion privada | 58.8 |
| `gru13hd3` | grupo 1: alimentos - otros gastos | 35.4 |
| `gru13hd4` | grupo 1: alimentos consumidos dentro hogar -bienes libres | 15.5 |
| `gru14hd` | alimentos preparados consumir en el hogar - pagado | 42.1 |
| `gru14hd1` | alimentos preparados consumir en el hogar - autoconsumo , autosuministro | 3.6 |
| `gru14hd2` | alimentos preparados consumir en el hogar - especie | 0.2 |
| `gru14hd3` | alimentos preparados consumir en el hogar - donado  publico | 0.0 |
| `gru14hd4` | alimentos preparados consumir en el hogar - donado privado | 10.2 |
| `gru14hd5` | alimentos preparados consumir en el hogar - otros | 0.0 |
| `gru14hd6` | grupo 1: alimentos consumidos fuera del hogar -bienes libres | 0.0 |

## 11.2 · Gasto grupo 2: vestido y calzado

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru21hd` | grupo 2: vestido y calzado - gasto | 76.2 |
| `gru22hd1` | grupo 2: vestido y calzado - autoconsumo, autosuministro | 1.2 |
| `gru22hd2` | grupo 2: vestido y calzado - pago en especie | 0.2 |
| `gru23hd1` | grupo 2: vestido y calzado - donacion publica | 0.3 |
| `gru23hd2` | grupo 2: vestido y calzado - donacion privada | 26.2 |
| `gru23hd3` | grupo 2: vestido y calzado - otros | 0.1 |
| `gru24hd` | grupo 2: vestido y calzado - no gasto, no sabe | 0.0 |

## 11.3 · Gasto grupo 3: alquiler, combustible, electricidad y conservación de la vivienda

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru31hd` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 96.3 |
| `gru32hd1` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 9.0 |
| `gru32hd2` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 0.0 |
| `gru33hd1` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 0.0 |
| `gru33hd2` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 13.0 |
| `gru33hd3` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 1.0 |
| `gru34hd` | grupo 3: alquiler de vivienda, combustible, electricidad y conservacion de la vi | 91.9 |

## 11.4 · Gasto grupo 4: muebles, enseres y mantenimiento

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru41hd` | grupo 4: muebles, enseres y mantenimiento de la vivienda - gasto | 93.5 |
| `gru42hd1` | grupo 4: muebles, enseres y mantenimiento de la vivienda - autoconsumo, autosumi | 6.0 |
| `gru42hd2` | grupo 4: muebles, enseres y mantenimiento de la vivienda - pago en especie | 0.2 |
| `gru43hd1` | grupo 4: muebles, enseres y mantenimiento de la vivienda - donacion publica | 1.0 |
| `gru43hd2` | grupo 4: muebles, enseres y mantenimiento de la vivienda - donacion privada | 63.7 |
| `gru43hd3` | grupo 4: muebles, enseres y mantenimiento de la vivienda - otros | 0.8 |
| `gru44hd` | grupo 4: muebles, enseres y mantenimiento de la vivienda - no gasto, no sabe | 0.1 |

## 11.5 · Gasto grupo 5: salud

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru51hd` | grupo 5: cuidado, conservacion de la salud y servicios medicos - gasto | 78.7 |
| `gru52hd1` | grupo 5: cuidado, conservacion de la salud y servicios medicos - autoconsumo, au | 0.9 |
| `gru53hd1` | grupo 5: cuidado, conservacion de la salud y servicios medicos - donacion public | 59.0 |
| `gru53hd2` | grupo 5: cuidado, conservacion de la salud y servicios medicos - donacion privad | 38.6 |
| `gru53hd3` | grupo 5: cuidado, conservacion de la salud y servicios medicos - otros | 0.8 |
| `gru53hd4` | grupo 5: cuidado, conservacion de la salud y servicios medicos - bienes libres | 0.1 |
| `gru54hd` | grupo 5: cuidado, conservacion de la salud y servicios medicos - no gasto, no s | 0.5 |

## 11.6 · Gasto grupo 6: transportes y comunicaciones

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru61hd` | grupo 6: transportes y comunicaciones - gasto | 94.6 |
| `gru62hd1` | grupo 6: transportes y comunicaciones - autoconsumo, autosuministro | 0.2 |
| `gru62hd2` | grupo 6: transportes y comunicaciones - pago en especie | 0.4 |
| `gru63hd1` | grupo 6: transportes y comunicaciones - donacion publica | 0.1 |
| `gru63hd2` | grupo 6: transportes y comunicaciones - donacion privada | 10.8 |
| `gru63hd3` | grupo 6: transportes y comunicaciones - otros | 0.1 |
| `gru64hd` | grupo 6: transportes y comunicaciones - no gasto, no sabe | 2.7 |

## 11.7 · Gasto grupo 7: esparcimiento, cultura y enseñanza

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru71hd` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - gasto | 72.6 |
| `gru72hd1` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - autocon | 1.0 |
| `gru72hd2` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - pago en | 1.4 |
| `gru73hd1` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - donacio | 34.0 |
| `gru73hd2` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - donacio | 23.5 |
| `gru73hd3` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - otros | 6.1 |
| `gru74hd` | grupo 7: esparcimiento, diversion, servicios culturales y de enseñanza - no gast | 0.0 |

## 11.8 · Gasto grupo 8: otros bienes y servicios

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gru81hd` | grupo 8: otros bienes y servicios - gasto | 93.7 |
| `gru82hd1` | grupo 8: otros bienes y servicios - autoconsumo, autosuministro | 6.9 |
| `gru82hd2` | grupo 8: otros bienes y servicios - pago en especie | 0.2 |
| `gru83hd1` | grupo 8: otros bienes y servicios - donacion publica | 0.3 |
| `gru83hd2` | grupo 8: otros bienes y servicios - donacion privada | 28.0 |
| `gru83hd3` | grupo 8: otros bienes y servicios - otros | 2.8 |
| `gru83hd4` | grupo 8: alimentos para mascotas - bien libre | 0.1 |
| `gru84hd` | grupo 8: otros bienes y servicios - no gasto, no sabe | 0.1 |
| `gru84hd1` | grupo 8: otros bienes y servicios fiestas familiares y sociales - pagado | 9.9 |
| `gru85hd1` | grupo 8: otros bienes y servicios fiestas familiares y sociales- autoconsumo, au | 0.3 |
| `gru86hd1` | grupo 8: otros bienes y servicios fiestas familiares y sociales- donado privado | 2.6 |
| `gru86hd2` | grupo 8: otros bienes y servicios fiestas familiares y sociales- donado - otro | 0.0 |
| `gru87hd` | grupo 8: otros bienes y servicios fiestas familiares y sociales-  no gasto, no | 0.0 |

## 12 · Equipamiento del hogar (compras y adquisiciones)

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `sg42` | gastos por equipamiento del hogar comprados- equipos tv, computadora ,sonido | 68.6 |
| `sg421` | gastos por equipamiento del hogar comprados- electrodomesticos | 80.9 |
| `sg422` | gastos por equipamiento del hogar comprados - transporte | 22.9 |
| `sg423` | gastos por equipamiento del hogar comprados- otros | 0.0 |
| `sg42d` | gastos por equipamiento del hogar adquiridos - equipos tv, computadora, sonido | 18.4 |
| `sg42d1` | gastos por equipamiento del hogar adquiridos- electrodomesticos | 19.4 |
| `sg42d2` | gastos por equipamiento del hogar adquiridos- transporte | 3.8 |
| `sg42d3` | gastos por equipamiento del hogar adquiridos- otros | 0.0 |

## 13 · Otros gastos

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `g07hd` | otros gastos - pago | 55.9 |
| `ig08hd` | ingresos y gastos, otros - no pago | 3.7 |

## 14 · Gasto: agregados del hogar

gashog2d es el gasto total y el que define la pobreza: comprobado, un hogar es pobre (pobreza <= 2) exactamente cuando gashog2d / mieperho / 12 < linea. Ojo: la suma de las gru* no da gashog2d (coincide en 3.4 % de hogares), así que no se recalcula el total sumando grupos.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `gashog1d` | gasto monetario | 100.0 |
| `gashog2d` | gasto total bruto | 100.0 |

## 15 · Pobreza, líneas y deflactor

pobreza: 1 pobre extremo (1,588 hogares), 2 pobre no extremo (5,224), 3 no pobre (26,879). Con factor07 × mieperho da 27.58 % de personas pobres. Las líneas están en soles mensuales por persona y ya varían por zona (linea: S/ 316 a 559); ld es el deflactor espacial (0.73 a 1.00) para comparar gastos o ingresos reales entre departamentos.

| Variable | Etiqueta del INEI | % > 0 |
| --- | --- | --- |
| `ld` | deflactor espacial | — |
| `linpe` | linea de pobreza alimentaria | — |
| `linea` | linea de pobreza total | — |
| `pobreza` | pobreza | — |
| `lineav` | linea corriente de vulnerabilidad | — |
| `pobrezav` | pobreza y vulnerable con linea corriente | — |

