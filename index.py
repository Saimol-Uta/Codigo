import time
import random
import sys
import argparse
import threading
from dataclasses import dataclass

# --- IMPLEMENTACIÓN DE CRC-8 ---

# Polinomio Generador: x^8 + x^2 + x + 1  => 100000111
# El '1' más significativo se asume, por lo que usamos 0x07 (00000111) en algunas implementaciones,
# pero aquí haremos la división larga explícita para mayor claridad.
POLINOMIO_CRC = 0b100000111

# Polinomios CRC adicionales comunes
POLINOMIOS_CRC = {
    'CRC-8': 0b100000111,      # x^8 + x^2 + x + 1
    'CRC-8-CCITT': 0b100000111,
    'CRC-16-IBM': 0x18005,     # x^16 + x^15 + x^2 + 1
    'CRC-16-CCITT': 0x11021,   # x^16 + x^12 + x^5 + 1
    'CRC-32': 0x104C11DB7,     # Ethernet polynomial
}

# Cache para tablas de lookup CRC
_crc_tables = {}

def generar_tabla_crc(poly: int, bits: int = 8) -> list:
    """Genera tabla de lookup para cálculos CRC rápidos."""
    degree = poly.bit_length() - 1
    tabla = []
    for i in range(256):
        valor = i << (degree - 8) if degree >= 8 else i >> (8 - degree)
        for _ in range(8):
            if valor & (1 << (degree - 1)):
                valor = (valor << 1) ^ poly
            else:
                valor <<= 1
        tabla.append(valor & ((1 << degree) - 1))
    return tabla

def calcular_crc(datos_bits: int, poly: int = POLINOMIO_CRC, data_bits: int = 8, usar_tabla: bool = True) -> int:
    """Calcula el CRC para una palabra de `data_bits` bits usando `poly`.

    Nota: asumimos que `poly` está dado como entero con el bit más significativo (grado) incluido.
    Para CRC-8, `poly` tiene 9 bits (grado 8), p.ej. 0b100000111.
    
    Args:
        datos_bits: Datos a procesar
        poly: Polinomio generador
        data_bits: Número de bits de datos (típicamente 8)
        usar_tabla: Si True, usa lookup table (más rápido)
    """
    degree = poly.bit_length() - 1
    
    # Método optimizado con tabla de lookup (solo para bytes completos)
    if usar_tabla and data_bits == 8 and degree == 8:
        if poly not in _crc_tables:
            _crc_tables[poly] = generar_tabla_crc(poly)
        tabla = _crc_tables[poly]
        return tabla[datos_bits & 0xFF]
    
    # Método tradicional bit a bit
    dividendo = datos_bits << degree  # anadimos degree ceros
    shift = data_bits - 1
    divisor = poly << shift
    for i in range(data_bits):
        if (dividendo >> (data_bits + degree - 1 - i)) & 1:
            dividendo ^= (divisor >> i)
    return dividendo & ((1 << degree) - 1)

def verificar_crc(datos_con_crc: int, poly: int = POLINOMIO_CRC, data_bits: int = 8) -> bool:
    """Verifica si un paquete (data_bits + degree) tiene error usando `poly`."""
    degree = poly.bit_length() - 1
    dividendo = datos_con_crc
    shift = data_bits - 1
    divisor = poly << shift
    for i in range(data_bits):
        if (dividendo >> (data_bits + degree - 1 - i)) & 1:
            dividendo ^= (divisor >> i)
    return (dividendo & ((1 << degree) - 1)) == 0

# --- IMPLEMENTACIÓN DE FEC (CÓDIGO DE HAMMING 12,8) ---

def codificar_hamming(datos_bits: int) -> int:
    """Codifica 8 bits de datos en una palabra de Hamming de 12 bits."""
    d = [(datos_bits >> i) & 1 for i in range(7, -1, -1)]  # d[0] es MSB
    p1 = d[0] ^ d[1] ^ d[3] ^ d[4] ^ d[6]
    p2 = d[0] ^ d[2] ^ d[3] ^ d[5] ^ d[6]
    p4 = d[1] ^ d[2] ^ d[3] ^ d[7]
    p8 = d[4] ^ d[5] ^ d[6] ^ d[7]
    codigo = (
        (p1 << 11) | (p2 << 10) | (d[0] << 9) | (p4 << 8)
        | (d[1] << 7) | (d[2] << 6) | (d[3] << 5) | (p8 << 4)
        | (d[4] << 3) | (d[5] << 2) | (d[6] << 1) | d[7]
    )
    return codigo

