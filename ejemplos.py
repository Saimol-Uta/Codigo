"""
Ejemplos de uso de la simulación CRC vs Hamming mejorada
Ejecuta este script para ver diferentes casos de uso
"""
import subprocess
import sys
import os

# Ruta al ejecutable de Python
PYTHON = r"C:/Users/saimo/AppData/Local/Programs/Python/Python312/python.exe"
INDEX_PY = os.path.join(os.path.dirname(__file__), "index.py")

def separador(titulo):
    print("\n" + "="*80)
    print(f"  {titulo}")
    print("="*80 + "\n")

def ejecutar(comando, descripcion):
    print(f"► {descripcion}")
    print(f"  Comando: {' '.join(comando[2:])}\n")
    subprocess.run(comando)
    input("\n[Presione ENTER para continuar...]")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           EJEMPLOS DE USO - SIMULACIÓN CRC vs HAMMING                        ║
║                    (Versión Mejorada)                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Ejemplo 1
    separador("EJEMPLO 1: Simulación Básica con Error de 1 Bit")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Hola mundo desde CRC", "--error-type", "un_bit"],
        "Error de 1 bit - Ambos métodos funcionan perfectamente"
    )
    
    # Ejemplo 2
    separador("EJEMPLO 2: Errores en Ráfaga (Burst Errors)")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Prueba de errores en rafaga continua", "--error-type", "rafaga"],
        "Errores en ráfaga - CRC detecta mejor que Hamming corrige"
    )
    
    # Ejemplo 3
    separador("EJEMPLO 3: Errores de Dos Bits")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Simulacion con dos bits erroneos", "--error-type", "dos_bits"],
        "2 bits erróneos - Hamming solo puede detectar, no corregir"
    )
    
    # Ejemplo 4
    separador("EJEMPLO 4: Comparación con CRC-16")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Test CRC-16", "--poly", "CRC-16-CCITT", "--error-type", "un_bit"],
        "Usando CRC-16 CCITT (usado en XMODEM, Bluetooth)"
    )
    
    # Ejemplo 5
    separador("EJEMPLO 5: Comparación con CRC-32")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Test", "--poly", "CRC-32", "--error-type", "un_bit"],
        "Usando CRC-32 (usado en Ethernet, ZIP, PNG)"
    )
    
    # Ejemplo 6
    separador("EJEMPLO 6: Simulación con Visualización Lenta")
    ejecutar(
        [PYTHON, INDEX_PY, "--text", "Demo lenta", "--error-type", "un_bit", "--sleep-ms", "100"],
        "Simulación ralentizada para ver progreso (100ms por byte)"
    )
    
    # Ejemplo 7
    separador("EJEMPLO 7: Benchmark de Rendimiento")
    ejecutar(
        [PYTHON, INDEX_PY, "--byte", "65", "--iters", "50000", "--poly", "CRC-8"],
        "Benchmark con 50,000 iteraciones del byte 'A' (65)"
    )
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ✅ Ejemplos completados                                                     ║
║                                                                              ║
║  Para usar la GUI con gráficos:                                              ║
║    python gui.py                                                             ║
║                                                                              ║
║  Para instalar dependencias de visualización (opcional):                     ║
║    pip install matplotlib numpy                                              ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Interrumpido por el usuario]")
    except Exception as e:
        print(f"\n\n[Error: {e}]")
