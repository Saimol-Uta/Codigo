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

def calcular_crc(datos_bits: int, poly: int = POLINOMIO_CRC, data_bits: int = 8) -> int:
    """Calcula el CRC para una palabra de `data_bits` bits usando `poly`.

    Nota: asumimos que `poly` está dado como entero con el bit más significativo (grado) incluido.
    Para CRC-8, `poly` tiene 9 bits (grado 8), p.ej. 0b100000111.
    """
    degree = poly.bit_length() - 1
    dividendo = datos_bits << degree  # anadimos degree ceros
    # Alineamos el divisor con el bit más significativo del dividendo
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
    if posicion_error != 0:
        return codigo_recibido ^ (1 << (12 - posicion_error))
    return codigo_recibido

# --- UTILIDADES DE SIMULACIÓN Y PROGRESO ---

def simular_error_un_bit(valor: int, ancho_bits: int) -> int:
    """Invierte un bit aleatorio dentro de un valor de 'ancho_bits' bits."""
    pos = random.randint(0, ancho_bits - 1)
    return valor ^ (1 << pos)

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


def procesar_crc(bytes_data: bytes, estado: dict, lock: threading.Lock, sleep_ms: float = 0.0, poly: int = POLINOMIO_CRC) -> Resultado:
    inicio = time.perf_counter()
    total = len(bytes_data)
    detectados = 0
    procesados = 0
    for b in bytes_data:
        crc = calcular_crc(b, poly=poly)
        paquete = (b << 8) | crc  # 16 bits
        recibido = simular_error_un_bit(paquete, 16)  # error de 1 bit
        ok = verificar_crc(recibido)
        if not ok:
            detectados += 1
        procesados += 1
        with lock:
            estado['crc']['procesados'] = procesados
            estado['crc']['detectados'] = detectados
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)
    fin = time.perf_counter()
    return Resultado(total=total, procesados=procesados, tiempo_ms=(fin - inicio) * 1000.0, metrica=f"errores detectados: {detectados}")

def procesar_hamming(bytes_data: bytes, estado: dict, lock: threading.Lock, sleep_ms: float = 0.0) -> Resultado:
    inicio = time.perf_counter()
    total = len(bytes_data)
    corregidos = 0
    procesados = 0
    for b in bytes_data:
        codigo = codificar_hamming(b)  # 12 bits
        recibido = simular_error_un_bit(codigo, 12)
        corregido = decodificar_corregir_hamming(recibido)
        if corregido == codigo:
            corregidos += 1
        procesados += 1
        with lock:
            estado['ham']['procesados'] = procesados
            estado['ham']['corregidos'] = corregidos
        if sleep_ms:
            time.sleep(sleep_ms / 1000.0)
    fin = time.perf_counter()
    return Resultado(total=total, procesados=procesados, tiempo_ms=(fin - inicio) * 1000.0, metrica=f"errores corregidos: {corregidos}")


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
    args = parser.parse_args()

    # Parse polinomio si fue pasado
    if args.poly is None:
        poly = POLINOMIO_CRC
    else:
        s = args.poly.strip()
        try:
            if s.startswith("0x") or s.startswith("0X"):
                poly = int(s, 16)
            elif s.startswith("0b") or s.startswith("0B"):
                poly = int(s, 2)
            else:
                poly = int(s, 0)
        except Exception:
            print(f"Polinomio inválido: {s}. Usando polinomio por defecto.")
            poly = POLINOMIO_CRC

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
        'crc': {'total': total, 'procesados': 0, 'detectados': 0, 'tiempo_ms': 0.0},
        'ham': {'total': total, 'procesados': 0, 'corregidos': 0, 'tiempo_ms': 0.0},
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
        resultado_crc = procesar_crc(datos, estado, lock, args.sleep_ms, poly=poly)
        with lock:
            estado['crc']['tiempo_ms'] = resultado_crc.tiempo_ms

    def tarea_ham():
        nonlocal resultado_ham, inicio_ham
        inicio_ham = time.perf_counter()
        resultado_ham = procesar_hamming(datos, estado, lock, args.sleep_ms)
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
    print("\nResumen:")
    print(f"- CRC-8:  tiempo = {resultado_crc.tiempo_ms:.2f} ms, {resultado_crc.metrica}")
    print(f"- Hamming: tiempo = {resultado_ham.tiempo_ms:.2f} ms, {resultado_ham.metrica}")
    if resultado_crc.tiempo_ms < resultado_ham.tiempo_ms:
        print("Más rápido: CRC-8")
    elif resultado_crc.tiempo_ms > resultado_ham.tiempo_ms:
        print("Más rápido: Hamming")
    else:
        print("Empate exacto")


if __name__ == "__main__":
    main()