def decodificar_corregir_hamming(codigo_recibido: int) -> int:
    """Decodifica y corrige un error de un solo bit en una palabra de Hamming de 12 bits."""
    bits = [(codigo_recibido >> i) & 1 for i in range(11, -1, -1)]
    p = bits  # p[0] es p1, p[1] es p2, etc.
    c1 = p[0] ^ p[2] ^ p[4] ^ p[6] ^ p[8] ^ p[10]
    c2 = p[1] ^ p[2] ^ p[5] ^ p[6] ^ p[9] ^ p[10]
    c4 = p[3] ^ p[4] ^ p[5] ^ p[6] ^ p[11]
    c8 = p[7] ^ p[8] ^ p[9] ^ p[10] ^ p[11]
    posicion_error = (c8 << 3) | (c4 << 2) | (c2 << 1) | c1

    if posicion_error == 0:
        # Síndrome 0 -> o no hay error o hay error no detectable por paridad (raro)
        return codigo_recibido, 'ok'

    # Validar que la posición de error esté dentro del rango
    if posicion_error > 12:
        # Múltiples errores: no corregible
        return codigo_recibido, 'no_corregible'

    # Corregir bit indicado
    corregido = codigo_recibido ^ (1 << (12 - posicion_error))

    # Verificar si tras la corrección la palabra queda consistente
    # Recalcular paridad sobre la palabra corregida
    bits_corr = [(corregido >> i) & 1 for i in range(11, -1, -1)]
    p2 = bits_corr
    c1c = p2[0] ^ p2[2] ^ p2[4] ^ p2[6] ^ p2[8] ^ p2[10]
    c2c = p2[1] ^ p2[2] ^ p2[5] ^ p2[6] ^ p2[9] ^ p2[10]
    c4c = p2[3] ^ p2[4] ^ p2[5] ^ p2[6] ^ p2[11]
    c8c = p2[7] ^ p2[8] ^ p2[9] ^ p2[10] ^ p2[11]
    sindrome_corregido = (c8c << 3) | (c4c << 2) | (c2c << 1) | c1c
    if sindrome_corregido == 0:
        return corregido, 'corregido'

    # Si después de la corrección el síndrome no es 0, entonces hay múltiples errores: no corregible
    return codigo_recibido, 'no_corregible'

# --- UTILIDADES DE SIMULACIÓN Y PROGRESO ---

# Tipos de errores para simulación más realista
TIPO_ERROR_UN_BIT = 'un_bit'
TIPO_ERROR_DOS_BITS = 'dos_bits'
TIPO_ERROR_RAFAGA = 'rafaga'  # burst error

def simular_error_un_bit(valor: int, ancho_bits: int) -> int:
    """Invierte un bit aleatorio dentro de un valor de 'ancho_bits' bits."""
    pos = random.randint(0, ancho_bits - 1)
    return valor ^ (1 << pos)

def simular_error_multiples_bits(valor: int, ancho_bits: int, num_errores: int = 2) -> int:
    """Invierte múltiples bits aleatorios."""
    resultado = valor
    posiciones = random.sample(range(ancho_bits), min(num_errores, ancho_bits))
    for pos in posiciones:
        resultado ^= (1 << pos)
    return resultado

def simular_error_rafaga(valor: int, ancho_bits: int, longitud_rafaga: int = 3) -> int:
    """Simula un error en ráfaga (burst): bits consecutivos alterados."""
    inicio = random.randint(0, max(0, ancho_bits - longitud_rafaga))
    resultado = valor
    for i in range(longitud_rafaga):
        if inicio + i < ancho_bits:
            resultado ^= (1 << (inicio + i))
    return resultado

