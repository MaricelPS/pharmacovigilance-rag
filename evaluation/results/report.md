# Agent Evaluation Report

**Total questions**: 15

## Overall metrics

| Metric | Value |
|--------|-------|
| Tool routing accuracy   | 100.0% |
| PT coverage (avg)       | 93.3% |
| No forbidden claims     | 100.0% |
| Cites n= evidence       | 100.0% |
| Mentions limitations    | 100.0% |
| Avg agent turns         | 3.2 |

## Per-question breakdown

### q01 — open_signal
**Question**: ¿Qué señales de seguridad emergentes aparecen para semaglutida en 2024?

- Tool routing: PASS (expected `detect_signals`, called ['detect_signals'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 2

<details><summary>Answer preview</summary>

```
## Señales de Seguridad Emergentes para Semaglutida (FAERS 2024)

El análisis de desproporcionalidad identificó **20 señales estadísticamente significativas** según criterios EMA y BCPNN. Presento las más relevantes clínicamente:

### 🔴 **Señales Gastrointestinales Graves**

1. **Vaciamiento gástrico alterado** (n=818)
   - IC=5.32, ROR=73.4 (IC 95%: 67.0-80.4)
   - La señal más robusta por número de casos

2. **Íleo** (n=252)
   - IC=4.63, ROR=35.8 (IC 95%: 31.0-41.4)

3. **Pancreatitis obstructiva** (n=27)
   - IC=4.04, ROR=30.2 (IC 95%: 19.7-46.3)

### 🔴 **Señales Neurológicas y Sensoriales**

4. **Neuropatía óptica isquémica** (n=90)
   - IC=5.03, ROR=67.3 (IC 95%: 51.5-88.1)
   - Señal preocupante para la visión

5. **Alodinia** (n=130)
   - IC=5.79, ROR=249.6 (IC 95%: 180.3-345.5)
   - Dolor neuropático al tacto no doloroso

### 🔴 **Señales Metabólicas**

6. **Cetoacidosis por inanición** (n=16)
   - IC=4.23, ROR=73.6 (IC 95%: 38.8-139.9)
   - Pérdida de peso excesiva puede preci...
```
</details>

### q02 — semantic_lookup
**Question**: ¿Hay reportes de problemas hepáticos con tirzepatida?

- Tool routing: PASS (expected `semantic_event_search`, called ['query_cohort_events', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 3

<details><summary>Answer preview</summary>

```
**Sí, existen reportes de problemas hepáticos asociados con tirzepatida en FAERS 2024:**

## Eventos hepáticos reportados:

- **Enzimas hepáticas aumentadas**: n=55 (el más frecuente)
- **Trastorno hepático**: n=19
- **Pruebas de función hepática anormales**: n=12
- **Función hepática anormal**: n=7
- **Falla hepática**: n=6
- **Falla hepática aguda**: n=3
- **Enzimas hepáticas anormales**: n=3
- **Fibrosis hepática**: n=2
- **Lesión hepatocelular**: n=1

## Interpretación importante:

**Total combinado**: Aproximadamente 108 reportes de eventos relacionados con el hígado.

**Limitaciones críticas:**
- Estos datos representan **ASOCIACIÓN, NO CAUSALIDAD**
- El sistema de notificación espontánea tiene **subnotificación** importante
- **Sesgo de notoriedad**: eventos esperados o publicitados se reportan más
- Sin denominador poblacional (no sabemos cuántos pacientes usan tirzepatida)
- **Confusión por indicación**: pacientes con diabetes/obesidad pueden tener factores de riesgo hepático ...
```
</details>

### q03 — comparison
**Question**: Comparame el perfil de pancreatitis entre semaglutida, liraglutida y tirzepatida.

- Tool routing: PASS (expected `compare_drugs`, called ['compare_drugs', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 3

<details><summary>Answer preview</summary>

```
## Comparación del perfil de pancreatitis entre semaglutida, liraglutida y tirzepatida

### **Hallazgos principales:**

#### **1. Pancreatitis (término general)**
- **Semaglutida**: n=345 casos
  - ROR=10.64 (IC 95%: 9.51-11.90) ✓ Señal EMA/BCPNN
  - IC=3.23
  
- **Liraglutida**: n=31 casos  
  - ROR=10.72 (IC 95%: 7.52-15.29) ✓ Señal EMA/BCPNN
  - IC=3.16
  
- **Tirzepatida**: n=309 casos
  - ROR=4.00 (IC 95%: 3.56-4.50) ✓ Señal EMA/BCPNN
  - IC=1.89

**Interpretación**: Semaglutida y liraglutida muestran una desproporcionalidad **2.5 veces mayor** que tirzepatida para pancreatitis general (ROR ~10-11 vs. 4).

---

#### **2. Pancreatitis aguda**
- **Semaglutida**: n=118 casos
  - ROR=7.68 (IC 95%: 6.37-9.27) ✓ Señal
  
- **Liraglutida**: n=21 casos
  - ROR=16.01 (IC 95%: 10.42-24.58) ✓ Señal
  - IC=3.52 (el más alto de todas las formas)
  
- **Tirzepatida**: n=47 casos
  - ROR=1.26 (IC 95%: 0.94-1.68) ✗ **NO señal**
  - No alcanza significación estadística

**Interpretación**: Liraglu...
```
</details>

### q04 — specific_signal
**Question**: ¿Existe alguna señal de alerta que vincule a la semaglutida con la neuropatía óptica isquémica anterior no arterítica (NAION) según estudios recientes de 2024?

- Tool routing: PASS (expected `check_signal`, called ['detect_signals', 'query_cohort_events', 'semantic_event_search'])
- PT coverage: 50% (missing: ['Optic nerve infarction'])
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 3

<details><summary>Answer preview</summary>

```
## Hallazgos sobre NAION y Semaglutida en FAERS 2024

**SÍ existe una señal estadística** que asocia semaglutida con neuropatía óptica isquémica (que incluye NAION) en los datos de FAERS 2024:

### **Datos de la Señal:**
- **Casos reportados:** n=93 (actualizado a n=90 en el análisis de señales)
- **Término MedDRA:** "Optic ischaemic neuropathy" (Neuropatía óptica isquémica)
- **Posición en ranking de señales:** 4° lugar entre todas las señales detectadas para semaglutida

### **Métricas de Desproporcionalidad:**
- **PRR:** 66.87 (IC 95%: rango robusto)
- **ROR:** 67.34 (IC 95%: 51.46 - 88.12)
- **IC (Componente de Información):** 5.03 (IC 95%: 4.68 - 5.38)
- **Cumple criterios:** ✓ EMA (Agencia Europea) y ✓ BCPNN

### **Interpretación:**

1. **Señal estadísticamente significativa:** La neuropatía óptica isquémica se reporta aproximadamente **67 veces más frecuentemente** con semaglutida que lo esperado comparado con otros medicamentos en la base de datos.

2. **Robustez:** El límite i...
```
</details>

### q05 — specific_signal
**Question**: Quiero saber si la gastroparesia o el retraso en el vaciamiento gástrico están estadísticamente asociados como señal para los agonistas de GLP-1.

- Tool routing: PASS (expected `check_signal`, called ['detect_signals', 'compare_drugs', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 4

<details><summary>Answer preview</summary>

```
## Resumen: Gastroparesia y Retraso del Vaciamiento Gástrico en Agonistas de GLP-1

**Sí, existe una señal estadística clara de desproporción** para la gastroparesia y el retraso del vaciamiento gástrico con los agonistas de GLP-1, aunque la magnitud varía entre los fármacos.

### **Hallazgos Principales:**

#### **1. "Impaired gastric emptying" (Vaciamiento gástrico alterado)**

Este es el término más reportado y muestra **señales muy robustas**:

- **Semaglutide:** n=818 casos
  - PRR=69.8, IC=5.3 (IC 95%: 5.20-5.20)
  - ROR=73.4 (IC 95%: 67.0-80.4)
  - ✓ Cumple criterios EMA y BCPNN

- **Dulaglutide:** n=443 casos
  - PRR=75.5, IC=5.8 (IC 95%: 5.63-5.63)
  - ROR=81.1 (IC 95%: 72.8-90.5)
  - ✓ Cumple criterios EMA y BCPNN

- **Tirzepatide:** n=421 casos
  - PRR=11.4, IC=3.2 (IC 95%: 3.03-3.03)
  - ROR=11.5 (IC 95%: 10.4-12.9)
  - ✓ Cumple criterios EMA y BCPNN

- **Liraglutide:** n=30 casos
  - PRR=18.3, IC=3.8 (IC 95%: 3.29-3.29)
  - ROR=18.9 (IC 95%: 13.2-27.2)
  - ✓ Cumple criteri...
```
</details>

### q06 — specific_signal
**Question**: ¿Hay reportes o señales de ideación suicida o comportamiento autolesivo asociados al uso de semaglutida?

- Tool routing: PASS (expected `check_signal`, called ['detect_signals', 'compare_drugs', 'query_cohort_events', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 4

<details><summary>Answer preview</summary>

```
## Hallazgos sobre ideación suicida y comportamiento autolesivo con semaglutida

**SÍ existen reportes**, pero con señales mixtas:

### **Reportes identificados con semaglutida:**

1. **Ideación suicida**: n=265 reportes
   - **Señal estadística POSITIVA**: PRR=3.97, ROR=4.02 (IC 95%: 3.54-4.57), IC=1.94
   - Cumple criterios EMA y BCPNN para señal de desproporción

2. **Depresión con ideas suicidas**: n=12 reportes
   - **Señal estadística POSITIVA**: PRR=5.40, ROR=5.62 (IC 95%: 3.17-9.93), IC=2.15
   - Cumple criterios de señal

3. **Ideación autolesiva**: n=10 reportes (señal no evaluable por bajo número)

4. **Intento de suicidio**: n=38 reportes
   - **NO es señal**: PRR=0.77, ROR=0.78 (IC 95%: 0.55-1.11)
   - Reportado con MENOR frecuencia que en el resto de la base de datos

5. **Suicidio consumado**: n=23 reportes
   - **NO es señal**: PRR=0.58, ROR=0.60 (IC 95%: 0.39-0.92)
   - También reportado con menor frecuencia relativa

6. **Lesión intencional autoinfligida**: n=10 repor...
```
</details>

### q07 — specific_signal
**Question**: Tengo una duda sobre seguridad en quirófano: ¿el uso de GLP-1 se asocia con un mayor riesgo de aspiración pulmonar bajo anestesia?

- Tool routing: PASS (expected `check_signal`, called ['detect_signals', 'compare_drugs', 'query_cohort_events', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 4

<details><summary>Answer preview</summary>

```
## Hallazgos sobre GLP-1 y Riesgo de Aspiración Pulmonar

Basándome en los datos de FAERS 2024, aquí está lo que encontré sobre la asociación entre GLP-1 y aspiración pulmonar perioperatoria:

### **Datos de Aspiración en la Cohorte GLP-1 (n=50 casos totales)**

1. **Neumonía por aspiración**: n=45 reportes
2. **Complicación pulmonar anestésica**: n=3 reportes  
3. **Aspiración de residuo gástrico**: n=1 reporte
4. **Neumonitis por aspiración**: n=1 reporte

### **Análisis de Desproporcionalidad por Fármaco**

**Hallazgo crítico**: Ningún GLP-1 mostró una señal de desproporcionalidad estadística para aspiración pulmonar:

- **Semaglutide**: 
  - Neumonía por aspiración (n=22): PRR=1.07, IC 95% [0.72-1.66], **no señal**
  - No alcanza criterios EMA ni BCPNN

- **Dulaglutide**: 
  - Neumonía por aspiración (n=10): PRR=1.29, ROR=1.35 [0.74-2.48], **no señal**

- **Liraglutide**: n=1 caso, **no señal**

- **Tirzepatide**: n=4 casos, PRR=0.08 (reportes **significativamente menores** a lo es...
```
</details>

### q08 — open_signal
**Question**: ¿Cuáles son las principales señales de seguridad y eventos adversos reportados para la tirzepatida en la base de datos?

- Tool routing: PASS (expected `get_open_signals`, called ['detect_signals'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 2

<details><summary>Answer preview</summary>

```
## Principales señales de seguridad para tirzepatida

Basándome en el análisis de desproporcionalidad de la base de datos FAERS 2024, estas son las principales señales de seguridad identificadas para tirzepatida:

### **1. Eventos relacionados con el sitio de inyección** (muy destacados)
- **Frialdad en sitio de inyección** (n=115): IC=4.75, ROR=105.0
- **Lesión en sitio de inyección** (n=549): IC=4.66, ROR=66.1
- **Hemorragia en sitio de inyección** (n=2,062): IC=3.60, ROR=17.6
- **Eritema en sitio de inyección** (n=1,753): IC=3.05, ROR=10.5
- **Dolor en sitio de inyección** (n=5,293): IC=2.79, ROR=9.2
- **Hematomas en sitio de inyección** (n=1,182): IC=2.87, ROR=8.9
- **Prurito en sitio de inyección** (n=813): IC=2.79, ROR=8.2

### **2. Errores de administración y uso del producto** (señal muy fuerte)
- **Dosis incorrecta administrada** (n=9,802): IC=3.88, ROR=29.4
- **Dosis extra administrada** (n=2,987): IC=4.31, ROR=40.0
- **Subdosis accidental** (n=1,982): IC=4.50, ROR=50.4
- **S...
```
</details>

### q09 — open_signal
**Question**: ¿Qué señales de alerta de tipo musculoesquelético severo, como la rabdomiólisis, se han detectado de forma abierta para la clase de los GLP-1?

- Tool routing: PASS (expected `get_open_signals`, called ['detect_signals', 'compare_drugs', 'query_cohort_events', 'semantic_event_search'])
- PT coverage: 50% (missing: ['Blood creatine phosphokinase increased'])
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 5

<details><summary>Answer preview</summary>

```
Con base en el análisis exhaustivo de las señales de seguridad musculoesqueléticas severas en la clase de GLP-1, puedo proporcionar la respuesta:

## Señales de Alerta Musculoesqueléticas Severas en GLP-1

### **Hallazgos Principales**

Según el análisis de la base de datos FAERS 2024 para la clase completa de agonistas del receptor GLP-1, **NO se han detectado señales de desproporción estadísticamente significativas** para eventos musculoesqueléticos severos como rabdomiólisis o miopatías en ninguno de los principales GLP-1.

### **Datos Específicos por Evento:**

**1. RABDOMIÓLISIS (n=53 reportes totales en la cohorte GLP-1)**
- **48 reportes serios**
- **Ningún GLP-1 muestra señal positiva:**
  - Semaglutida: n=12, PRR=0.45, ROR=0.47 (IC 95%: 0.27-0.83) - **Señal NEGATIVA** (menos reportes de lo esperado)
  - Tirzepatida: n=6, PRR=0.10, ROR=0.11 (IC 95%: 0.05-0.23) - **Señal NEGATIVA**
  - Liraglutida: n=2, PRR=0.92, ROR=1.15 (IC 95%: 0.33-3.96) - Sin señal
  - Dulaglutida: n=3, PRR...
```
</details>

### q10 — comparison
**Question**: Comparame el perfil de eventos adversos gastrointestinales específicamente entre semaglutida y tirzepatida.

- Tool routing: PASS (expected `compare_drugs`, called ['compare_drugs', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 5

<details><summary>Answer preview</summary>

```
## Comparación de eventos adversos gastrointestinales: Semaglutida vs Tirzepatida

### Hallazgos principales (FAERS 2024)

**IMPORTANTE**: Los siguientes datos representan **asociaciones**, no causalidad. Las notificaciones espontáneas están sujetas a sesgos de notificación, subnotificación y ausencia de denominador poblacional adecuado.

---

### **1. NÁUSEAS**
- **Semaglutida**: n=2,504 | ROR 4.46 (IC 95%: 4.27-4.66) | IC=1.93
- **Tirzepatida**: n=3,703 | ROR 2.72 (IC 95%: 2.63-2.82) | IC=1.30
- **Interpretación**: Ambos fármacos muestran señal significativa, pero semaglutida presenta una desproporción **64% mayor** (ROR 4.46 vs 2.72).

---

### **2. VÓMITOS**
- **Semaglutida**: n=1,801 | ROR 5.04 (IC 95%: 4.79-5.30) | IC=2.15
- **Tirzepatida**: n=1,640 | ROR 1.83 (IC 95%: 1.74-1.93) | IC=0.82
- **Interpretación**: Diferencia muy marcada. Semaglutida muestra una desproporción **175% mayor** que tirzepatida. El vómito cumple criterios EMA solo para semaglutida.

---

### **3. DIARREA*...
```
</details>

### q11 — subgroup
**Question**: ¿Cuáles son las señales de eventos adversos más serios o que resultaron en muerte en el subgrupo de pacientes mayores de 65 años que toman liraglutida?

- Tool routing: PASS (expected `check_subgroup`, called ['query_cohort_events', 'detect_signals'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 3

<details><summary>Answer preview</summary>

```
## Señales de eventos adversos serios en pacientes mayores de 65 años con liraglutida

Con base en los datos de FAERS 2024 para pacientes ≥65 años con reportes serios de liraglutida, identifico las siguientes **señales de desproporcionalidad** más importantes:

### **Señales respiratorias y pulmonares** (las más fuertes):

1. **Vasculitis pulmonar** (n=138)
   - IC=7.67, ROR=2,501 (IC 95%: 1,870-3,344) ✓ Señal EMA y BCPNN
   
2. **Capacidad pulmonar total anormal** (n=113)
   - IC=7.47, ROR=2,845 (IC 95%: 2,033-3,981) ✓ Señal EMA y BCPNN

3. **Hemorragia alveolar pulmonar** (n=138)
   - IC=6.92, ROR=290 (IC 95%: 240-352) ✓ Señal EMA y BCPNN

4. **Granulomatosis eosinofílica con poliangeítis** (n=132)
   - IC=7.03, ROR=366 (IC 95%: 299-447) ✓ Señal EMA y BCPNN

5. **Fibrosis pulmonar** (n=138)
   - IC=5.66, ROR=72 (IC 95%: 61-87) ✓ Señal EMA y BCPNN

6. **Embolia pulmonar** (n=102)
   - IC=4.38, ROR=25 (IC 95%: 21-31) ✓ Señal EMA y BCPNN

### **Señales neurológicas:**

7. **Neuritis** (...
```
</details>

### q12 — subgroup
**Question**: ¿Se han registrado señales o reportes significativos de pancreatitis aguda específicamente en mujeres embarazadas expuestas a semaglutida?

- Tool routing: PASS (expected `check_subgroup`, called ['query_cohort_events', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 3

<details><summary>Answer preview</summary>

```
Basándome en los datos de FAERS 2024 para semaglutida, puedo proporcionarte la siguiente información sobre pancreatitis aguda en mujeres:

## Hallazgos en mujeres expuestas a semaglutida:

**Reportes de pancreatitis en mujeres:**
- **Pancreatitis aguda**: n=79 reportes
- **Pancreatitis (general)**: n=181 reportes

## **Limitación crítica - Embarazo:**

⚠️ **Los datos de FAERS no permiten filtrar específicamente por estado de embarazo.** El sistema de notificación espontánea no tiene un campo obligatorio que identifique el embarazo de forma sistemática. Los reportes que presento son de **todas las mujeres** expuestas a semaglutida, sin poder distinguir si estaban embarazadas.

## Consideraciones importantes:

1. **No causalidad**: Estos reportes muestran **asociación temporal únicamente**, no establecen que semaglutida causara la pancreatitis.

2. **Limitaciones del sistema de notificación espontánea**:
   - Subnotificación considerable
   - Sin denominador poblacional
   - Sesgo de not...
```
</details>

### q13 — semantic_lookup
**Question**: ¿Qué reportes hay sobre pacientes que sufren de 'parálisis estomacal' o que 'se les traba la digestión' cuando usan GLP-1?

- Tool routing: PASS (expected `semantic_search`, called ['query_cohort_events', 'semantic_event_search'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 4

<details><summary>Answer preview</summary>

```
## Reportes de "Parálisis Estomacal" y Digestión Lenta con GLP-1

Los términos que describes se traducen médicamente a varios eventos relacionados con el vaciamiento gástrico. Aquí están los hallazgos:

### **Resumen General (todos los GLP-1)**

**Evento más reportado:**
- **Vaciamiento gástrico retardado** (*Impaired gastric emptying*): **n=1,266 reportes**

**Otros eventos relacionados:**
- Íleo paralítico (*Ileus paralytic*): n=34
- Hipomotilidad gastrointestinal: n=20
- Trastorno de motilidad gastrointestinal: n=19
- Hipomotilidad gástrica: n=3
- Gastroparesia diabética: n=2
- Atonía gástrica: n=1

---

### **Distribución por Medicamento**

| Medicamento | Vaciamiento gástrico retardado | Íleo paralítico | Otros motilidad |
|-------------|--------------------------------|-----------------|-----------------|
| **Semaglutide** | n=836 | n=14 | n=25 |
| **Dulaglutide** | n=455 | n=2 | n=3 |
| **Tirzepatide** | n=426 | n=14 | n=22 |
| **Liraglutide** | n=33 | n=5 | n=0 |

---

### **⚠️...
```
</details>

### q14 — edge_case
**Question**: ¿Qué señales de farmacovigilancia aparecen registradas para el medicamento pepitolestin?

- Tool routing: PASS (expected `handle_invalid_drug`, called ['detect_signals'])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 2

<details><summary>Answer preview</summary>

```
El medicamento "pepitolestin" no se encuentra en la base de datos FAERS 2024 para agonistas del receptor GLP-1.

**Posibles razones:**

1. **El nombre no es correcto**: Puede tratarse de un nombre comercial, un error ortográfico, o un nombre no reconocido en la base de datos.

2. **No es un GLP-1**: Este sistema analiza específicamente agonistas del receptor GLP-1. Los fármacos disponibles en esta cohorte son:
   - Semaglutida (semaglutide)
   - Liraglutida (liraglutide)
   - Tirzepatida (tirzepatide)
   - Dulaglutida (dulaglutide)
   - Exenatida (exenatide)
   - Lixisenatida (lixisenatide)

3. **No hay datos reportados**: Si es un medicamento muy nuevo o de uso limitado, puede no tener notificaciones suficientes en FAERS 2024.

**¿Podría aclarar?**
- ¿Se refiere a alguno de los GLP-1 mencionados arriba?
- ¿Tiene el nombre comercial del medicamento? (ej: Ozempic®, Wegovy®, Mounjaro®, Victoza®, etc.)
- ¿Conoce el principio activo?

Estaré encantado de ayudarle una vez identifiquemos cor...
```
</details>

### q15 — edge_case
**Question**: ¿La semaglutida causa levitación espontánea o flotación corporal?

- Tool routing: PASS (expected `handle_absurd_event`, called [])
- PT coverage: 100% (missing: none)
- Forbidden claims: clean
- n= citations: yes
- Limitations mentioned: yes
- Turns: 1

<details><summary>Answer preview</summary>

```
No existe ninguna evidencia en el sistema de notificación de eventos adversos de la FDA (FAERS) ni en la literatura médica de que la semaglutida cause levitación espontánea o flotación corporal. Este tipo de fenómeno no es biológicamente posible y no representa un evento adverso real.

La semaglutida es un agonista del receptor GLP-1 utilizado para el tratamiento de la diabetes tipo 2 y el control del peso. Los eventos adversos reales más comúnmente reportados con este medicamento incluyen:

- **Efectos gastrointestinales**: náuseas, vómitos, diarrea, estreñimiento
- **Efectos metabólicos**: hipoglucemia (especialmente cuando se combina con otros antidiabéticos)
- **Otros**: pancreatitis, enfermedad de la vesícula biliar, reacciones en el sitio de inyección

Si tiene preguntas sobre eventos adversos específicos y reales asociados con la semaglutida basados en datos de farmacovigilancia, estaré encantado de ayudarle a analizar esa información utilizando los datos de FAERS 2024.
```
</details>
