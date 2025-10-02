# Simulación CRC vs FEC (Hamming) - Redes de Computadoras

## 📡 Descripción
Simulación educativa avanzada para comparar técnicas de **control de errores en redes**:
- **CRC (Cyclic Redundancy Check)**: Detección de errores usado en Ethernet, Wi-Fi, TCP/IP
- **FEC (Forward Error Correction) - Hamming**: Corrección de errores usado en transmisiones satelitales, VoIP

### 🎓 Contexto Académico
**Curso:** Redes de Computadoras - Quinto Semestre  
**Tema:** Capa de Enlace de Datos - Control de Errores  
**Conceptos:** Detección vs Corrección, ARQ, FEC, Overhead de protocolos

## Mejoras Implementadas

### 1. ✅ Optimización de CRC con Tabla de Lookup
- **Implementación de tabla precalculada** para acelerar cálculos CRC
- Método tradicional bit a bit disponible como fallback
- **Mejora de rendimiento**: ~2-5x más rápido en operaciones repetitivas

### 2. ✅ Múltiples Tipos de Errores
Se pueden simular tres tipos de errores realistas:
- **`un_bit`**: Error de un solo bit (más común)
- **`dos_bits`**: Errores de dos bits simultáneos
- **`rafaga`**: Error en ráfaga (burst error) - 3 bits consecutivos

Esto permite evaluar mejor las capacidades reales de detección/corrección:
- CRC detecta bien errores de 1 bit y muchos de múltiples bits
- Hamming corrige 1 bit pero solo detecta 2 bits

### 3. ✅ Estadísticas Detalladas
Nuevas métricas implementadas:
- **Tasa de detección/corrección** (%)
- **Overhead de bits** (bits adicionales necesarios)
- **Eficiencia** (ratio datos útiles / datos totales)
- **Throughput** (MB/s)
- **Tasas de falsos positivos/negativos**

### 4. ✅ Soporte para Múltiples Polinomios CRC
Polinomios predefinidos usados en protocolos de red reales:
- **CRC-8**: 0b100000111 (I2C, 1-Wire, sensores)
- **CRC-16-IBM**: 0x18005 (MODBUS RTU - automatización industrial)
- **CRC-16-CCITT**: 0x11021 (XMODEM, Bluetooth, HDLC, X.25)
- **CRC-32**: 0x104C11DB7 (Ethernet IEEE 802.3, ZIP, PNG, MPEG-2)

**Aplicación en protocolos reales:**
- 🌐 **Ethernet**: Cada trama termina con CRC-32 de 4 bytes
- 📡 **Wi-Fi (802.11)**: CRC para verificar integridad de frames
- 🔗 **HDLC/PPP**: Protocolos de enlace punto a punto con CRC-16
- 🏭 **MODBUS**: Comunicación industrial con CRC-16-IBM

### 5. ✅ Visualización con Gráficos (Opcional)
Si matplotlib y numpy están instalados:
- Gráficos comparativos de tiempos
- Gráficos de throughput
- Comparación de tasas de detección/corrección
- Visualización de overhead y eficiencia
- Resumen visual integrado

## Uso

### Modo Terminal

#### Simulación básica con texto:
```powershell
python index.py --text "Hola CRC y Hamming"
```

#### Con tipo de error específico:
```powershell
python index.py --text "Prueba" --error-type dos_bits
```

#### Con polinomio CRC diferente:
```powershell
python index.py --text "Test" --poly CRC-16-IBM
```

#### Simulación con errores en ráfaga:
```powershell
python index.py --text "Mensaje largo para probar" --error-type rafaga --sleep-ms 1
```

#### Benchmark de rendimiento:
```powershell
python index.py --byte 65 --iters 100000 --poly CRC-8
```

### Modo GUI

```powershell
python gui.py
```

Características de la GUI:
1. Selector de texto a transmitir
2. Selector de polinomio CRC (dropdown con opciones predefinidas)
3. Selector de tipo de error (un_bit, dos_bits, rafaga)
4. Control de velocidad de animación (sleep ms)
5. Barras de progreso en tiempo real
6. Panel de métricas detalladas
7. Botón "Ver Gráficos" para análisis visual (requiere matplotlib)

## Argumentos de Línea de Comandos

```
--text TEXT             Texto a simular (UTF-8)
--poly POLY            Polinomio CRC: nombre predefinido o valor (ej. 0x107, 0b100000111)
--byte BYTE            Modo benchmark: valor 0-255 para probar
--iters ITERS          Número de iteraciones para benchmark (default: 100000)
--sleep-ms SLEEP       Retardo artificial en ms para visualización
--error-type TYPE      Tipo de error: un_bit, dos_bits, rafaga
```

## Instalación de Dependencias

### Básico (sin gráficos):
```powershell
# No requiere dependencias adicionales, usa solo bibliotecas estándar
```

### Con visualización (gráficos):
```powershell
pip install matplotlib numpy
```

## Resultados de Ejemplo

