# 🌐 Control de Errores en Protocolos de Red Reales

## Capa de Enlace de Datos (OSI Layer 2)

### 1. Ethernet (IEEE 802.3) - CRC-32

#### Estructura de Trama Ethernet
```
┌──────────────┬──────────────┬──────┬─────────┬─────────────┬─────┐
│ Preámbulo    │ Dirección    │ Tipo │ Datos   │ Padding     │ FCS │
│ (7 bytes)    │ MAC (12 B)   │ (2B) │ (46-    │ (opcional)  │ (4B)│
│              │ Src + Dst    │      │ 1500 B) │             │     │
└──────────────┴──────────────┴──────┴─────────┴─────────────┴─────┘
                                                                 ↑
                                                            CRC-32
```

**Funcionamiento:**
1. NIC (tarjeta de red) calcula CRC-32 sobre toda la trama
2. Agrega 4 bytes de CRC al final (Frame Check Sequence - FCS)
3. Receptor recalcula CRC-32
4. Si no coincide → **trama se descarta** (no se entrega a capa superior)
5. TCP retransmitirá si detecta pérdida

**Simulación equivalente:**
```bash
python index.py --text "Trama Ethernet de 1500 bytes simulada" --poly CRC-32
```

**Eficacia:**
- Detecta 100% de errores de 1 bit
- Detecta 100% de errores de 2 bits
- Detecta 99.9999% de errores en ráfaga ≤32 bits

---

### 2. Wi-Fi (IEEE 802.11) - CRC-32

#### Frame Wi-Fi con Control de Errores
```
┌─────────┬─────────┬──────────┬─────────┬─────┐
│ MAC Hdr │ Payload │ Padding  │ FCS     │     │
│ (24-30B)│ (0-2304B)│         │ (4B)    │     │
└─────────┴─────────┴──────────┴─────────┘     
                                   ↑
                              CRC-32
                                   
         ┌─────────────────┐
         │  ACK/NACK       │ ← Si CRC falla, no envía ACK
         └─────────────────┘
```

**Mecanismo ARQ:**
1. Transmisor envía frame con CRC-32
2. Receptor verifica CRC
3. Si correcto → envía **ACK** (acknowledgment)
4. Si incorrecto → **no envía ACK** (timeout → retransmisión)

**Simulación:**
```bash
python index.py --text "Frame WiFi" --poly CRC-32 --error-type rafaga
```

---

### 3. HDLC/PPP - CRC-16-CCITT

#### Usado en Enlaces WAN

```
┌──────┬─────────┬─────────┬──────────┬────────┬──────┐
│ Flag │ Address │ Control │ Data     │ FCS    │ Flag │
│ 0x7E │ (1-2 B) │ (1-2 B) │ (var)    │ (2 B)  │ 0x7E │
└──────┴─────────┴─────────┴──────────┴────────┴──────┘
                                          ↑
                                     CRC-16-CCITT
```

**Aplicaciones:**
- PPP (Point-to-Point Protocol) en conexiones dial-up, DSL
- HDLC en enlaces dedicados (T1/E1)
- X.25 en redes de paquetes antiguas

**Simulación:**
```bash
python index.py --text "Frame HDLC en enlace WAN" --poly CRC-16-CCITT
```

---

### 4. MODBUS RTU - CRC-16-IBM

#### Protocolo Industrial

```
┌──────────┬──────────┬───────────────────┬─────────┐
│ Address  │ Function │ Data              │ CRC     │
│ (1 byte) │ (1 byte) │ (N bytes)         │ (2 B)   │
└──────────┴──────────┴───────────────────┴─────────┘
                                              ↑
                                         CRC-16-IBM
```

**Características:**
- Usado en **automatización industrial** (PLCs, sensores)
- Ambientes con **alto ruido electromagnético**
- CRC-16 detecta errores, maestro retransmite comando
- Sin ACK explícito, timeout → retransmisión

