"""
Script de prueba rápida para validar las mejoras implementadas
"""
import sys
import os

# Asegurar que podemos importar index
sys.path.insert(0, os.path.dirname(__file__))

import index

def prueba_basica():
    """Prueba básica de funcionalidad."""
    print("="*80)
    print("PRUEBA 1: Verificación de tabla de lookup CRC")
    print("="*80)
    
    # Probar cálculo CRC con y sin tabla
    byte_prueba = 0x41  # 'A'
    crc_con_tabla = index.calcular_crc(byte_prueba, usar_tabla=True)
    crc_sin_tabla = index.calcular_crc(byte_prueba, usar_tabla=False)
    
    print(f"Byte de prueba: 0x{byte_prueba:02X}")
    print(f"CRC con tabla: 0x{crc_con_tabla:02X}")
    print(f"CRC sin tabla: 0x{crc_sin_tabla:02X}")
    print(f"✓ Coinciden: {crc_con_tabla == crc_sin_tabla}")
    
    print("\n" + "="*80)
    print("PRUEBA 2: Tipos de errores")
    print("="*80)
    
    valor = 0b11110000
    ancho = 8
    
    print(f"Valor original: 0b{valor:08b}")
    
    # Error de 1 bit
    error1 = index.simular_error(valor, ancho, index.TIPO_ERROR_UN_BIT)
    print(f"Error 1 bit:    0b{error1:08b} ({bin(valor ^ error1).count('1')} bits diferentes)")
    
    # Error de 2 bits
    error2 = index.simular_error(valor, ancho, index.TIPO_ERROR_DOS_BITS)
    print(f"Error 2 bits:   0b{error2:08b} ({bin(valor ^ error2).count('1')} bits diferentes)")
    
    # Error en ráfaga
    error_rafaga = index.simular_error(valor, ancho, index.TIPO_ERROR_RAFAGA)
    print(f"Error ráfaga:   0b{error_rafaga:08b} ({bin(valor ^ error_rafaga).count('1')} bits diferentes)")
    
    print("\n" + "="*80)
    print("PRUEBA 3: Polinomios CRC disponibles")
    print("="*80)
    
    for nombre, poly in index.POLINOMIOS_CRC.items():
        print(f"{nombre:15} : 0b{poly:b} (grado {poly.bit_length()-1})")
    
    print("\n" + "="*80)
    print("PRUEBA 4: Estadísticas de Resultado")
    print("="*80)
    
    # Crear resultado de ejemplo
    resultado = index.Resultado(
        total=100,
        procesados=100,
        tiempo_ms=10.5,
        metrica="prueba",
        detectados=95,
        corregidos=90,
        no_detectados=5,
        no_corregibles=10,
        overhead_bits=800
    )
    
    print(f"Total: {resultado.total}")
    print(f"Tasa de detección: {resultado.tasa_deteccion:.1f}%")
    print(f"Tasa de corrección: {resultado.tasa_correccion:.1f}%")
    print(f"Eficiencia: {resultado.eficiencia:.2f}%")
    print(f"Throughput: {resultado.throughput:.3f} MB/s")
    
    print("\n" + "="*80)
    print("PRUEBA 5: Codificación Hamming")
    print("="*80)
    
    byte_prueba = 0b10101010
    codigo = index.codificar_hamming(byte_prueba)
    print(f"Dato original (8 bits):  0b{byte_prueba:08b}")
    print(f"Código Hamming (12 bits): 0b{codigo:012b}")
    
    # Introducir error de 1 bit
    error = codigo ^ (1 << 5)  # Invertir bit 5
    print(f"Con error en bit 5:       0b{error:012b}")
    
    corregido, status = index.decodificar_corregir_hamming(error)
    print(f"Después de corrección:    0b{corregido:012b}")
    print(f"Estado: {status}")
    print(f"✓ Corrección exitosa: {corregido == codigo}")
    
    print("\n" + "="*80)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("="*80)

if __name__ == "__main__":
    prueba_basica()
