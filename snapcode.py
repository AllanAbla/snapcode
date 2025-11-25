import os
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from datetime import datetime
import json

APP_CONFIG_FILE = "app_config.json"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, APP_CONFIG_FILE)
OUTPUTS_BASE_DIR = os.path.join(BASE_DIR, "outputs")

def load_app_data():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"presets": {}, "version": 0}
    return {"presets": {}, "version": 0}

def save_app_data(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_next_version(app_data) -> tuple[str, int]:
    current_version_num = app_data.get("version", 0)
    next_version_num = current_version_num + 1
    
    app_data["version"] = next_version_num
    
    return f"v{next_version_num}", next_version_num

def generate_filetree(files: list[str]) -> str:
    tree = ""
    for file in sorted(files):
        tree += f" - {file}\n"
    return tree

def read_files(files: list[str]) -> list[tuple[str, str]]:
    file_contents = []
    for file in files:
        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            file_contents.append((file, content))
        except Exception as e:
            print(f"[ERROR] Não foi possível ler {file}: {e}")
    return file_contents

def write_output(version: str, code_base_name: str, files_data: list[tuple[str, str]], preset_name: str):
    if not files_data:
        print("[WARN] Nenhuma informação de arquivo para escrever.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    preset_output_dir = os.path.join(OUTPUTS_BASE_DIR, preset_name)
    os.makedirs(preset_output_dir, exist_ok=True)

    output_filename = f"{preset_name}_{timestamp}.txt"
    output_path = os.path.join(preset_output_dir, output_filename)

    header = f"### CODEBASE SNAPSHOT ({version})\n"
    header += f"### Código Base: {code_base_name}\n"
    header += f"### Preset: {preset_name}\n"
    header += f"### Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    header += "### FILE TREE\n"
    header += generate_filetree([f for f, _ in files_data])
    header += "\n" + ("=" * 80) + "\n\n"

    with open(output_path, "w", encoding="utf-8") as out:
        out.write(header)
        for filename, content in files_data:
            out.write(f"\n### BEGIN FILE: {filename}\n\n")
            out.write(content)
            out.write(f"\n\n### END FILE: {filename}\n")
            out.write("\n" + ("-" * 80) + "\n")

    print(f"[OK] Saída escrita em: {output_path}")
    messagebox.showinfo("Sucesso", f"Snapshot gerado com sucesso!\nArquivo: {output_path}")

class PresetManagerApp:
    def __init__(self, master):
        self.master = master
        master.title("Menu de Presets")
        self.app_data = load_app_data()
        self.presets = self.app_data.get("presets", {})
        self.master.protocol("WM_DELETE_WINDOW", self.close_app)

        self.create_widgets()

    def create_widgets(self):
        for widget in self.master.winfo_children():
            widget.destroy()

        tk.Label(self.master, text="Selecione ou Crie um Preset:", font=('Arial', 14, 'bold')).pack(pady=10)

        list_frame = tk.Frame(self.master)
        list_frame.pack(pady=5, padx=20, fill='x')

        self.listbox = tk.Listbox(list_frame, height=10)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        for name in sorted(self.presets.keys()):
            self.listbox.insert(tk.END, name)

        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Usar Preset Selecionado", command=self.load_selected_preset, bg='green', fg='white').pack(side="left", padx=5)
        tk.Button(button_frame, text="Criar Novo Preset", command=self.start_new_preset, bg='blue', fg='white').pack(side="left", padx=5)
        tk.Button(button_frame, text="Excluir Preset", command=self.delete_selected_preset, bg='red', fg='white').pack(side="left", padx=5)
        
        tk.Button(self.master, text="Sair", command=self.close_app).pack(pady=10)

    def load_selected_preset(self):
        selected_index = self.listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Atenção", "Selecione um preset na lista.")
            return

        preset_name = self.listbox.get(selected_index[0])
        preset_data = self.presets.get(preset_name)
        
        if not preset_data or not os.path.isdir(preset_data["root_dir"]):
            messagebox.showerror("Erro", "Diretório do preset não encontrado ou inválido. Exclua e crie novamente.")
            self.delete_selected_preset(silent=True)
            self.create_widgets()
            return
            
        self.master.withdraw()
        FileSelectorApp(tk.Toplevel(self.master), preset_name, preset_data, self.return_to_menu, self.app_data)

    def start_new_preset(self):
        new_name = simpledialog.askstring("Novo Preset", "Digite o nome do novo preset:")
        if not new_name:
            return

        if new_name in self.presets:
            messagebox.showwarning("Atenção", f"O preset '{new_name}' já existe.")
            return

        root_dir = filedialog.askdirectory(title=f"Selecione a Pasta Raiz para o Preset: {new_name}")
        
        if root_dir:
            initial_data = {
                "root_dir": root_dir,
                "excluded_files": []
            }
            self.presets[new_name] = initial_data
            self.app_data["presets"] = self.presets
            save_app_data(self.app_data)
            
            self.master.withdraw()
            FileSelectorApp(tk.Toplevel(self.master), new_name, initial_data, self.return_to_menu, self.app_data)

    def delete_selected_preset(self, silent=False):
        selected_index = self.listbox.curselection()
        if not selected_index:
            if not silent:
                messagebox.showwarning("Atenção", "Selecione um preset para excluir.")
            return

        preset_name = self.listbox.get(selected_index[0])

        if not silent and not messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o preset '{preset_name}'?"):
            return

        del self.presets[preset_name]
        self.app_data["presets"] = self.presets
        save_app_data(self.app_data)
        
        if not silent:
            messagebox.showinfo("Sucesso", f"Preset '{preset_name}' excluído.")
        
        self.create_widgets()

    def return_to_menu(self):
        self.app_data = load_app_data()
        self.presets = self.app_data.get("presets", {})
        self.master.deiconify()
        self.create_widgets()
        
    def close_app(self):
        self.master.quit()
        self.master.destroy()

class FileSelectorApp:
    def __init__(self, master, preset_name, preset_data, return_callback, app_data):
        self.master = master
        self.preset_name = preset_name
        self.root_dir = preset_data["root_dir"]
        self.initial_excluded_files = set(preset_data["excluded_files"])
        self.return_callback = return_callback
        self.app_data = app_data
        
        self.master.title(f"Codebase Snapshot Generator - Preset: {self.preset_name}")
        
        self.all_files = []
        self.checkbox_vars = {}
        self.code_base_name = os.path.basename(self.root_dir)
        
        self.master.protocol("WM_DELETE_WINDOW", self.cancel_and_return)
        
        self.scan_files()
        
        if self.all_files:
            os.chdir(self.root_dir)
            self.create_widgets()
        else:
            self.cancel_and_return()

    def list_files_relative(self, path: str) -> list[str]:
        all_files = []
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not (d.startswith('.') or d == '__pycache__')]

            for file in files:
                if file.startswith('.'):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, path)
                
                all_files.append(relative_path)
        return all_files

    def scan_files(self):
        all_paths = self.list_files_relative(self.root_dir)
        
        if not all_paths:
            messagebox.showwarning("Atenção", "Nenhum arquivo encontrado na pasta selecionada.")
            return

        self.all_files = sorted(all_paths)

    def create_widgets(self):
        tk.Label(self.master, text=f"Pasta: {self.code_base_name}", font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(self.master, text="Selecione os arquivos para incluir:").pack()

        scroll_frame = tk.Frame(self.master)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(scroll_frame)
        self.scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        grouped_by_dir: dict[str, list[str]] = {}
        for path in self.all_files:
            dir_path = os.path.dirname(path)
            grouped_by_dir.setdefault(dir_path, []).append(path)

        for dir_path in sorted(grouped_by_dir.keys(), key=lambda d: (d != "", d.lower())):
            display_name = dir_path if dir_path else "[raiz]"
            group_frame = tk.LabelFrame(self.scrollable_frame, text=display_name, padx=5, pady=5)
            group_frame.pack(fill="x", expand=True, padx=5, pady=5)

            row = 0
            col = 0
            for file_path in sorted(grouped_by_dir[dir_path]):
                is_checked = file_path not in self.initial_excluded_files
                var = tk.BooleanVar(value=is_checked)
                file_label = os.path.basename(file_path)

                cb = tk.Checkbutton(group_frame, text=file_label, variable=var, anchor="w", justify="left")
                cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)

                self.checkbox_vars[file_path] = var

                col += 1
                if col >= 3:
                    col = 0
                    row += 1
        
        quick_action_frame = tk.Frame(self.master)
        quick_action_frame.pack(pady=5)
        
        tk.Button(quick_action_frame, text="Selecionar Todos", command=self.select_all).pack(side="left", padx=5)
        tk.Button(quick_action_frame, text="Desmarcar Todos", command=self.deselect_all).pack(side="left", padx=5)
            
        tk.Button(self.master, text="GERAR SNAPSHOT E SALVAR PADRÃO", command=self.generate_snapshot, 
                  bg='green', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
                  
        tk.Button(self.master, text="Cancelar e Voltar ao Menu", command=self.cancel_and_return).pack(pady=5)

    def select_all(self):
        for var in self.checkbox_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.checkbox_vars.values():
            var.set(False)
            
    def cancel_and_return(self):
        self.master.destroy()
        self.return_callback()

    def generate_snapshot(self):
        selected_files = []
        excluded_files_to_save = []
        
        for file, var in self.checkbox_vars.items():
            if var.get():
                selected_files.append(file)
            else:
                excluded_files_to_save.append(file)
                
        if not selected_files:
            messagebox.showwarning("Atenção", "Nenhum arquivo selecionado para gerar o snapshot.")
            return

        self.save_current_preset(excluded_files_to_save)

        version_str, new_version_num = get_next_version(self.app_data)
        files_data = read_files(selected_files)
        
        write_output(version_str, self.code_base_name, files_data, self.preset_name)
        
        save_app_data(self.app_data)
        
        self.master.destroy()
        self.return_callback()

    def save_current_preset(self, excluded_files):
        if "presets" not in self.app_data:
            self.app_data["presets"] = {}

        if self.preset_name in self.app_data["presets"]:
            self.app_data["presets"][self.preset_name]["excluded_files"] = excluded_files
        else:
            self.app_data["presets"][self.preset_name] = {
                "root_dir": self.root_dir,
                "excluded_files": excluded_files
            }

def main_gui():
    root = tk.Tk()
    root.geometry("600x500")
    
    PresetManagerApp(root)
    
    root.mainloop()

if __name__ == "__main__":
    main_gui()