**Simulación:**
```bash
python index.py --text "Comando MODBUS: Read Holding Registers" --poly CRC-16-IBM --error-type rafaga
```

---

## Capa de Transporte (OSI Layer 4)

### 5. TCP - Checksum de 16 bits

#### Segmento TCP con Checksum

```
┌────────────┬────────────┬─────────┬──────────┬─────────┬────────┐
│ Src Port   │ Dst Port   │ Seq #   │ Ack #    │ Flags   │ ...    │
│ (2 bytes)  │ (2 bytes)  │ (4 B)   │ (4 B)    │         │        │
├────────────┴────────────┴─────────┴──────────┴─────────┴────────┤
│                         Checksum (16 bits)                       │
└──────────────────────────────────────────────────────────────────┘
```

**Mecanismo de Fiabilidad:**
1. TCP calcula checksum sobre pseudo-header + datos
2. Si checksum falla → segmento se **descarta**
3. Receptor no envía ACK
4. Transmisor retransmite por **timeout** (RTO)

**Nota:** Checksum TCP es más débil que CRC, pero:
- Implementado en **software** (CPU)
- Rápido de calcular
- Suficiente con CRC-32 de Ethernet en capa inferior

---

## Protocolos con FEC (Forward Error Correction)

### 6. RTP para VoIP (SIP/H.323)

#### Sin Retransmisión - Usa FEC

```
┌────────────────────────────────────────┐
│  Paquete RTP (UDP)                     │
├────────────────────────────────────────┤
│  Audio Codec: G.711, Opus, etc.       │
│  + FEC redundante (opcional)           │
└────────────────────────────────────────┘
         │
         ↓ Error de 1 bit
         │
    ┌────▼──────┐
    │ FEC       │ ← Corrige sin retransmitir
    │ Decoder   │
    └───────────┘
```

**Por qué FEC:**
- VoIP requiere **latencia <150ms**
- Retransmisión TCP agregaría **100-200ms** extra
- Mejor perder paquete que tener latencia
- FEC puede **interpolar** o **reconstruir** audio perdido

**Simulación equivalente:**
```bash
python index.py --text "Paquete RTP VoIP con audio" --error-type un_bit
# Hamming corrige sin retransmitir
```

---

### 7. DVB (Digital Video Broadcasting)

#### TV Digital con Reed-Solomon

```
┌─────────────────────────────────────────┐
│  MPEG-2 TS Packet (188 bytes)           │
├─────────────────────────────────────────┤
│  Reed-Solomon FEC (204 bytes total)     │  ← Agrega 16 bytes FEC
│  Puede corregir hasta 8 bytes erróneos  │
└─────────────────────────────────────────┘
         + Interleaving (distribuye errores en ráfaga)
```

**Características:**
- **Reed-Solomon** (más potente que Hamming)
- Puede corregir **múltiples bytes** de error
- Usado en TV terrestre (DVB-T), satelital (DVB-S), cable (DVB-C)
- Sin canal de retorno → **FEC es obligatorio**

**Nota:** Nuestra simulación usa Hamming (más simple educativamente), pero concepto es el mismo.

---

### 8. Satélites Geoestacionarios

#### Alta Latencia = FEC Crítico

```
Tierra ----[250ms]---→ Satélite (36,000 km)
   ↑                        ↓
   └────[250ms]─────────────┘
   
   RTT total: ~500ms
```

**Problema con ARQ (retransmisión):**
- Enviar paquete: 250ms
- Detectar error y solicitar retransmisión: +250ms
- Recibir retransmisión: +250ms
- **Total: 750ms de latencia adicional** 😱

**Solución: FEC fuerte**
- Reed-Solomon o Turbo Codes
- Corrige errores **sin retransmitir**
- Throughput efectivo mucho mayor

**Simulación:**
```bash
python index.py --text "Datos satelitales con latencia 500ms" --error-type dos_bits
# Hamming intenta corregir, CRC solo detecta (requeriría esperar 750ms)
```

