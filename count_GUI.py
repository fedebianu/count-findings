import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import asyncio
import threading
from count_core import CountCore

class CountGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Audit Statistics")
        self.root.geometry("800x600")
        
        self.analyzer = None
        
        # Configuration frame
        self.frame_config = ttk.LabelFrame(root, text="Configuration", padding="5")
        self.frame_config.pack(fill="x", padx=5, pady=5)
        
        # GitHub Token
        ttk.Label(self.frame_config, text="GitHub Token:").grid(row=0, column=0, padx=5, pady=5)
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(self.frame_config, textvariable=self.token_var, show="*", width=50)
        self.token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Security Researcher
        ttk.Label(self.frame_config, text="Security Researcher:").grid(row=1, column=0, padx=5, pady=5)
        self.sr_var = tk.StringVar()
        self.sr_entry = ttk.Entry(self.frame_config, textvariable=self.sr_var, width=50)
        self.sr_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Domains frame
        self.frame_domains = ttk.LabelFrame(root, text="Domains", padding="5")
        self.frame_domains.pack(fill="x", padx=5, pady=5)
        
        self.domains_text = scrolledtext.ScrolledText(self.frame_domains, height=5)
        self.domains_text.pack(fill="x", padx=5, pady=5)
        
        # Default domains
        default_domains = "code4rena-2023\nspearbit\nsherlock-audit\nyAudit"
        self.domains_text.insert("1.0", default_domains)
        
        # Buttons frame
        self.frame_buttons = ttk.Frame(root)
        self.frame_buttons.pack(fill="x", padx=5, pady=5)
        
        self.save_config_btn = ttk.Button(self.frame_buttons, text="Save Configuration", command=self.save_config)
        self.save_config_btn.pack(side="left", padx=5)
        
        self.load_config_btn = ttk.Button(self.frame_buttons, text="Load Configuration", command=self.load_config)
        self.load_config_btn.pack(side="left", padx=5)
        
        self.toggle_btn = ttk.Button(self.frame_buttons, text="Run Analysis", command=self.toggle_analysis)
        self.toggle_btn.pack(side="right", padx=5)
        
        # Progress and Output
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(root, textvariable=self.progress_var)
        self.progress_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill="x", padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(root, height=15)
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load saved config if exists
        self.load_config()
    
    def update_output(self, text):
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    def save_config(self):
        config = {
            'token': self.token_var.get(),
            'sr': self.sr_var.get(),
            'domains': self.domains_text.get("1.0", tk.END).strip().split('\n')
        }
        try:
            with open('gui_config.json', 'w') as f:
                json.dump(config, f)
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving configuration: {str(e)}")

    def load_config(self):
        try:
            with open('gui_config.json', 'r') as f:
                config = json.load(f)
                self.token_var.set(config.get('token', ''))
                self.sr_var.set(config.get('sr', ''))
                self.domains_text.delete("1.0", tk.END)
                self.domains_text.insert("1.0", '\n'.join(config.get('domains', [])))
        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")

    def toggle_analysis(self):
        if not self.analyzer or not self.analyzer.is_running:
            if not all([self.token_var.get(), self.sr_var.get(), self.domains_text.get("1.0", tk.END).strip()]):
                messagebox.showerror("Error", "Please fill in all required fields")
                return
            
            self.toggle_btn.configure(text="Stop Analysis")
            self.progress.start()
            self.progress_var.set("Analysis in progress...")
            self.output_text.delete("1.0", tk.END)
            
            self.analyzer = CountCore(
                self.token_var.get(),
                self.sr_var.get(),
                self.domains_text.get("1.0", tk.END),
                self.update_output
            )
            
            def run_async():
                success = asyncio.run(self.analyzer.analyze())
                if success:
                    self.root.after(0, self.analysis_complete)
                else:
                    self.root.after(0, self.analysis_stopped)
            
            threading.Thread(target=run_async, daemon=True).start()
        else:
            self.analyzer.stop()
            self.toggle_btn.configure(text="Run Analysis")
            self.progress.stop()
            self.progress_var.set("Analysis stopped")
            self.update_output("Analysis stopped by user")

    def analysis_complete(self):
        self.toggle_btn.configure(text="Run Analysis")
        self.progress.stop()
        self.progress_var.set("Analysis complete!")
        messagebox.showinfo("Complete", "Analysis has been completed and report.md has been generated!")

    def analysis_stopped(self):
        self.toggle_btn.configure(text="Run Analysis")
        self.progress.stop()
        self.progress_var.set("Analysis stopped")

if __name__ == "__main__":
    root = tk.Tk()
    app = CountGUI(root)
    root.mainloop()