"""
Módulo de visualización para comparación CRC vs Hamming
Proporciona gráficos y análisis visual de resultados
"""
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class VentanaGraficos(tk.Toplevel):
    """Ventana secundaria con gráficos comparativos."""
    
    def __init__(self, parent, resultado_crc, resultado_ham, titulo="Análisis Comparativo"):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("900x700")
        
        self.resultado_crc = resultado_crc
        self.resultado_ham = resultado_ham
        
        self.crear_graficos()
    
    def crear_graficos(self):
        """Crea los gráficos comparativos."""
        # Crear figura con múltiples subplots
        fig = Figure(figsize=(9, 7), dpi=100)
        
        # 1. Comparación de tiempos
        ax1 = fig.add_subplot(2, 2, 1)
        metodos = ['CRC', 'Hamming']
        tiempos = [self.resultado_crc.tiempo_ms, self.resultado_ham.tiempo_ms]
        colores = ['#3498db', '#e74c3c']
        bars = ax1.bar(metodos, tiempos, color=colores, alpha=0.7, edgecolor='black')
        ax1.set_ylabel('Tiempo (ms)', fontweight='bold')
        ax1.set_title('Comparación de Tiempos', fontweight='bold', pad=10)
        ax1.grid(axis='y', alpha=0.3)
        
        # Añadir valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f} ms',
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Comparación de Throughput
        ax2 = fig.add_subplot(2, 2, 2)
        throughputs = [self.resultado_crc.throughput, self.resultado_ham.throughput]
        bars = ax2.bar(metodos, throughputs, color=colores, alpha=0.7, edgecolor='black')
        ax2.set_ylabel('Throughput (MB/s)', fontweight='bold')
        ax2.set_title('Comparación de Throughput', fontweight='bold', pad=10)
        ax2.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f} MB/s',
                    ha='center', va='bottom', fontweight='bold')
        
        # 3. Tasas de detección/corrección
        ax3 = fig.add_subplot(2, 2, 3)
        tasas = [self.resultado_crc.tasa_deteccion, self.resultado_ham.tasa_correccion]
        bars = ax3.bar(['CRC\nDetección', 'Hamming\nCorrección'], tasas, 
                      color=colores, alpha=0.7, edgecolor='black')
        ax3.set_ylabel('Porcentaje (%)', fontweight='bold')
        ax3.set_title('Tasas de Detección/Corrección', fontweight='bold', pad=10)
        ax3.set_ylim([0, 105])
        ax3.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontweight='bold')
        
        # 4. Overhead y Eficiencia
        ax4 = fig.add_subplot(2, 2, 4)
        eficiencias = [self.resultado_crc.eficiencia, self.resultado_ham.eficiencia]
        overheads = [
            (self.resultado_crc.overhead_bits / (self.resultado_crc.total * 8)) * 100,
            (self.resultado_ham.overhead_bits / (self.resultado_ham.total * 8)) * 100
        ]
        
        x = np.arange(len(metodos))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, eficiencias, width, label='Eficiencia', 
                       color='#2ecc71', alpha=0.7, edgecolor='black')
        bars2 = ax4.bar(x + width/2, overheads, width, label='Overhead', 
                       color='#f39c12', alpha=0.7, edgecolor='black')
        
        ax4.set_ylabel('Porcentaje (%)', fontweight='bold')
        ax4.set_title('Eficiencia vs Overhead', fontweight='bold', pad=10)
        ax4.set_xticks(x)
        ax4.set_xticklabels(metodos)
        ax4.legend()
        ax4.grid(axis='y', alpha=0.3)
        
        # Añadir valores sobre las barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%',
                        ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        fig.tight_layout(pad=2.0)
        
        # Integrar en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Añadir panel de resumen textual
        self.crear_resumen()
    
    def crear_resumen(self):
        """Crea un panel de resumen con estadísticas clave."""
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.X)
        
        # Determinar ganadores
        ganador_velocidad = "CRC" if self.resultado_crc.tiempo_ms < self.resultado_ham.tiempo_ms else "Hamming"
        ganador_eficiencia = "CRC" if self.resultado_crc.eficiencia > self.resultado_ham.eficiencia else "Hamming"
        
        resumen_text = f"""
┌─────────────────────────────────────────────────────────────────────┐
│                       RESUMEN COMPARATIVO                           │
├─────────────────────────────────────────────────────────────────────┤
│ Más rápido:    {ganador_velocidad:10} ({abs(self.resultado_crc.tiempo_ms - self.resultado_ham.tiempo_ms):.2f} ms diferencia)
│ Más eficiente: {ganador_eficiencia:10} ({abs(self.resultado_crc.eficiencia - self.resultado_ham.eficiencia):.2f}% diferencia)
│                                                                     │
│ CRC:    Detectó {self.resultado_crc.detectados}/{self.resultado_crc.total} errores ({self.resultado_crc.tasa_deteccion:.1f}%)
│ Hamming: Corrigió {self.resultado_ham.corregidos}/{self.resultado_ham.total} errores ({self.resultado_ham.tasa_correccion:.1f}%)
└─────────────────────────────────────────────────────────────────────┘
        """
        
        label = tk.Label(frame, text=resumen_text, font=('Courier', 9), 
                        justify=tk.LEFT, bg='#f0f0f0', relief=tk.SUNKEN)
        label.pack(fill=tk.X)


def mostrar_graficos_comparativos(parent, resultado_crc, resultado_ham):
    """Función auxiliar para mostrar la ventana de gráficos."""
    ventana = VentanaGraficos(parent, resultado_crc, resultado_ham)
    ventana.transient(parent)
    ventana.grab_set()