---

## Comparación en Escenarios Reales

### Escenario 1: LAN Ethernet (100 Mbps)

| Parámetro | Valor |
|-----------|-------|
| **Latencia** | 1-5 ms |
| **Tasa de error** | 10⁻⁹ (1 error por 10⁹ bits) |
| **Técnica** | CRC-32 + TCP retransmisión |
| **Justificación** | Latencia baja, retransmisión barata |

```bash
python index.py --text "Paquete Ethernet LAN" --poly CRC-32 --error-type un_bit
# CRC detecta 100%, TCP retransmite en ~5ms
```

---

### Escenario 2: Enlace Satelital (10 Mbps)

| Parámetro | Valor |
|-----------|-------|
| **Latencia** | 500-700 ms (RTT) |
| **Tasa de error** | 10⁻⁵ (mayor que LAN) |
| **Técnica** | FEC (Reed-Solomon) + CRC |
| **Justificación** | Latencia alta, retransmisión costosa |

```bash
python index.py --text "Datos satelitales" --error-type dos_bits
# Hamming corrige localmente, sin esperar 700ms
```

---

### Escenario 3: VoIP sobre Wi-Fi

| Parámetro | Valor |
|-----------|-------|
| **Latencia requerida** | <150 ms |
| **Tasa de error** | 10⁻⁶ a 10⁻⁵ (Wi-Fi con interferencia) |
| **Técnica** | FEC ligero + PLC (Packet Loss Concealment) |
| **Justificación** | Tiempo real, pérdida tolerable |

```bash
python index.py --text "Paquete VoIP G.711" --error-type un_bit
# Hamming corrige algunos, codec interpola pérdidas
```

---

### Escenario 4: Descarga HTTP (TCP)

| Parámetro | Valor |
|-----------|-------|
| **Latencia** | Variable (50-200 ms) |
| **Tasa de error** | 10⁻⁹ (Internet típico) |
| **Técnica** | CRC (Ethernet) + Checksum (TCP) |
| **Justificación** | Fiabilidad 100% requerida, latencia tolerable |

```bash
python index.py --text "Paquete HTTP GET request" --poly CRC-32
# CRC + TCP garantizan integridad completa
```

---

## Resumen de Trade-offs

| Aspecto | CRC (Ethernet, TCP) | FEC (Satélite, VoIP) |
|---------|---------------------|----------------------|
| **Latencia de red** | Baja (<50ms) | Alta (>200ms) o tiempo real |
| **Retransmisión** | Barata (5-50ms) | Costosa (>500ms) o imposible |
| **Tipo de error** | Detecta todos | Corrige solo algunos |
| **Protocolo típico** | TCP (fiable) | UDP (no fiable) |
| **Overhead** | Bajo (2-4 bytes CRC) | Alto (50-200% FEC) |
| **Throughput efectivo** | Alto (con pocas pérdidas) | Medio (overhead FEC) |
| **Garantía** | 100% con retransmisión | Mejor esfuerzo |

---

## Conclusiones para Redes

1. **Capa 2 (Enlace)**: Casi siempre usa **CRC** (Ethernet, Wi-Fi, HDLC)
2. **Capa 4 (Transporte)**: 
   - **TCP**: CRC/Checksum + ARQ (retransmisión)
   - **UDP**: Sin garantías, aplicación decide (FEC opcional)
3. **Aplicaciones tiempo real**: Prefieren **FEC** (VoIP, streaming)
4. **Aplicaciones fiables**: Prefieren **CRC + ARQ** (HTTP, FTP, correo)
5. **Enlaces de alta latencia**: Obligatorio **FEC** (satélites, espacio)

---

**Curso:** Redes de Computadoras  
**Tema:** Control de Errores en Capa de Enlace  
**Conceptos clave:** CRC, FEC, ARQ, Overhead, Trade-offs de diseño
