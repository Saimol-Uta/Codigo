# 🎯 Guía de Uso Rápida - Simulación CRC vs Hamming
## Control de Errores en Redes de Computadoras

### 🌐 Contexto
Esta simulación demuestra dos técnicas fundamentales de control de errores en la **Capa de Enlace de Datos (Capa 2 OSI)**:
- **CRC**: Detección de errores (usado en Ethernet, Wi-Fi, HDLC)
- **Hamming (FEC)**: Corrección de errores (usado en enlaces satelitales, VoIP)

## Inicio Rápido

### 1. Simulación Básica (Terminal)
```bash
python index.py --text "Mi mensaje de prueba"
```

### 2. Interfaz Gráfica
```bash
python gui.py
```

### 3. Ejemplos Guiados
```bash
python ejemplos.py
```

### 4. Pruebas de Validación
```bash
python test_mejoras.py
```

---

## Casos de Uso en Redes Reales

### 🌐 Simular Trama Ethernet con CRC-32
```bash
python index.py --text "Trama Ethernet simulada" --poly CRC-32 --error-type un_bit
```
**Contexto:** Ethernet IEEE 802.3 usa CRC-32 al final de cada trama  
**Resultado esperado:** CRC detecta 100% de errores, trama se descarta si falla

### 📡 Simular Frame Wi-Fi con Errores de Interferencia
```bash
python index.py --text "Frame WiFi 802.11" --poly CRC-16-CCITT --error-type dos_bits
```
**Contexto:** Wi-Fi usa CRC para verificar frames, interferencia causa errores múltiples  
**Resultado esperado:** CRC detecta ~100%, Wi-Fi solicita retransmisión

### 🛰️ Simular Enlace Satelital con FEC
```bash
python index.py --text "Datos satelitales con alta latencia" --error-type un_bit
```
**Contexto:** Satélites tienen RTT de 500ms, retransmisión es costosa  
**Resultado esperado:** Hamming corrige errores sin retransmitir (ideal para este caso)

### 📹 Simular Streaming de Video (UDP)
```bash
python index.py --text "Paquete de video H.264" --error-type rafaga
```
**Contexto:** Netflix/YouTube usan UDP con FEC, no hay tiempo para retransmitir  
**Resultado esperado:** Hamming corrige algunos, pero errores en ráfaga causan pérdida

### 🏭 Simular MODBUS Industrial
```bash
python index.py --text "Comando MODBUS" --poly CRC-16-IBM --error-type rafaga
```
**Contexto:** MODBUS RTU usa CRC-16 en ambientes industriales ruidosos  
**Resultado esperado:** CRC detecta errores en ráfaga, maestro retransmite comando

### 🔗 Simular Protocolo HDLC (WAN)
```bash
python index.py --text "Frame HDLC" --poly CRC-16-CCITT --error-type dos_bits
```
**Contexto:** HDLC/PPP usa CRC-16 en enlaces punto a punto  
**Resultado esperado:** CRC detecta, protocolo retransmite frame

---

## Casos de Uso Comunes

### 📡 Simular Transmisión en Red con Errores Aleatorios
```bash
python index.py --text "Paquete de red" --error-type un_bit
```
**Resultado esperado:** CRC y Hamming detectan/corrigen ~100%

### 💿 Simular Errores en Disco (Burst Errors)
```bash
python index.py --text "Datos en disco duro" --error-type rafaga
```
**Resultado esperado:** CRC detecta ~100%, Hamming corrige ~60-70%

### 📻 Simular Interferencia Electromagnética
```bash
python index.py --text "Transmision por radio" --error-type dos_bits
```
**Resultado esperado:** CRC detecta ~100%, Hamming corrige ~75%

### 🔧 Probar Diferentes Protocolos CRC
```bash
# MODBUS (RTU)
python index.py --text "MODBUS" --poly CRC-16-IBM

# XMODEM / Bluetooth
python index.py --text "XMODEM" --poly CRC-16-CCITT

# Ethernet / ZIP
python index.py --text "Ethernet" --poly CRC-32
```

### ⚡ Benchmark de Rendimiento
```bash
# Comparar velocidad con 100,000 iteraciones
python index.py --byte 65 --iters 100000
```

### 🎬 Visualización Lenta (Demostración)
```bash
# Ralentizar para presentaciones
python index.py --text "Demo" --sleep-ms 200
```

---

## Parámetros de Línea de Comandos

### `--text TEXT`
Texto a transmitir y simular errores.
```bash
python index.py --text "Hola mundo"
```

### `--error-type TYPE`
Tipo de error a simular:
- `un_bit` - Error de 1 bit (defecto)
- `dos_bits` - Error de 2 bits
- `rafaga` - Error en ráfaga (3 bits)

```bash
python index.py --text "Test" --error-type rafaga
```

### `--poly POLYNOMIAL`
Polinomio CRC a usar:
- `CRC-8` (defecto)
- `CRC-16-IBM`
- `CRC-16-CCITT`
- `CRC-32`
- O valor custom: `0x107`, `0b100000111`

```bash
python index.py --text "Test" --poly CRC-32
```

### `--byte BYTE` y `--iters N`
Modo benchmark con un byte específico:
```bash
python index.py --byte 65 --iters 50000
```

### `--sleep-ms MS`
Retardo artificial para visualización:
```bash
python index.py --text "Demo" --sleep-ms 100
```

---

## Uso de la GUI

### Elementos de la Interfaz

1. **Campo de texto:** Mensaje a transmitir
2. **Polinomio CRC:** Selector de polinomio
3. **Tipo de error:** Selector de tipo de error
4. **Sleep ms:** Control de velocidad de animación
5. **Botón "Ejecutar":** Inicia simulación
6. **Botón "Ver Gráficos":** Muestra análisis visual (requiere matplotlib)

