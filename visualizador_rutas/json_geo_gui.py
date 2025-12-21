#!/usr/bin/env python3
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
from waypoints_to_geojson import convert_to_geojson_data

class JsonGeoTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentiance JSON & GeoJSON Viewer")
        self.root.geometry("1000x800")

        # Main PanedWindow (Vertical)
        self.paned = tk.PanedWindow(root, orient=tk.VERTICAL, sashwidth=4, bg="#cccccc")
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 1. Input Section
        self.input_frame = tk.LabelFrame(self.paned, text="1. Paste JSON Register Here", padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(self.input_frame, height=10, undo=True)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.input_frame)

        # Button Section (between input and output)
        self.btn_frame = tk.Frame(root, pady=5)
        self.btn_frame.pack(fill=tk.X)
        self.convert_btn = tk.Button(self.btn_frame, text="Process & Format", command=self.process_json, 
                                     bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.convert_btn.pack()

        # 2. Pretty JSON Section
        self.pretty_frame = tk.LabelFrame(self.paned, text="2. Formatted JSON", padx=5, pady=5)
        self.paned.add(self.pretty_frame)
        
        self.pretty_header = tk.Frame(self.pretty_frame)
        self.pretty_header.pack(fill=tk.X)
        tk.Button(self.pretty_header, text="Copy formatted JSON", command=lambda: self.copy_to_clipboard(self.pretty_text)).pack(side=tk.RIGHT)
        
        self.pretty_text = scrolledtext.ScrolledText(self.pretty_frame, height=10)
        self.pretty_text.pack(fill=tk.BOTH, expand=True)

        # 3. GeoJSON Section
        self.geo_frame = tk.LabelFrame(self.paned, text="3. Generated GeoJSON", padx=5, pady=5)
        self.paned.add(self.geo_frame)
        
        self.geo_header = tk.Frame(self.geo_frame)
        self.geo_header.pack(fill=tk.X)
        tk.Button(self.geo_header, text="Copy GeoJSON", command=lambda: self.copy_to_clipboard(self.geo_text)).pack(side=tk.RIGHT)
        
        self.geo_text = scrolledtext.ScrolledText(self.geo_frame, height=10)
        self.geo_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for colors if needed
        self.pretty_text.tag_configure("error", foreground="red")

    def copy_to_clipboard(self, text_widget):
        content = text_widget.get("1.0", tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Copied", "Content copied to clipboard!")

    def process_json(self):
        # Clear previous outputs
        self.pretty_text.delete("1.0", tk.END)
        self.geo_text.delete("1.0", tk.END)

        raw_content = self.input_text.get("1.0", tk.END).strip()
        if not raw_content:
            return

        try:
            # Parse JSON
            data = json.loads(raw_content)
            
            # 1. Output Pretty JSON
            pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
            self.pretty_text.insert(tk.END, pretty_json)

            # 2. Output GeoJSON
            geojson_data = convert_to_geojson_data(data)
            
            # Only show if there are actual features
            if geojson_data.get("features"):
                final_geojson = json.dumps(geojson_data, indent=2, ensure_ascii=False)
                self.geo_text.insert(tk.END, final_geojson)
            else:
                self.geo_text.insert(tk.END, "No waypoints found in the input JSON.")

        except json.JSONDecodeError as e:
            messagebox.showerror("JSON Error", f"Failed to parse input JSON:\n{str(e)}")
            self.pretty_text.insert(tk.END, f"ERROR: {str(e)}", "error")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonGeoTool(root)
    root.mainloop()
