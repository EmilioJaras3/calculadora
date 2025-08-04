import tkinter as tk
from tkinter import ttk, messagebox, Menu, Toplevel, filedialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sympy as sp
from sympy.utilities.lambdify import lambdify
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from pathlib import Path
import random
import json

# Estilos de la interfaz con paleta de colores pastel
class Style:
    # Paleta de colores pastel
    BG = "#F7F9FB"       # Fondo principal (Gris claro suave)
    BG_LIGHT = "#E9EDF2" # Fondo para paneles/secundario (Gris un poco más oscuro)
    TEXT = "#4A4A4A"     # Texto principal (Gris oscuro)
    PRIMARY = "#AECBFF"   # Azul pastel para botones de acción principal
    SUCCESS = "#B7E8B9"  # Verde pastel para éxito/confirmación
    ERROR = "#FFADAD"    # Rojo pastel para errores/limpiar
    HIGHLIGHT = "#8BB5FF"# Azul vibrante pastel para resaltado

    # Fuentes
    FONT_FAMILY = "Helvetica"
    FONT_NORMAL = (FONT_FAMILY, 10)
    FONT_LARGE = (FONT_FAMILY, 12)
    FONT_TITLE = (FONT_FAMILY, 14, "bold")

    # Atributos de widgets
    ENTRY = {
        "font": FONT_LARGE,
        "bg": BG_LIGHT,
        "fg": TEXT,
        "relief": "flat",
        "highlightthickness": 1,
        "highlightbackground": PRIMARY,
        "highlightcolor": PRIMARY,
        "insertbackground": TEXT,
        "borderwidth": 0,
        "highlightthickness": 0
    }
    BUTTON_BASE = {
        "font": (FONT_FAMILY, 10, "bold"),
        "relief": "flat",
        "fg": TEXT,
        "bd": 0,
        "padx": 10,
        "pady": 5,
        "activebackground": HIGHLIGHT,
        "activeforeground": TEXT
    }
    FRAME = {
        "bg": BG,
        "relief": "flat"
    }
    # Estilos TTK
    @staticmethod
    def configure_ttk_style():
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TNotebook", background=Style.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=Style.BG_LIGHT, foreground=Style.TEXT, padding=[10, 5], font=Style.FONT_NORMAL, borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", Style.HIGHLIGHT)], foreground=[("selected", "white")])
        
        # Configurar el estilo del PanedWindow
        style.configure("TPanedwindow", background=Style.BG)


# Símbolos y funciones
x = sp.Symbol('x')
math_dict = {
    "pi": sp.pi, "π": sp.pi,
    "oo": sp.oo, "∞": sp.oo,
    "exp": sp.exp,
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "log": sp.log,
    "ln": sp.ln,
    'x': x
}