def simular_error(valor: int, ancho_bits: int, tipo_error: str = TIPO_ERROR_UN_BIT) -> int:
    """Simula un error según el tipo especificado."""
    if tipo_error == TIPO_ERROR_DOS_BITS:
        return simular_error_multiples_bits(valor, ancho_bits, 2)
    elif tipo_error == TIPO_ERROR_RAFAGA:
        return simular_error_rafaga(valor, ancho_bits, 3)
    else:  # TIPO_ERROR_UN_BIT
        return simular_error_un_bit(valor, ancho_bits)

def barra_progreso(nombre: str, hecho: int, total: int, ancho: int = 30, extra: str = "") -> str:
    if total <= 0:
        total = 1
    porcentaje = hecho / total
    llenos = int(porcentaje * ancho)
    vacios = ancho - llenos
    return f"{nombre:8} |[" + "#" * llenos + "." * vacios + f"] {porcentaje*100:6.2f}% ({hecho}/{total}) {extra}"

@dataclass
class Resultado:
    total: int
    procesados: int
    tiempo_ms: float
    metrica: str
    detectados: int = 0
    corregidos: int = 0
    no_detectados: int = 0
    no_corregibles: int = 0
    falsos_positivos: int = 0
    overhead_bits: int = 0
    
    @property
    def tasa_deteccion(self) -> float:
        """Porcentaje de errores detectados."""
        if self.total == 0:
            return 0.0
        return (self.detectados / self.total) * 100
    
    @property
    def tasa_correccion(self) -> float:
        """Porcentaje de errores corregidos."""
        if self.total == 0:
            return 0.0
        return (self.corregidos / self.total) * 100
    
    @property
    def eficiencia(self) -> float:
        """Eficiencia: bits útiles / bits totales."""
        if self.overhead_bits == 0:
            return 100.0
        bits_datos = self.total * 8
        bits_totales = bits_datos + self.overhead_bits
        return (bits_datos / bits_totales) * 100
    
    @property
    def throughput(self) -> float:
        """Throughput en MB/s."""
        if self.tiempo_ms == 0:
            return 0.0
        return (self.total / (self.tiempo_ms / 1000)) / (1024 * 1024)


def procesar_crc(bytes_data: bytes, estado: dict, lock: threading.Lock, sleep_ms: float = 0.0, poly: int = POLINOMIO_CRC, tipo_error: str = TIPO_ERROR_UN_BIT) -> Resultado:
    """Procesa datos con CRC y simula errores para evaluar detección."""
    inicio = time.perf_counter()
    total = len(bytes_data)
    detectados = 0
    no_detectados = 0
    falsos_positivos = 0
    procesados = 0
    degree = poly.bit_length() - 1
    
    for b in bytes_data:
        # Codificar
        crc = calcular_crc(b, poly=poly)
        paquete = (b << degree) | crc  # bits de datos + CRC
        
        # Simular error
        recibido = simular_error(paquete, 8 + degree, tipo_error)
        
        # Verificar
        tiene_error = (recibido != paquete)  # error real introducido
        crc_detecta = not verificar_crc(recibido, poly=poly)
        
        if tiene_error:
            if crc_detecta:
                detectados += 1
            else:
                no_detectados += 1
        else:
            if crc_detecta:
                falsos_positivos += 1
        
        procesados += 1
        with lock:
            estado['crc']['procesados'] = procesados
            estado['crc']['detectados'] = detectados
            estado['crc']['no_detectados'] = no_detectados
        
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)
    
    fin = time.perf_counter()
    overhead = total * degree  # bits de overhead (CRC)
    
    return Resultado(
        total=total,
        procesados=procesados,
        tiempo_ms=(fin - inicio) * 1000.0,
        metrica=f"detectados: {detectados}, no detectados: {no_detectados}",
        detectados=detectados,
        no_detectados=no_detectados,
        falsos_positivos=falsos_positivos,
        overhead_bits=overhead
    )

