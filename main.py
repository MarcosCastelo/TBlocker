import customtkinter as ctk
import json 
import os
import subprocess
import psutil

from utils import load_config, hash_password

CONFIG_PATH = "config.json"
BLOCKER_SCRIPT = "blocker.py"

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class BlockerConfigurator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TBlocker - Configurador")
        self.geometry("600x550")

        self.label_title = ctk.CTkLabel(self, text="TBlocker", font=("Segoe UI", 24, "bold"))
        self.label_title.pack(pady=(20, 10))

        self.blocked_sites_entry = ctk.CTkEntry(self, placeholder_text="Sites bloqueados (separados por vírgula)")
        self.blocked_sites_entry.pack(pady=10, fill="x", padx=40)

        self.blocked_apps_entry = ctk.CTkEntry(self, placeholder_text="Apps bloqueados (ex: chrome.exe, valorant.exe)")
        self.blocked_apps_entry.pack(pady=10, fill="x", padx=40)

        self.start_time = ctk.CTkEntry(self, placeholder_text="Início do bloqueio (HH:MM)")
        self.start_time.pack(pady=10, fill="x", padx=40)

        self.end_time = ctk.CTkEntry(self, placeholder_text="Fim do bloqueio (HH:MM)")
        self.end_time.pack(pady=10, fill="x", padx=40)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Senha de desbloqueio (opcional)", show="*")
        self.password_entry.pack(pady=10, fill="x", padx=40)

        self.hardcore_var = ctk.BooleanVar()
        self.hardcore_checkbox = ctk.CTkCheckBox(self, text="Modo Hardcore", variable=self.hardcore_var)
        self.hardcore_checkbox.pack(pady=10)

        self.save_button = ctk.CTkButton(self, text="Salvar Configuração", command=self.save_config)
        self.save_button.pack(pady=10)

        self.start_button = ctk.CTkButton(self, text="Iniciar Bloqueador", command=self.start_blocker)
        self.start_button.pack(pady=10)
        
        self.stop_button = ctk.CTkButton(self, text="Parar Bloqueador", command=self.prompt_password_and_stop)
        self.stop_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=5)

        self.load_existing_config()

    def load_existing_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                self.blocked_sites_entry.insert(0, ", ".join(data.get("blocked_sites", [])))
                self.blocked_apps_entry.insert(0, ", ".join(data.get("blocked_apps", [])))
                if "schedule" in data:
                    self.start_time.insert(0, data["schedule"].get("start", ""))
                    self.end_time.insert(0, data["schedule"].get("end", ""))
                self.password_entry.insert(0, "")
                self.hardcore_var.set(data.get("hardcore", False))
            except Exception as e:
                self.status_label.configure(text=f"Erro ao carregar config: {e}", text_color="red")

    def save_config(self):
        try:
            config = {
                "blocked_sites": [s.strip() for s in self.blocked_sites_entry.get().split(",") if s.strip()],
                "blocked_apps": [a.strip() for a in self.blocked_apps_entry.get().split(",") if a.strip()],
                "schedule": {
                    "start": self.start_time.get().strip(),
                    "end": self.end_time.get().strip()
                },
                "unlock_password": hash_password(self.password_entry.get().strip()),
                "hardcore": self.hardcore_var.get()
            }
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            self.status_label.configure(text="Configuração salva com sucesso!", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao salvar: {e}", text_color="red")

    def start_blocker(self):
        if not os.path.exists(BLOCKER_SCRIPT):
            self.status_label.configure(text="blocker.py não encontrado!", text_color="red")
            return
        try:
            process = subprocess.Popen(["python", BLOCKER_SCRIPT], creationflags=subprocess.CREATE_NEW_CONSOLE)
            with open("blocker.pid", "w") as f:
                f.write(str(process.pid))
            self.status_label.configure(text="Bloqueador iniciado!", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao iniciar: {e}", text_color="red")
            
    def stop_blocker(self):
        try:
            with open("blocker.pid", "r") as f:
                pid = int(f.read())
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=5)
                self.status_label.configure(text="Bloqueador parado com sucesso.", text_color="orange")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao parar a execução: {e}", text_color="red")
    
    def prompt_password_and_stop(self):
        config = load_config()
        stored_password = config.get("unlock_password", "")
        if not stored_password:
            self.stop_blocker()
            return
        
        def on_confirm():
            typed = password_entry.get()
            print(stored_password, hash_password(typed))
            if hash_password(typed) == stored_password:
                password_popup.destroy()
                self.stop_blocker()
            else:
                error_label.configure(text="Incorrect Password!", text_color="red")
                
        password_popup = ctk.CTkToplevel(self)
        password_popup.title("Enter the password for unlock")
        password_popup.geometry("400x150")
        password_popup.grab_set()
        
        password_label = ctk.CTkLabel(password_popup, text="Password:")
        password_label.pack(pady=(20,5))
        
        password_entry = ctk.CTkEntry(password_popup, show="*")
        password_entry.pack(fill="x", padx=40)
        
        error_label = ctk.CTkLabel(password_popup, text="")
        error_label.pack()
        
        confirm_button = ctk.CTkButton(password_popup, text="Confirm", command=on_confirm)
        confirm_button.pack()


if __name__ == "__main__":
    app = BlockerConfigurator()
    app.mainloop()
