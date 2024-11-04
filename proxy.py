import os
import tkinter as tk
from tkinter import messagebox
import requests
from bs4 import BeautifulSoup
import re
import time
from threading import Thread

class ProxyChecker:
    def __init__(self, master):
        self.master = master
        master.title("Proxy Checker")

        self.label = tk.Label(master, text="Enter Proxy (format: ip:port):")
        self.label.pack()

        self.proxy_entry = tk.Entry(master, width=40)
        self.proxy_entry.pack(pady=10)

        self.check_button = tk.Button(master, text="Check Proxy", command=self.check_proxy)
        self.check_button.pack()

        self.scrape_button = tk.Button(master, text="Scrape Proxies", command=self.scrape_proxies)
        self.scrape_button.pack()

        self.result_label = tk.Label(master, text="", wraplength=300)
        self.result_label.pack(pady=10)

        self.proxy_list_label = tk.Label(master, text="Valid Proxies:")
        self.proxy_list_label.pack()

        self.proxy_listbox = tk.Listbox(master, width=50)
        self.proxy_listbox.pack(pady=10)

        self.proxies = []

        # Start the background thread to periodically check proxies
        self.check_thread = Thread(target=self.periodic_proxy_check, daemon=True)
        self.check_thread.start()

    def check_proxy(self):
        proxy = self.proxy_entry.get()
        if not proxy:
            messagebox.showwarning("Input Error", "Please enter a proxy.")
            return

        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        }

        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
            if response.status_code == 200:
                self.result_label.config(text=f"Proxy is working: {response.json()['origin']}")
                self.add_to_proxy_list(proxy)
            else:
                self.result_label.config(text="Proxy failed with status code: " + str(response.status_code))
        except requests.exceptions.RequestException as e:
            self.result_label.config(text=f"Proxy failed: {e}")

    def scrape_proxies(self):
        url = "https://www.free-proxy-list.net/"  # Example proxy list URL
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            proxy_list = set()

            # Regex to find IP:PORT patterns
            for item in soup.find_all('tr'):
                columns = item.find_all('td')
                if len(columns) > 1:  # Make sure there's enough columns
                    ip = columns[0].text
                    port = columns[1].text
                    proxy = f"{ip}:{port}"
                    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', proxy):
                        proxy_list.add(proxy)

            self.result_label.config(text=f"Found {len(proxy_list)} proxies.")
            for proxy in proxy_list:
                self.add_to_proxy_list(proxy)

        except requests.exceptions.RequestException as e:
            self.result_label.config(text=f"Failed to scrape proxies: {e}")

    def add_to_proxy_list(self, proxy):
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            self.proxy_listbox.insert(tk.END, proxy)
            self.result_label.config(text=f"Added proxy: {proxy}")
            self.save_proxy_to_file(proxy)

    def save_proxy_to_file(self, proxy):
        # Determine the proxy type and save it accordingly
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', proxy):
            ip, port = proxy.split(':')
            if port in ['80', '8080', '3128']:  # Common HTTP ports
                self.append_to_file('http_proxies.txt', proxy)
            elif port in ['443']:  # Common HTTPS port
                self.append_to_file('https_proxies.txt', proxy)
            elif port in ['1080']:  # Common SOCKS4 port
                self.append_to_file('socks4_proxies.txt', proxy)
            elif port in ['1080']:  # Common SOCKS5 port
                self.append_to_file('socks5_proxies.txt', proxy)

    def append_to_file(self, filename, proxy):
        if os.path.exists(filename) and os.path.getsize(filename) < 1 * 1024 * 1024 * 1024:  # less than 1 GB
            with open(filename, 'a') as f:
                f.write(proxy + '\n')
        elif not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(proxy + '\n')
        else:
            # If the file is full, create a new one with an incremented name
            base, ext = os.path.splitext(filename)
            counter = 1
            new_filename = f"{base}_{counter}{ext}"
            while os.path.exists(new_filename):
                counter += 1
                new_filename = f"{base}_{counter}{ext}"
            with open(new_filename, 'w') as f:
                f.write(proxy + '\n')

    def periodic_proxy_check(self):
        while True:
            time.sleep(60)  # Check every minute
            valid_proxies = []
            for proxy in self.proxies:
                proxies = {
                    "http": f"http://{proxy}",
                    "https": f"http://{proxy}",
                }
                try:
                    response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
                    if response.status_code == 200:
                        valid_proxies.append(proxy)
                except requests.exceptions.RequestException:
                    pass
            
            # Update the proxy listbox with valid proxies
            self.update_proxy_list(valid_proxies)

    def update_proxy_list(self, valid_proxies):
        # Remove proxies that are not valid
        self.proxies = valid_proxies
        self.proxy_listbox.delete(0, tk.END)  # Clear current list
        for proxy in valid_proxies:
            self.proxy_listbox.insert(tk.END, proxy)  # Reinsert valid proxies

if __name__ == "__main__":
    root = tk.Tk()
    app = ProxyChecker(root)
    root.mainloop()