def procesar_hamming(bytes_data: bytes, estado: dict, lock: threading.Lock, sleep_ms: float = 0.0, tipo_error: str = TIPO_ERROR_UN_BIT) -> Resultado:
    """Procesa datos con código de Hamming y simula errores para evaluar corrección."""
    inicio = time.perf_counter()
    total = len(bytes_data)
    corregidos = 0
    no_corregibles = 0
    correctos = 0
    procesados = 0
    
    for b in bytes_data:
        # Codificar
        codigo = codificar_hamming(b)  # 12 bits
        
        # Simular error
        recibido = simular_error(codigo, 12, tipo_error)
        
        # Decodificar y corregir
        corregido, status = decodificar_corregir_hamming(recibido)
        
        if status == 'corregido':
            corregidos += 1
        elif status == 'no_corregible':
            no_corregibles += 1
        elif status == 'ok':
            correctos += 1
            
        procesados += 1
        with lock:
            estado['ham']['procesados'] = procesados
            estado['ham']['corregidos'] = corregidos
            estado['ham']['no_corregibles'] = no_corregibles
            estado['ham']['correctos'] = correctos
        
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)
    
    fin = time.perf_counter()
    overhead = total * 4  # bits de overhead (4 bits de paridad por cada 8 de datos)
    
    return Resultado(
        total=total,
        procesados=procesados,
        tiempo_ms=(fin - inicio) * 1000.0,
        metrica=f"corregidos: {corregidos}, no_corregibles: {no_corregibles}",
        corregidos=corregidos,
        no_corregibles=no_corregibles,
        overhead_bits=overhead
    )