### Comparación con Error de 1 Bit:
```
RESUMEN DETALLADO DE LA SIMULACIÓN
================================================================================
Tipo de error simulado: un_bit
Total de bytes procesados: 20

--- CRC-8 ---
  Tiempo:           0.523 ms
  Throughput:       36.421 MB/s
  Errores detectados: 20/20 (100.0%)
  No detectados:    0/20
  Overhead:         160 bits (100.0%)
  Eficiencia:       50.00%

--- Hamming (12,8) ---
  Tiempo:           0.687 ms
  Throughput:       27.735 MB/s
  Errores corregidos: 20/20 (100.0%)
  No corregibles:   0/20
  Overhead:         80 bits (50.0%)
  Eficiencia:       66.67%

--- Comparación ---
  Más rápido: CRC-8 (31.4% más rápido)
  Capacidad de detección CRC: 100.0%
  Capacidad de corrección Hamming: 100.0%
```

### Comparación con Errores en Ráfaga:
```
--- CRC-8 ---
  Errores detectados: 18/20 (90.0%)  # CRC puede fallar con burst errors
  
--- Hamming (12,8) ---
  Errores corregidos: 5/20 (25.0%)   # Hamming solo corrige 1 bit
  No corregibles:   15/20
```

## 🎓 Análisis Técnico para Redes

### Ventajas de CRC (usado en TCP/IP, Ethernet):
- ✅ Más rápido en procesamiento
- ✅ Excelente detección de errores (99.9%+)
- ✅ Detecta errores en ráfaga (comunes en redes por ruido)
- ✅ **Implementado en hardware** en tarjetas de red (NICs)
- ✅ Compatible con **ARQ (retransmisión automática)**
- ❌ No puede corregir errores (TCP retransmite, Ethernet descarta)
- ❌ Mayor overhead (100-400% dependiendo del tamaño)

### Ventajas de Hamming (usado en VoIP, streaming):
- ✅ Puede corregir errores de 1 bit **sin retransmisión**
- ✅ Menor overhead (50% para Hamming 12,8)
- ✅ Mayor eficiencia en ancho de banda
- ✅ Ideal para **UDP en tiempo real** (sin ACKs)
- ✅ Usado en **transmisiones satelitales** (latencia 250-500ms)
- ❌ Solo corrige 1 bit, detecta 2 bits
- ❌ Falla con errores múltiples o en ráfaga
- ❌ Más lento computacionalmente

### Casos de Uso en Protocolos de Red:

**CRC** es mejor para:
- 🌐 **Ethernet (IEEE 802.3)**: CRC-32 en cada trama (14-1518 bytes)
- 🔗 **TCP/IP**: Checksum en cabeceras, retransmisión si falla
- 📡 **Wi-Fi (IEEE 802.11)**: CRC en frames, ACK/NACK
- 🏭 **MODBUS RTU**: CRC-16 en comunicación industrial
- 💾 **Protocolos de almacenamiento**: Verificación de integridad
- 📞 **HDLC, PPP, X.25**: Protocolos de enlace de datos WAN

**Hamming** es mejor para:
- 🛰️ **Comunicaciones satelitales**: Latencia round-trip 500ms+, retransmisión costosa
- 📹 **Streaming de video/audio UDP**: Netflix, YouTube en vivo, Twitch
- 🎮 **Gaming online (UDP)**: CS:GO, Fortnite, latencia <50ms crítica
- 📻 **VoIP (SIP/RTP)**: Skype, WhatsApp calls, Zoom
- 🚀 **Transmisiones espaciales**: Comunicación con sondas (Mars Rover)
- 📺 **DVB (Digital Video Broadcasting)**: TV digital terrestre/satélite

### Comparación en Escenarios de Red:

| Escenario | Protocolo | Técnica | Razón |
|-----------|-----------|---------|-------|
| LAN Ethernet | TCP/IP | CRC-32 | Baja latencia, fácil retransmitir |
| Descarga HTTP | TCP | CRC/Checksum | Integridad garantizada con ACK |
| Videollamada | UDP/RTP | FEC (Reed-Solomon) | Sin tiempo para retransmisión |
| Enlace satelital | Custom | FEC fuerte | RTT 500ms, retransmisión costosa |
| Gaming online | UDP | Ninguno/FEC ligero | Latencia crítica <50ms |
| MODBUS industrial | Serial | CRC-16 | Ambientes ruidosos, detección robusta |

## Estructura del Código

```
.
├── index.py           # Módulo principal con lógica de simulación
├── gui.py            # Interfaz gráfica Tkinter
├── visualizacion.py  # Módulo de gráficos (opcional)
└── README.md         # Este archivo
```

## Autor
Simulación educativa para curso de **Redes de Computadoras**  
Universidad - Quinto Semestre - Primer Parcial

## Referencias de Protocolos Reales
- **IEEE 802.3** (Ethernet): Uso de CRC-32
- **RFC 793** (TCP): Checksum en segmentos
- **RFC 768** (UDP): Checksum opcional
- **ISO 13239** (HDLC): CRC-16 en frames
- **Hamming Codes**: Teoría de códigos correctores de errores

## Licencia
Uso educativo - Aprendizaje de control de errores en redes
