import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

# Reuse functions from index.py by importing it as a module
import index

# Intentar importar visualización (opcional)
try:
    from visualizacion import mostrar_graficos_comparativos
    TIENE_GRAFICOS = True
except ImportError:
    TIENE_GRAFICOS = False
    print("Módulo de visualización no disponible. Instale matplotlib y numpy para habilitar gráficos.")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulación CRC vs Hamming")
        self.geometry("700x420")

        self.create_widgets()

    def create_widgets(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        # Row: Texto
        ttk.Label(frm, text="Texto:").grid(column=0, row=0, sticky=tk.W)
        self.text_entry = ttk.Entry(frm, width=60)
        self.text_entry.grid(column=1, row=0, columnspan=3, sticky=tk.W)
        self.text_entry.insert(0, "Hola CRC y Hamming desde GUI")

        # Row: Polinomio (combobox)
        ttk.Label(frm, text="Polinomio CRC:").grid(column=0, row=1, sticky=tk.W)
        self.poly_combo = ttk.Combobox(frm, values=list(index.POLINOMIOS_CRC.keys()), width=18)
        self.poly_combo.grid(column=1, row=1, sticky=tk.W)
        self.poly_combo.set("CRC-8")
        
        # Row: Tipo de error
        ttk.Label(frm, text="Tipo de error:").grid(column=2, row=1, sticky=tk.W)
        self.error_combo = ttk.Combobox(frm, 
                                        values=[index.TIPO_ERROR_UN_BIT, index.TIPO_ERROR_DOS_BITS, index.TIPO_ERROR_RAFAGA],
                                        width=12)
        self.error_combo.grid(column=3, row=1, sticky=tk.W)
        self.error_combo.set(index.TIPO_ERROR_UN_BIT)

        # Sleep ms en una nueva fila
        ttk.Label(frm, text="Sleep ms (visual):").grid(column=0, row=2, sticky=tk.W)
        self.sleep_entry = ttk.Entry(frm, width=8)
        self.sleep_entry.grid(column=1, row=2, sticky=tk.W)
        self.sleep_entry.insert(0, "2")

        # Row: Byte / Iters for benchmark - actualizar row numbers
        ttk.Label(frm, text="Modo byte (opcional):").grid(column=0, row=3, sticky=tk.W)
        self.byte_entry = ttk.Entry(frm, width=8)
        self.byte_entry.grid(column=1, row=3, sticky=tk.W)
        self.byte_entry.insert(0, "")
        ttk.Label(frm, text="Iters:").grid(column=2, row=3, sticky=tk.W)
        self.iters_entry = ttk.Entry(frm, width=12)
        self.iters_entry.grid(column=3, row=3, sticky=tk.W)
        self.iters_entry.insert(0, "100000")

        # Progress bars - actualizar row numbers
        ttk.Label(frm, text="CRC-8:").grid(column=0, row=4, sticky=tk.W)
        self.pb_crc = ttk.Progressbar(frm, maximum=100, length=500)
        self.pb_crc.grid(column=1, row=4, columnspan=3, sticky=tk.W)

        ttk.Label(frm, text="Hamming:").grid(column=0, row=5, sticky=tk.W)
        self.pb_ham = ttk.Progressbar(frm, maximum=100, length=500)
        self.pb_ham.grid(column=1, row=5, columnspan=3, sticky=tk.W)

        # Info labels under progressbars
        self.lbl_crc_info = ttk.Label(frm, text="CRC: 0/0, t=0.0ms, detectados=0")
        self.lbl_crc_info.grid(column=1, row=6, columnspan=3, sticky=tk.W)
        self.lbl_ham_info = ttk.Label(frm, text="Hamming: 0/0, t=0.0ms, corregidos=0, no_corregibles=0")
        self.lbl_ham_info.grid(column=1, row=7, columnspan=3, sticky=tk.W)
        self.lbl_summary = ttk.Label(frm, text="Resumen: -")
        self.lbl_summary.grid(column=0, row=8, columnspan=4, sticky=tk.W)

        # Buttons
        self.run_btn = ttk.Button(frm, text="Ejecutar", command=self.on_run)
        self.run_btn.grid(column=1, row=9, sticky=tk.W)
        self.stop_btn = ttk.Button(frm, text="Detener", command=self.on_stop, state=tk.DISABLED)
        self.stop_btn.grid(column=2, row=9, sticky=tk.W)
        
        # Botón para mostrar gráficos (solo si está disponible)
        if TIENE_GRAFICOS:
            self.graph_btn = ttk.Button(frm, text="Ver Gráficos", command=self.on_show_graphs, state=tk.DISABLED)
            self.graph_btn.grid(column=3, row=9, sticky=tk.W)
        else:
            self.graph_btn = None

        # Log / resumen
        self.log = ScrolledText(frm, height=10)
        self.log.grid(column=0, row=10, columnspan=4, sticky=tk.EW)

        # Detailed metrics panel
        self.metrics_panel = ScrolledText(frm, height=6)
        self.metrics_panel.grid(column=0, row=11, columnspan=4, sticky=tk.EW)

        # Internal
        self._worker = None
        self._stop_event = threading.Event()
        self._resultado_crc = None
        self._resultado_ham = None

    def on_run(self):
        # Disable run, enable stop
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self._stop_event.clear()
        texto = self.text_entry.get()
        poly_s = self.poly_combo.get().strip()
        error_type = self.error_combo.get().strip()
        try:
            sleep_ms = float(self.sleep_entry.get() or 0)
        except Exception:
            sleep_ms = 0.0
        byte_s = self.byte_entry.get().strip()
        try:
            iters = int(self.iters_entry.get() or 100000)
        except Exception:
            iters = 100000

        # Resolve poly from combobox string
        try:
            if poly_s in index.POLINOMIOS_CRC:
                poly = index.POLINOMIOS_CRC[poly_s]
            elif poly_s.startswith("0x"):
                poly = int(poly_s, 16)
            elif poly_s.startswith("0b"):
                poly = int(poly_s, 2)
            elif poly_s == "":
                poly = index.POLINOMIO_CRC
            else:
                poly = int(poly_s, 0)
        except Exception:
            messagebox.showerror("Error", "Polinomio inválido")
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            return

        # Start worker thread
        self._worker = threading.Thread(target=self.worker_task, args=(texto, poly, sleep_ms, byte_s, iters, error_type), daemon=True)
        self._worker.start()
        self.after(100, self.ui_update)

    def on_stop(self):
        self._stop_event.set()
        self.stop_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.NORMAL)
    
    def on_show_graphs(self):
        """Muestra la ventana con gráficos comparativos."""
        if self._resultado_crc and self._resultado_ham and TIENE_GRAFICOS:
            mostrar_graficos_comparativos(self, self._resultado_crc, self._resultado_ham)
        else:
            messagebox.showinfo("Info", "Primero ejecute una simulación completa.")

    def ui_update(self):
        # Periodically update progress bars from index.estado if available
        try:
            estado = index.estado  # atributo global en index.py
        except Exception:
            estado = None
        if estado:
            try:
                crc = estado['crc']
                ham = estado['ham']
                total_crc = crc.get('total', 1)
                proc_crc = crc.get('procesados', 0)
                total_ham = ham.get('total', 1)
                proc_ham = ham.get('procesados', 0)
                self.pb_crc['value'] = (proc_crc / max(1, total_crc)) * 100
                self.pb_ham['value'] = (proc_ham / max(1, total_ham)) * 100
                # Update info labels
                t_crc = crc.get('tiempo_ms', 0.0)
                t_ham = ham.get('tiempo_ms', 0.0)
                det = crc.get('detectados', 0)
                cor = ham.get('corregidos', 0)
                no_corr = ham.get('no_corregibles', 0)
                self.lbl_crc_info.config(text=f"CRC: {proc_crc}/{total_crc}, t={t_crc:.3f} ms, detectados={det}")
                self.lbl_ham_info.config(text=f"Hamming: {proc_ham}/{total_ham}, t={t_ham:.3f} ms, corregidos={cor}, no_corregibles={no_corr}")
                # If both finished, show summary
                if proc_crc >= total_crc and proc_ham >= total_ham:
                    if t_crc < t_ham:
                        winner = "CRC"
                    elif t_ham < t_crc:
                        winner = "Hamming"
                    else:
                        winner = "Empate"
                    self.lbl_summary.config(text=f"Resumen: Más rápido = {winner}")
                    # Update metrics panel with detailed final metrics
                    self.metrics_panel.delete('1.0', tk.END)
                    self.metrics_panel.insert(tk.END, f"CRC final:\n  procesados={proc_crc}/{total_crc}\n  tiempo={t_crc:.3f} ms\n  detectados={det}\n\n")
                    self.metrics_panel.insert(tk.END, f"Hamming final:\n  procesados={proc_ham}/{total_ham}\n  tiempo={t_ham:.3f} ms\n  corregidos={cor}\n  no_corregibles={no_corr}\n\n")
                    self.metrics_panel.insert(tk.END, f"Ganador: {winner}\n")
            except Exception:
                pass
        if self._worker and self._worker.is_alive() and not self._stop_event.is_set():
            self.after(100, self.ui_update)
        else:
            self.run_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            # Habilitar botón de gráficos si hay resultados
            if self.graph_btn and self._resultado_crc and self._resultado_ham:
                self.graph_btn.config(state=tk.NORMAL)
            # final update in case state exists
            try:
                estado = index.estado
                crc = estado['crc']
                ham = estado['ham']
                self.lbl_crc_info.config(text=f"CRC: {crc.get('procesados',0)}/{crc.get('total',0)}, t={crc.get('tiempo_ms',0.0):.3f} ms, detectados={crc.get('detectados',0)}")
                self.lbl_ham_info.config(text=f"Hamming: {ham.get('procesados',0)}/{ham.get('total',0)}, t={ham.get('tiempo_ms',0.0):.3f} ms, corregidos={ham.get('corregidos',0)}, no_corregibles={ham.get('no_corregibles',0)}")
                t_crc = crc.get('tiempo_ms', 0.0)
                t_ham = ham.get('tiempo_ms', 0.0)
                if t_crc and t_ham:
                    if t_crc < t_ham:
                        winner = "CRC"
                    elif t_ham < t_crc:
                        winner = "Hamming"
                    else:
                        winner = "Empate"
                    self.lbl_summary.config(text=f"Resumen: Más rápido = {winner}")
            except Exception:
                pass

    def worker_task(self, texto, poly, sleep_ms, byte_s, iters, error_type):
        # If byte_s specified, run benchmark
        if byte_s != "":
            try:
                b = int(byte_s)
                if b < 0 or b > 255:
                    raise ValueError()
            except Exception:
                self.log.insert(tk.END, "Byte inválido\n")
                return
            self.log.insert(tk.END, f"Benchmark por byte: valor={b}, iter={iters}\n")
            inicio_crc = time.perf_counter()
            for i in range(iters):
                if self._stop_event.is_set():
                    break
                crc = index.calcular_crc(b, poly=poly)
                paquete = (b << (poly.bit_length() - 1)) | crc
                recibido = index.simular_error(paquete, (8 + (poly.bit_length() - 1)), error_type)
                _ = index.verificar_crc(recibido, poly=poly)
                if i % (iters // 10 or 1) == 0:
                    self.log.insert(tk.END, f"CRC iter {i}\n")
            fin_crc = time.perf_counter()
            inicio_ham = time.perf_counter()
            for i in range(iters):
                if self._stop_event.is_set():
                    break
                codigo = index.codificar_hamming(b)
                recibido = index.simular_error(codigo, 12, error_type)
                _ = index.decodificar_corregir_hamming(recibido)
                if i % (iters // 10 or 1) == 0:
                    self.log.insert(tk.END, f"HAM iter {i}\n")
            fin_ham = time.perf_counter()
            total_crc_ms = (fin_crc - inicio_crc) * 1000.0
            total_ham_ms = (fin_ham - inicio_ham) * 1000.0
            self.log.insert(tk.END, f"CRC total {total_crc_ms:.3f} ms\n")
            self.log.insert(tk.END, f"HAM total {total_ham_ms:.3f} ms\n")
            return

        # Otherwise run the text-mode simulation using index.main logic
        # Set index.estado so GUI can read progress
        index.estado = {
            'crc': {'total': len(texto.encode('utf-8')), 'procesados': 0, 'detectados': 0, 'no_detectados': 0, 'tiempo_ms': 0.0},
            'ham': {'total': len(texto.encode('utf-8')), 'procesados': 0, 'corregidos': 0, 'no_corregibles': 0, 'correctos': 0, 'tiempo_ms': 0.0},
        }
        lock = threading.Lock()
        stop_event = self._stop_event

        def tarea_crc():
            res = index.procesar_crc(texto.encode('utf-8'), index.estado, lock, sleep_ms, poly=poly, tipo_error=error_type)
            index.estado['crc']['tiempo_ms'] = res.tiempo_ms
            self._resultado_crc = res

        def tarea_ham():
            res = index.procesar_hamming(texto.encode('utf-8'), index.estado, lock, sleep_ms, tipo_error=error_type)
            index.estado['ham']['tiempo_ms'] = res.tiempo_ms
            self._resultado_ham = res

        th1 = threading.Thread(target=tarea_crc, daemon=True)
        th2 = threading.Thread(target=tarea_ham, daemon=True)
        th1.start()
        th2.start()
        while th1.is_alive() or th2.is_alive():
            if stop_event.is_set():
                break
            time.sleep(0.1)
        self.log.insert(tk.END, "Finalizado\n")


if __name__ == '__main__':
    app = App()
    app.mainloop()