def render_barras(estado: dict, lock: threading.Lock, stop_event: threading.Event, inicio_crc: float, inicio_ham: float):
    # Preparar dos líneas para las barras y refrescar hasta que se indique stop
    # Intento de usar ANSI para mover el cursor; en PowerShell moderno suele estar habilitado.
    print()  # línea para CRC
    print()  # línea para HAM
    try:
        while not stop_event.is_set():
            with lock:
                crc = estado['crc']
                ham = estado['ham']
                ahora = time.perf_counter()
                extra_crc = f"t={((ahora - inicio_crc)*1000):.1f}ms, det={crc['detectados']}"
                extra_ham = f"t={((ahora - inicio_ham)*1000):.1f}ms, cor={ham['corregidos']}"
                linea_crc = barra_progreso("CRC-8", crc['procesados'], crc['total'], extra=extra_crc)
                linea_ham = barra_progreso("Hamming", ham['procesados'], ham['total'], extra=extra_ham)
            sys.stdout.write("\x1b[2A")  # subir 2 líneas
            sys.stdout.write("\r" + linea_crc.ljust(100) + "\n")
            sys.stdout.write(linea_ham.ljust(100) + "\n")
            sys.stdout.flush()
            time.sleep(0.05)
    finally:
        # Una última actualización final
        with lock:
            crc = estado['crc']
            ham = estado['ham']
            extra_crc = f"t={crc['tiempo_ms']:.1f}ms, det={crc['detectados']}"
            extra_ham = f"t={ham['tiempo_ms']:.1f}ms, cor={ham['corregidos']}"
            linea_crc = barra_progreso("CRC-8", crc['procesados'], crc['total'], extra=extra_crc)
            linea_ham = barra_progreso("Hamming", ham['procesados'], ham['total'], extra=extra_ham)
        sys.stdout.write("\x1b[2A")
        sys.stdout.write("\r" + linea_crc.ljust(100) + "\n")
        sys.stdout.write(linea_ham.ljust(100) + "\n")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Simulación CRC-8 vs Hamming (12,8) con barras de progreso")
    parser.add_argument("--text", type=str, help="Texto a simular (UTF-8)")
    parser.add_argument("--poly", type=str, default=None, help="Polinomio CRC (ej. 0x107 o 0b100000111). Si no se pasa, se usa 0b100000111")
    parser.add_argument("--byte", type=int, default=None, help="Valor de 8 bits para benchmark (0-255). Si se pasa, se ejecuta benchmark en modo por-byte con --iters")
    parser.add_argument("--iters", type=int, default=100000, help="Número de iteraciones para el benchmark por byte")
    parser.add_argument("--sleep-ms", type=float, default=0.0, help="Retardo artificial por byte para visualizar mejor")
    parser.add_argument("--error-type", type=str, default=TIPO_ERROR_UN_BIT, 
                       choices=[TIPO_ERROR_UN_BIT, TIPO_ERROR_DOS_BITS, TIPO_ERROR_RAFAGA],
                       help="Tipo de error a simular: un_bit, dos_bits, rafaga")
    args = parser.parse_args()

    # Parse polinomio si fue pasado
    if args.poly is None:
        poly = POLINOMIO_CRC
        poly_name = "CRC-8"
    else:
        s = args.poly.strip()
        try:
            # Verificar si es un nombre predefinido
            if s in POLINOMIOS_CRC:
                poly = POLINOMIOS_CRC[s]
                poly_name = s
            elif s.startswith("0x") or s.startswith("0X"):
                poly = int(s, 16)
                poly_name = f"Custom (0x{poly:X})"
            elif s.startswith("0b") or s.startswith("0B"):
                poly = int(s, 2)
                poly_name = f"Custom (0b{poly:b})"
            else:
                poly = int(s, 0)
                poly_name = f"Custom ({poly})"
        except Exception:
            print(f"Polinomio inválido: {s}. Usando polinomio por defecto.")
            poly = POLINOMIO_CRC
            poly_name = "CRC-8"
    
    print(f"Usando polinomio: {poly_name} = 0b{poly:b}")

    # Modo benchmark por byte: comparar procesamiento de una sola palabra de 8 bits
    if args.byte is not None:
        b = args.byte
        if b < 0 or b > 255:
            print("El parámetro --byte debe estar en 0..255")
            return
        iters = max(1, args.iters)
        print(f"Benchmark por byte: valor={b}, iteraciones={iters}, polinomio=0b{poly:b}")

        # Benchmark CRC: calcular CRC y verificar con un error simulado por iteración
        inicio_crc = time.perf_counter()
        for _ in range(iters):
            crc = calcular_crc(b, poly=poly)
            paquete = (b << (poly.bit_length() - 1)) | crc
            recibido = simular_error_un_bit(paquete, (8 + (poly.bit_length() - 1)))
            _ = verificar_crc(recibido, poly=poly)
        fin_crc = time.perf_counter()

        # Benchmark Hamming: codificar y decodificar/corregir por iteración
        inicio_ham = time.perf_counter()
        for _ in range(iters):
            codigo = codificar_hamming(b)
            recibido = simular_error_un_bit(codigo, 12)
            _ = decodificar_corregir_hamming(recibido)
        fin_ham = time.perf_counter()

        total_crc_ms = (fin_crc - inicio_crc) * 1000.0
        total_ham_ms = (fin_ham - inicio_ham) * 1000.0
        print(f"Resultado benchmark:\n - CRC:  tiempo total = {total_crc_ms:.3f} ms, tiempo/op = {total_crc_ms/iters*1000:.3f} µs")
        print(f" - Hamming: tiempo total = {total_ham_ms:.3f} ms, tiempo/op = {total_ham_ms/iters*1000:.3f} µs")
        if total_crc_ms < total_ham_ms:
            print("Más rápido: CRC")
        elif total_crc_ms > total_ham_ms:
            print("Más rápido: Hamming")
        else:
            print("Empate exacto")
        return

    if args.text is None or args.text.strip() == "":
        try:
            texto = input("Ingrese el texto a transmitir: ")
        except EOFError:
            texto = "Hola mundo"
    else:
        texto = args.text

    datos = texto.encode('utf-8')
    total = len(datos)
    if total == 0:
        print("No hay datos que procesar.")
        return

    # Estado compartido para las barras
    lock = threading.Lock()
    estado = {
        'crc': {'total': total, 'procesados': 0, 'detectados': 0, 'no_detectados': 0, 'tiempo_ms': 0.0},
        'ham': {'total': total, 'procesados': 0, 'corregidos': 0, 'no_corregibles': 0, 'correctos': 0, 'tiempo_ms': 0.0},
    }

    stop_event = threading.Event()

    # Arrancar renderizador
    inicio_crc = time.perf_counter()
    inicio_ham = inicio_crc
    render_thread = threading.Thread(target=render_barras, args=(estado, lock, stop_event, inicio_crc, inicio_ham), daemon=True)
    render_thread.start()

    # Trabajos en paralelo
    resultado_crc: Resultado | None = None
    resultado_ham: Resultado | None = None

    def tarea_crc():
        nonlocal resultado_crc, inicio_crc
        inicio_crc = time.perf_counter()
        resultado_crc = procesar_crc(datos, estado, lock, args.sleep_ms, poly=poly, tipo_error=args.error_type)
        with lock:
            estado['crc']['tiempo_ms'] = resultado_crc.tiempo_ms

    def tarea_ham():
        nonlocal resultado_ham, inicio_ham
        inicio_ham = time.perf_counter()
        resultado_ham = procesar_hamming(datos, estado, lock, args.sleep_ms, tipo_error=args.error_type)
        with lock:
            estado['ham']['tiempo_ms'] = resultado_ham.tiempo_ms

    th_crc = threading.Thread(target=tarea_crc, daemon=True)
    th_ham = threading.Thread(target=tarea_ham, daemon=True)

    th_crc.start()
    th_ham.start()

    th_crc.join()
    th_ham.join()

    stop_event.set()
    render_thread.join(timeout=0.2)

    # Resumen
    assert resultado_crc is not None and resultado_ham is not None
    print("\n" + "="*80)
    print("RESUMEN DETALLADO DE LA SIMULACIÓN")
    print("="*80)
    print(f"\nTipo de error simulado: {args.error_type}")
    print(f"Total de bytes procesados: {total}")
    
    print("\n--- CRC-8 ---")
    print(f"  Tiempo:           {resultado_crc.tiempo_ms:.3f} ms")
    print(f"  Throughput:       {resultado_crc.throughput:.3f} MB/s")
    print(f"  Errores detectados: {resultado_crc.detectados}/{total} ({resultado_crc.tasa_deteccion:.1f}%)")
    print(f"  No detectados:    {resultado_crc.no_detectados}/{total}")
    print(f"  Overhead:         {resultado_crc.overhead_bits} bits ({(resultado_crc.overhead_bits/(total*8))*100:.1f}%)")
    print(f"  Eficiencia:       {resultado_crc.eficiencia:.2f}%")
    
    print("\n--- Hamming (12,8) ---")
    print(f"  Tiempo:           {resultado_ham.tiempo_ms:.3f} ms")
    print(f"  Throughput:       {resultado_ham.throughput:.3f} MB/s")
    print(f"  Errores corregidos: {resultado_ham.corregidos}/{total} ({resultado_ham.tasa_correccion:.1f}%)")
    print(f"  No corregibles:   {resultado_ham.no_corregibles}/{total}")
    print(f"  Overhead:         {resultado_ham.overhead_bits} bits ({(resultado_ham.overhead_bits/(total*8))*100:.1f}%)")
    print(f"  Eficiencia:       {resultado_ham.eficiencia:.2f}%")
    
    print("\n--- Comparación ---")
    if resultado_crc.tiempo_ms < resultado_ham.tiempo_ms:
        velocidad_ganador = "CRC-8"
        diferencia = ((resultado_ham.tiempo_ms / resultado_crc.tiempo_ms - 1) * 100)
    elif resultado_crc.tiempo_ms > resultado_ham.tiempo_ms:
        velocidad_ganador = "Hamming"
        diferencia = ((resultado_crc.tiempo_ms / resultado_ham.tiempo_ms - 1) * 100)
    else:
        velocidad_ganador = "Empate"
        diferencia = 0
    
    print(f"  Más rápido: {velocidad_ganador} ({diferencia:.1f}% más rápido)" if velocidad_ganador != "Empate" else "  Empate en velocidad")
    
    # Comparación de capacidades
    print(f"\n  Capacidad de detección CRC: {resultado_crc.tasa_deteccion:.1f}%")
    print(f"  Capacidad de corrección Hamming: {resultado_ham.tasa_correccion:.1f}%")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()