# Clase principal de la aplicación
class IntegralCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Configuración de la ventana
        self.title("Calculadora de Integrales Gráfica v6.1")
        self.configure(bg=Style.BG)
        self.geometry("1280x720")
        self.minsize(1000, 600)
        # Configuración de estilos
        Style.configure_ttk_style()
        # Variables de la aplicación
        self.history = []
        self.last_integral = None
        
        # Cargar historial al iniciar
        self.load_history_from_file()
        
        # Creación de la UI
        self._create_menu()
        self._create_layout()
        self._create_status_bar()
        self.update_status("Listo para calcular. Ingrese una función.")

    # Menú
    def _create_menu(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)
        
        file_menu = tk.Menu(menu_bar, tearoff=0, bg=Style.BG_LIGHT, fg=Style.TEXT, activebackground=Style.HIGHLIGHT, activeforeground=Style.TEXT)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar Historial a PDF", command=self.export_to_pdf)
        file_menu.add_command(label="Exportar Gráfica a PNG", command=self.export_plot_to_image)
        file_menu.add_separator()
        file_menu.add_command(label="Guardar Historial", command=self.save_history_to_file)
        file_menu.add_command(label="Ver Historial Guardado", command=self.show_saved_history)
        file_menu.add_command(label="Limpiar Historial", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.quit)
        
        help_menu = tk.Menu(menu_bar, tearoff=0, bg=Style.BG_LIGHT, fg=Style.TEXT, activebackground=Style.HIGHLIGHT, activeforeground=Style.TEXT)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about_info)

    # Barra de estado
    def _create_status_bar(self):
        self.status_bar = tk.Label(self, text="Listo", bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                   bg=Style.BG_LIGHT, fg=Style.TEXT, font=Style.FONT_NORMAL)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # Diseño de la interfaz
    def _create_layout(self):
        main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo: Entradas, resultados y teclado
        left_frame = tk.Frame(main_paned_window, **Style.FRAME, width=400)
        left_frame.pack_propagate(False)

        # Panel derecho: Gráfica
        right_frame = tk.Frame(main_paned_window, **Style.FRAME)
        
        main_paned_window.add(left_frame, weight=1)
        main_paned_window.add(right_frame, weight=2)
        
        self._create_input_panel(left_frame)
        self.results_frame = self._create_results_panel(left_frame)
        self.result_indef_label, self.result_def_label, self.result_deriv_label = self._create_results_labels(self.results_frame)
        self._create_numpad_panel(left_frame)
        self._create_plot_panel(right_frame)

    # Panel de entrada
    def _create_input_panel(self, parent):
        frame = tk.Frame(parent, **Style.FRAME, padx=10, pady=10)
        frame.pack(fill=tk.X, pady=(0, 10))
        
        label_style = {"bg": Style.BG, "fg": Style.TEXT, "font": Style.FONT_NORMAL}
        
        tk.Label(frame, text="Función f(x):", **label_style).pack(anchor="w")
        self.func_entry = tk.Entry(frame, **Style.ENTRY)
        self.func_entry.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame, text="Límite inferior (a):", **label_style).pack(anchor="w")
        self.lower_limit_entry = tk.Entry(frame, **Style.ENTRY)
        self.lower_limit_entry.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(frame, text="Límite superior (b):", **label_style).pack(anchor="w")
        self.upper_limit_entry = tk.Entry(frame, **Style.ENTRY)
        self.upper_limit_entry.pack(fill=tk.X, pady=(0, 10))
        
        action_buttons_frame = tk.Frame(frame, **Style.FRAME)
        action_buttons_frame.pack(fill=tk.X)
        
        calculate_style = Style.BUTTON_BASE.copy()
        calculate_style.update({"bg": Style.PRIMARY, "activebackground": Style.SUCCESS})
        tk.Button(action_buttons_frame, text="Calcular", command=self.calculate, **calculate_style).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        clear_style = Style.BUTTON_BASE.copy()
        clear_style.update({"bg": Style.ERROR, "activebackground": "#FF9D9D"})
        tk.Button(action_buttons_frame, text="Limpiar", command=self.clear_inputs, **clear_style).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _create_results_panel(self, parent):
        frame = tk.Frame(parent, **Style.FRAME)
        frame.pack(fill=tk.X, pady=(0, 20))
        return frame

    def _create_results_labels(self, parent):
        label_style = {"bg": Style.BG, "fg": Style.TEXT, "font": Style.FONT_NORMAL}
        result_style = {"bg": Style.BG, "fg": Style.SUCCESS, "font": Style.FONT_TITLE}
        
        tk.Label(parent, text="Integral Indefinida:", **label_style).pack(pady=(5,0))
        self.result_indef_label = tk.Label(parent, text="...", **result_style)
        self.result_indef_label.pack(pady=(0,10))
        
        tk.Label(parent, text="Integral Definida:", **label_style).pack()
        self.result_def_label = tk.Label(parent, text="...", **result_style)
        self.result_def_label.pack(pady=(0,10))

        tk.Label(parent, text="Derivada f'(x):", **label_style).pack()
        self.result_deriv_label = tk.Label(parent, text="...", **result_style)
        self.result_deriv_label.pack(pady=(0,10))
        
        return self.result_indef_label, self.result_def_label, self.result_deriv_label

    # Teclado numérico y de funciones
    def _create_numpad_panel(self, parent):
        frame = tk.Frame(parent, **Style.FRAME)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        buttons_layout = [
            ['Derivar', 'Simplificar', 'sin(', 'cos(', 'tan('],
            ['log(', 'ln(', 'sqrt(', 'x', 'π'],
            ['7', '8', '9', '/', '('],
            ['4', '5', '6', '*', ')'],
            ['1', '2', '3', '-', '^'],
            ['0', '.', 'exp(', '+', '=']
        ]
        
        for i, row in enumerate(buttons_layout):
            frame.rowconfigure(i, weight=1)
            for j, val in enumerate(row):
                frame.columnconfigure(j, weight=1)
                
                button_style = Style.BUTTON_BASE.copy()
                
                if val == '=':
                    cmd = self.calculate
                    button_style.update({"bg": Style.PRIMARY, "activebackground": Style.HIGHLIGHT})
                elif val in ['Derivar', 'Simplificar']:
                    cmd = self.calculate_derivative if val == 'Derivar' else self.simplify_function
                    button_style.update({"bg": Style.HIGHLIGHT, "activebackground": Style.PRIMARY, "fg": "white"})
                elif val == '^':
                    cmd = lambda: self.insert_text_in_focused_entry('**')
                    button_style.update({"bg": Style.BG_LIGHT, "activebackground": Style.HIGHLIGHT})
                else:
                    cmd = lambda v=val: self.insert_text_in_focused_entry(v)
                    button_style.update({"bg": Style.BG_LIGHT, "activebackground": Style.HIGHLIGHT})
                
                tk.Button(frame, text=val, command=cmd, **button_style).grid(row=i, column=j, padx=2, pady=2, sticky="nsew")

    # Panel de gráfica
    def _create_plot_panel(self, parent):
        frame = tk.Frame(parent, **Style.FRAME)
        frame.pack(fill=tk.BOTH, expand=True) 
        
        # Aumentamos el padding superior para empujar los botones hacia arriba
        plot_control_frame = tk.Frame(frame, **Style.FRAME)
        plot_control_frame.pack(fill=tk.X, pady=(10, 5)) 
        # Estilos de los botones de la gráfica
        export_button_style = Style.BUTTON_BASE.copy()
        export_button_style.update({"bg": Style.HIGHLIGHT, "fg": "white", "activeforeground": "white"})
        tk.Button(plot_control_frame, text="Exportar Gráfica", command=self.export_plot_to_image, **export_button_style).pack(side=tk.LEFT, padx=(0, 5))
        
        clear_button_style = Style.BUTTON_BASE.copy()
        clear_button_style.update({"bg": Style.ERROR, "fg": "white", "activeforeground": "white"})
        tk.Button(plot_control_frame, text="Limpiar Gráfica", command=self.clear_plot, **clear_button_style).pack(side=tk.LEFT)
        
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._style_plot()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)
        self.clear_plot()
        
    # Estilos de la gráfica
    def _style_plot(self):
        self.fig.patch.set_facecolor(Style.BG_LIGHT)
        self.ax.set_facecolor(Style.BG)
        self.ax.grid(True, linestyle="--", alpha=0.5, color=Style.TEXT)
        self.ax.axhline(0, color=Style.TEXT, linewidth=0.7)
        self.ax.axvline(0, color=Style.TEXT, linewidth=0.7)
        self.ax.tick_params(axis='x', colors=Style.TEXT)
        self.ax.tick_params(axis='y', colors=Style.TEXT)
        
        for spine in self.ax.spines.values():
            spine.set_edgecolor(Style.TEXT)
            
        self.ax.set_title("Gráfica de la Función", color=Style.TEXT, fontname=Style.FONT_FAMILY, fontsize=14)
        self.ax.set_xlabel("x", color=Style.TEXT)
        self.ax.set_ylabel("f(x)", color=Style.TEXT)

    # Validación de entradas
    def _get_and_validate_inputs(self, check_limits=True):
        try:
            func_str = self.func_entry.get().strip()
            if not func_str:
                raise ValueError("El campo de la función no puede estar vacío.")

            func = sp.sympify(func_str, locals=math_dict)
            a, b = None, None
            if check_limits:
                a_str = self.lower_limit_entry.get().strip()
                b_str = self.upper_limit_entry.get().strip()
                if not a_str or not b_str:
                    raise ValueError("Los campos de límites no pueden estar vacíos para calcular una integral definida.")
                a = sp.sympify(a_str, locals=math_dict)
                b = sp.sympify(b_str, locals=math_dict)

            return func, a, b, func_str
        except (ValueError, sp.SympifyError) as e:
            messagebox.showerror("Error de Entrada", f"Revisa los datos ingresados.\n\nDetalle: {e}")
            self.update_status(f"Error de entrada: {e}")
            return None, None, None, None
            
    # Función principal de cálculo
    def calculate(self):
        func, a, b, func_str = self._get_and_validate_inputs(check_limits=True)
        if func is None:
            return
        
        self.update_status("Calculando...")
        
        try:
            # Integrar
            result_indef = sp.integrate(func, x)
            result_def = sp.integrate(func, (x, a, b))
            result_def_eval = result_def.evalf()
            
            # Guardar resultado en la memoria del programa
            self.last_integral = {'func': func_str, 'a': str(a), 'b': str(b), 'result': str(result_def_eval), 'indef_result': str(result_indef)}
            self.history.append(self.last_integral)
            
            # Actualizar UI
            self._update_display(result_indef, result_def_eval, None)
            self.plot_function(func, a, b)
            
            self.update_status("Cálculo completado.")
            self.celebrate()
            
        except Exception as e:
            messagebox.showerror("Error de Cálculo", f"No se pudo procesar la integral.\n\nError: {e}")
            self.update_status(f"Error de cálculo: {e}")

    # Nueva función: Calcular derivada
    def calculate_derivative(self):
        func, _, _, func_str = self._get_and_validate_inputs(check_limits=False)
        if func is None:
            return

        try:
            derivative = sp.diff(func, x)
            self.result_deriv_label.config(text=f"$f'(x) = {sp.latex(derivative)}$")
            self.update_status("Derivada calculada.")
        except Exception as e:
            messagebox.showerror("Error de Derivación", f"No se pudo calcular la derivada.\n\nError: {e}")
            self.update_status(f"Error de derivación: {e}")
    
    # Nueva función: Simplificar
    def simplify_function(self):
        func_str = self.func_entry.get().strip()
        if not func_str:
            messagebox.showwarning("Advertencia", "No hay función para simplificar.")
            return

        try:
            func = sp.sympify(func_str, locals=math_dict)
            simplified_func = sp.simplify(func)
            self.func_entry.delete(0, tk.END)
            self.func_entry.insert(0, str(simplified_func))
            self.update_status("Función simplificada.")
        except (ValueError, sp.SympifyError) as e:
            messagebox.showerror("Error de Simplificación", f"No se pudo simplificar la función.\n\nDetalle: {e}")
            self.update_status(f"Error de simplificación: {e}")

    # Graficación de la función
    def plot_function(self, func, a, b):
        self.ax.clear()
        self._style_plot()
        
        try:
            f = lambdify(x, func, modules=["numpy"])
        except Exception:
            self.ax.set_title("Función no válida para graficar", color=Style.ERROR)
            self.canvas.draw()
            return
            
        try:
            # Rango de la gráfica
            a_f = float(a) if a not in [sp.oo, -sp.oo] else -10
            b_f = float(b) if b not in [sp.oo, -sp.oo] else 10
            
            if a in [sp.oo, -sp.oo] or b in [sp.oo, -sp.oo]:
                 self.update_status("Advertencia: La función se graficó en el rango [-10, 10] debido a los límites infinitos.")
            
            x_plot = np.linspace(a_f - 2, b_f + 2, 1000)
            x_fill = np.linspace(a_f, b_f, 500)
        except (TypeError, ValueError):
            a_f, b_f = -10, 10
            x_plot = np.linspace(a_f, b_f, 1000)
            x_fill = np.linspace(a_f, b_f, 500)
        
        try:
            # Graficar
            y_plot = f(x_plot)
            y_fill = f(x_fill)
        except (ValueError, ZeroDivisionError, TypeError):
            self.update_status("Advertencia: No se pudo evaluar la función en el rango. La gráfica podría ser incorrecta.")
            self.canvas.draw()
            return
            
        self.ax.plot(x_plot, y_plot, label=f"$f(x) = {sp.latex(func)}$", color=Style.PRIMARY)
        self.ax.fill_between(x_fill, y_fill, color=Style.SUCCESS, alpha=0.6, label="Área de la integral")
        
        legend = self.ax.legend(facecolor=Style.BG_LIGHT, edgecolor=Style.HIGHLIGHT, labelcolor=Style.TEXT)
        self.canvas.draw()
        
    def clear_plot(self):
        self.ax.clear()
        self._style_plot()
        self.canvas.draw()

    # Nueva función: Exportar Gráfica
    def export_plot_to_image(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("Archivos PNG", "*.png"), ("Archivos JPEG", "*.jpg")],
                initialfile="grafica_integral.png",
                title="Guardar Gráfica"
            )
            if filename:
                self.fig.savefig(filename, dpi=300, facecolor=self.fig.get_facecolor())
                messagebox.showinfo("Éxito", f"Gráfica guardada como '{Path(filename).name}'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la gráfica.\n\nDetalles: {e}")

    # Actualizar barra de estado
    def update_status(self, message):
        self.status_bar.config(text=message)

    # Actualizar etiquetas de resultados
    def _update_display(self, indef_result, def_result, deriv_result):
        try:
            indef_text = f"$\\int f(x)dx = {sp.latex(indef_result)} + C$"
            def_text = f"≈ {def_result:.6f}"
            self.result_indef_label.config(text=indef_text)
            self.result_def_label.config(text=def_text)
        except Exception:
            self.result_indef_label.config(text="No mostrada")
            self.result_def_label.config(text="No mostrada")
        
        if deriv_result is not None:
            try:
                self.result_deriv_label.config(text=f"$f'(x) = {sp.latex(deriv_result)}$")
            except Exception:
                self.result_deriv_label.config(text="No mostrada")
        else:
            self.result_deriv_label.config(text="...")

    def clear_inputs(self):
        self.func_entry.delete(0, tk.END)
        self.lower_limit_entry.delete(0, tk.END)
        self.upper_limit_entry.delete(0, tk.END)
        self.result_indef_label.config(text="...")
        self.result_def_label.config(text="...")
        self.result_deriv_label.config(text="...")
        self.clear_plot()
        self.update_status("Entradas limpiadas.")
        
    # Manejo de entrada de texto
    def get_focused_entry(self):
        focused_widget = self.focus_get()
        if focused_widget == self.func_entry:
            return self.func_entry
        elif focused_widget == self.lower_limit_entry:
            return self.lower_limit_entry
        elif focused_widget == self.upper_limit_entry:
            return self.upper_limit_entry
        return self.func_entry

    def insert_text_in_focused_entry(self, value):
        entry = self.get_focused_entry()
        entry.insert(tk.INSERT, value)

    # Gestión de historial en archivos
    def save_history_to_file(self):
        if not self.history:
            messagebox.showinfo("Info", "No hay historial para guardar.")
            return
        try:
            with open("history.txt", "w") as f:
                for item in self.history:
                    f.write(f"Función: {item['func']}\n")
                    f.write(f"Límites: {item['a']} a {item['b']}\n")
                    f.write(f"Integral Indefinida: {item['indef_result']}\n")
                    f.write(f"Resultado Definido: {item['result']}\n")
                    f.write("----------------------------------------\n")
            messagebox.showinfo("Éxito", "Historial guardado en 'history.txt'.")
            self.update_status("Historial guardado en 'history.txt'.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el historial.\n\nDetalles: {e}")
            self.update_status(f"Error al guardar historial: {e}")

    def load_history_from_file(self):
        try:
            with open("history.txt", "r") as f:
                content = f.read()
                self.history = []
                lines = content.split("----------------------------------------\n")
                for line in lines:
                    if line.strip():
                        parts = line.strip().split("\n")
                        if len(parts) >= 4:
                            func = parts[0].replace("Función: ", "")
                            limits = parts[1].replace("Límites: ", "").split(" a ")
                            a = limits[0]
                            b = limits[1]
                            indef_result = parts[2].replace("Integral Indefinida: ", "")
                            result = parts[3].replace("Resultado Definido: ", "")
                            self.history.append({'func': func, 'a': a, 'b': b, 'result': result, 'indef_result': indef_result})
        except FileNotFoundError:
            self.history = []
            
    def show_saved_history(self):
        try:
            with open("history.txt", "r") as f:
                content = f.read()
            if not content:
                content = "El historial guardado está vacío."
            
            # Crear una nueva ventana para mostrar el historial
            history_window = Toplevel(self)
            history_window.title("Historial de Cálculos")
            history_window.geometry("600x400")
            history_window.configure(bg=Style.BG)
            
            scrollbar = ttk.Scrollbar(history_window)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_widget = tk.Text(history_window, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                                  bg=Style.BG_LIGHT, fg=Style.TEXT, font=Style.FONT_NORMAL,
                                  relief=tk.FLAT, borderwidth=0)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED) # No editable
            
            scrollbar.config(command=text_widget.yview)

        except FileNotFoundError:
            messagebox.showinfo("Info", "No se encontró el archivo de historial 'history.txt'.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el historial.\n\nDetalles: {e}")
            
    def clear_history(self):
        self.history = []
        try:
            # Eliminar el archivo de historial si existe
            if Path("history.txt").exists():
                Path("history.txt").unlink()
            messagebox.showinfo("Éxito", "El historial ha sido limpiado.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al intentar limpiar el archivo de historial.\n\nDetalles: {e}")
        self.update_status("Historial limpiado.")

    # Exportar a PDF
    def export_to_pdf(self):
        if not self.history:
            messagebox.showinfo("Info", "Historial vacío.")
            return
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Archivos PDF", "*.pdf")],
                initialfile="reporte_integrales.pdf",
                title="Guardar Historial"
            )
            if not filename:
                return
            c = canvas.Canvas(filename, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(inch, 10.5 * inch, "Reporte de Integrales")
            c.setFont("Helvetica", 12)
            y = 10 * inch
            for item in self.history:
                text = f"∫({item['func']}) dx de {item['a']} a {item['b']} ≈ {float(item['result']):.4f}"
                if y < inch:
                    c.showPage()
                    y = 10 * inch
                    c.setFont("Helvetica", 12)
                c.drawString(inch, y, text)
                y -= 0.25 * inch
            c.save()
            messagebox.showinfo("Éxito", f"Reporte guardado como '{Path(filename).name}'")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear PDF.\n\nDetalles: {e}")

    # Ventana de información
    def show_about_info(self):
        messagebox.showinfo("Acerca de", "Calculadora de Integrales Gráfica\nVersión 6.1\n\nDesarrollada para la práctica de programación avanzada. Combina SymPy, Matplotlib y ReportLab.\n\nNovedades:\n- Paleta de colores pastel\n- Mejor organización de la interfaz\n- Funciones de Derivada y Simplificación\n- Exportar gráfica a PNG\n- Gestión de Historial a través de archivos")

    # Animación de celebración
    def celebrate(self):
        confetti_window = Toplevel(self)
        confetti_window.overrideredirect(True)
        confetti_window.attributes('-transparentcolor', Style.BG)
        confetti_window.attributes('-alpha', 0.8)
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        confetti_window.geometry(f"{main_width}x{main_height}+{main_x}+{main_y}")
        confetti_canvas = tk.Canvas(confetti_window, bg=Style.BG, highlightthickness=0)
        confetti_canvas.pack(fill="both", expand=True)
        particles = []
        colors = ['#FFADAD', '#FFD1DC', '#FFC994', '#FFF5BA', '#C7E6D0', '#B3D6FF', '#C4B7E0']
        for _ in range(100):
            x_pos = random.randint(0, main_width)
            y_pos = random.randint(-50, 0)
            size = random.randint(5, 10)
            color = random.choice(colors)
            particle = confetti_canvas.create_rectangle(x_pos, y_pos, x_pos + size, y_pos + size, fill=color, outline='')
            particles.append({'id': particle, 'x': x_pos, 'y': y_pos, 'vy': random.uniform(1, 3), 'vx': random.uniform(-1, 1)})
        def animate_confetti():
            for p in particles:
                p['y'] += p['vy']
                p['x'] += p['vx']
                confetti_canvas.coords(p['id'], p['x'], p['y'], p['x'] + 10, p['y'] + 10)
                if p['y'] > main_height:
                    confetti_canvas.delete(p['id'])
                    particles.remove(p)
            if particles:
                confetti_window.after(20, animate_confetti)
            else:
                confetti_window.destroy()
        animate_confetti()

if __name__ == "__main__":
    app = IntegralCalculatorApp()
    app.mainloop()