#!/usr/bin/env python3
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
import tkintermapview
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
                                     bg="#4CAF50", fg="black", font=("Arial", 10, "bold"), padx=20)
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
        tk.Button(self.geo_header, text="Copy GeoJSON", command=lambda: self.copy_to_clipboard(self.geo_text)).pack(side=tk.RIGHT, padx=2)
        tk.Button(self.geo_header, text="Show on Map", command=self.show_map, bg="#2196F3", fg="black").pack(side=tk.RIGHT, padx=2)
        
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

    def show_map(self):
        content = self.geo_text.get("1.0", tk.END).strip()
        if not content or content.startswith("No waypoints") or content.startswith("ERROR"):
            messagebox.showwarning("No Data", "No valid GeoJSON data to display on map.")
            return
        
        try:
            geojson_data = json.loads(content)
            MapWindow(self.root, geojson_data)
        except Exception as e:
            messagebox.showerror("Map Error", f"Could not display map: {str(e)}")

class MapWindow(tk.Toplevel):
    def __init__(self, parent, geojson_data):
        super().__init__(parent)
        self.title("GeoJSON Map View")
        self.geometry("900x700")
        
        # Button Section
        btn_frame = tk.Frame(self)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        tk.Label(btn_frame, text="Use Right Click to change map tile provider", fg="gray").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="📸 Copy Map to Clipboard", command=self.copy_map_to_clipboard, bg="#FF9800", fg="black").pack(side=tk.RIGHT)

        self.map_widget = tkintermapview.TkinterMapView(self, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True)
        
        # Set default tile server (OpenStreetMap)
        self.map_widget.set_tile_server("https://a.tile.openstreetmap.org/{z}/{x}/{y}.png")
        
        self.display_geojson(geojson_data)

    def display_geojson(self, geojson_data):
        features = geojson_data.get("features", [])
        if not features:
            return

        all_coords = []
        
        for feature in features:
            geom = feature.get("geometry", {})
            props = feature.get("properties", {})
            
            if geom.get("type") == "LineString":
                coords = geom.get("coordinates", [])
                # tkintermapview path needs (lat, lon)
                path_coords = [(lat, lon) for lon, lat in coords]
                if path_coords:
                    # Color based on transport mode if available
                    color = self.get_color_by_mode(props.get("transportMode"))
                    self.map_widget.set_path(path_coords, color=color, width=3)
                    all_coords.extend(path_coords)
                    
                    # Add marker at start and end
                    self.map_widget.set_marker(path_coords[0][0], path_coords[0][1], text=f"Start: {props.get('type','?')}")
                    self.map_widget.set_marker(path_coords[-1][0], path_coords[-1][1], text=f"End: {props.get('type','?')}")
        
        if all_coords:
            # Set map position to focus on the data
            lats = [c[0] for c in all_coords]
            lons = [c[1] for c in all_coords]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            
            avg_lat = (min_lat + max_lat) / 2
            avg_lon = (min_lon + max_lon) / 2
            
            self.map_widget.set_position(avg_lat, avg_lon)
            self.map_widget.set_zoom(14)

    def get_color_by_mode(self, mode):
        colors = {
            "bus": "#FF5722",
            "car": "#2196F3",
            "walking": "#4CAF50",
            "train": "#9C27B0",
            "cycling": "#FFEB3B",
            "stationary": "#9E9E9E"
        }
        return colors.get(str(mode).lower(), "#0000FF")

    def copy_map_to_clipboard(self):
        try:
            from PIL import ImageGrab
            import subprocess
            import os
            import tempfile
            from tkinter import messagebox

            # Update idletasks to ensure widget is drawn and position is correct
            self.update_idletasks()
            
            # Get widget position relative to screen
            # we need to consider the scaling factor on Mac/Retina
            # Tkinter winfo usually returns logical pixels.
            x1 = self.map_widget.winfo_rootx()
            y1 = self.map_widget.winfo_rooty()
            x2 = x1 + self.map_widget.winfo_width()
            y2 = y1 + self.map_widget.winfo_height()

            # Capture the widget
            # Note: ImageGrab.grab(bbox) on Mac might require screen recording permissions
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                temp_path = tmp.name
                img.save(temp_path)
            
            # Use AppleScript to put the image file into the clipboard on macOS
            script = f'set the clipboard to (read (POSIX file "{temp_path}") as «class PNGf»)'
            subprocess.run(['osascript', '-e', script], check=True)
            
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            messagebox.showinfo("Clipboard", "Map image copied to clipboard!\n(Note: Screen recording permission may be required if the image is blank)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy map image:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = JsonGeoTool(root)
    root.mainloop()