### Flujo de Trabajo GUI

1. Escribir texto en el campo
2. Seleccionar polinomio CRC (o dejar CRC-8)
3. Seleccionar tipo de error
4. Clic en "Ejecutar"
5. Observar barras de progreso
6. Revisar métricas finales
7. (Opcional) Clic en "Ver Gráficos"

---

## Interpretación de Resultados

### Métricas Principales

#### Tiempo (ms)
Tiempo total de procesamiento. **Menor es mejor.**
- CRC suele ser más rápido con 1 bit
- Hamming puede ser más rápido con texto largo

#### Throughput (MB/s)
Velocidad de procesamiento. **Mayor es mejor.**
```
Throughput = Bytes procesados / Tiempo (segundos)
```

#### Tasa de Detección/Corrección (%)
- **CRC:** % de errores detectados
- **Hamming:** % de errores corregidos

**Objetivo:** 100% en ambos casos ideales

#### Overhead (%)
Porcentaje de bits adicionales necesarios.
- CRC-8: 100% (duplica el tamaño)
- CRC-16: 200% (triplica el tamaño)
- CRC-32: 400% (quintuplica el tamaño)
- Hamming (12,8): 50% (1.5x el tamaño)

**Menor es mejor** para eficiencia de ancho de banda.

#### Eficiencia (%)
Porcentaje de bits que son datos útiles.
```
Eficiencia = (Bits de datos / Bits totales) × 100
```

**Mayor es mejor.**

---

## Escenarios de Comparación

### Escenario 1: Canal Confiable (Pocos Errores)
```bash
python index.py --text "Canal confiable" --error-type un_bit
```
**Resultado:** Ambos funcionan bien, elegir por velocidad.

### Escenario 2: Canal Ruidoso (Muchos Errores)
```bash
python index.py --text "Canal ruidoso con interferencias" --error-type rafaga
```
**Resultado:** CRC superior en detección, Hamming falla en corrección.

### Escenario 3: Sin Retransmisión Posible
**Contexto:** Satélite con 5 minutos de latencia
```bash
python index.py --text "Datos satelitales" --error-type un_bit
```
**Decisión:** Hamming - puede corregir sin retransmitir.

### Escenario 4: Con Retransmisión Disponible
**Contexto:** Red Ethernet local
```bash
python index.py --text "Paquete Ethernet" --poly CRC-32 --error-type un_bit
```
**Decisión:** CRC-32 - detecta y retransmite si hay error.

---

## Solución de Problemas

### Error: "python no se reconoce"
**Solución:** Usar ruta completa o `py`:
```bash
py index.py --text "Test"
```

### Error: "matplotlib no encontrado"
**Solución:** Instalar dependencias opcionales:
```bash
pip install matplotlib numpy
```
O usar sin gráficos (funcionalidad básica disponible).

### Error: "AssertionError" o cálculos incorrectos
**Solución:** Ejecutar pruebas de validación:
```bash
python test_mejoras.py
```

### GUI no responde
**Causa:** Simulación muy larga o muchas iteraciones
**Solución:** 
- Reducir tamaño del texto
- Usar `--sleep-ms 0` para máxima velocidad
- Click en "Detener" si es necesario

---

## Preguntas Frecuentes

### ¿Cuándo usar CRC? (Protocolos típicos)
- ✅ **Ethernet (802.3)** - Detección en LAN, descarta trama errónea
- ✅ **TCP/IP** - Checksum + retransmisión automática (ARQ)
- ✅ **Wi-Fi (802.11)** - Detección en WLAN, solicita reenvío
- ✅ **HDLC/PPP** - Enlaces punto a punto WAN
- ✅ **MODBUS** - Comunicación industrial con ruido

### ¿Cuándo usar Hamming? (Protocolos típicos)
- ✅ **Satélites** - Latencia alta (500ms RTT), retransmisión costosa
- ✅ **VoIP (RTP/UDP)** - Tiempo real, sin retransmisión
- ✅ **Streaming (UDP)** - Netflix, YouTube, Twitch
- ✅ **Gaming (UDP)** - Latencia <50ms crítica
- ✅ **DVB** - TV digital terrestre/satélite

### ¿Puedo combinar ambos?
Sí, en sistemas reales a veces se combinan:
- **FEC (Hamming/Reed-Solomon)** para corrección de errores simples
- **CRC** para detección de errores graves que FEC no puede corregir
- **Ejemplo 1**: DVB usa Reed-Solomon (FEC) + CRC
- **Ejemplo 2**: Algunos protocolos satelitales usan FEC + ARQ híbrido
- **Ejemplo 3**: Memoria ECC (Hamming) + CRC en disco duro

### ¿Qué polinomio CRC elegir?
Depende de tu aplicación:
- **CRC-8:** Sensores, I2C, dispositivos simples
- **CRC-16:** MODBUS, XMODEM, protocolos seriales
- **CRC-32:** Ethernet, ZIP, almacenamiento

---

## Recursos Adicionales

### Archivos Incluidos
- `index.py` - Simulación principal
- `gui.py` - Interfaz gráfica
- `visualizacion.py` - Módulo de gráficos
- `test_mejoras.py` - Suite de pruebas
- `ejemplos.py` - Ejemplos guiados
- `README.md` - Documentación completa
- `MEJORAS.md` - Resumen de mejoras

### Documentación Externa
- CRC: https://en.wikipedia.org/wiki/Cyclic_redundancy_check
- Hamming: https://en.wikipedia.org/wiki/Hamming_code
- Error Control: https://en.wikipedia.org/wiki/Error_detection_and_correction

---

**Versión:** 2.0 (Mejorada)  
**Fecha:** Octubre 2025  
**Soporte:** Uso educativo
