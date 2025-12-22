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

        self.last_data = None
        
        # Main PanedWindow (Vertical)
        self.paned = tk.PanedWindow(root, orient=tk.VERTICAL, sashwidth=4, bg="#cccccc")
        self.paned.pack(fill=tk.BOTH, expand=True)

        # 1. Input Section
        self.input_frame = tk.LabelFrame(self.paned, text="1. Paste JSON Register Here", padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(self.input_frame, height=10, undo=True)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Process & Clear Buttons
        self.btn_frame = tk.Frame(self.input_frame, pady=5)
        self.btn_frame.pack(fill=tk.X)
        
        self.convert_btn = tk.Button(self.btn_frame, text="⚡ Process & Format", command=self.process_json, 
                                     bg="#00FF00", fg="black", font=("Arial", 10, "bold"), padx=20)
        self.convert_btn.pack(side=tk.RIGHT, padx=5)

        self.clear_btn = tk.Button(self.btn_frame, text="🗑 Clear All", command=self.clear_all, 
                                   bg="#f44336", fg="black", font=("Arial", 10), padx=15)
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        self.paned.add(self.input_frame)

        # 2. Pretty JSON Section
        self.pretty_frame = tk.LabelFrame(self.paned, text="2. Formatted JSON", padx=5, pady=5)
        self.paned.add(self.pretty_frame)
        
        self.pretty_header = tk.Frame(self.pretty_frame)
        self.pretty_header.pack(fill=tk.X)
        tk.Button(self.pretty_header, text="Copy formatted JSON", command=lambda: self.copy_to_clipboard(self.pretty_text)).pack(side=tk.RIGHT, padx=2)
        tk.Button(self.pretty_header, text="Copy Truncated (AI)", command=self.copy_truncated_json, bg="#e1f5fe").pack(side=tk.RIGHT, padx=2)
        
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

        # Configure tags for colors
        self.pretty_text.tag_configure("error", foreground="red")
        self.setup_highlight_tags(self.pretty_text)
        self.setup_highlight_tags(self.geo_text)

    def setup_highlight_tags(self, text_widget):
        """Define colors for JSON syntax highlighting"""
        text_widget.tag_configure("key", foreground="#1a73e8", font=("Courier", 10, "bold"))
        text_widget.tag_configure("string", foreground="#0d904f")
        text_widget.tag_configure("number", foreground="#d93025")
        text_widget.tag_configure("boolean", foreground="#9334e6")
        text_widget.tag_configure("null", foreground="#70757a")

    def highlight_json(self, text_widget, json_str):
        """Apply syntax highlighting to the JSON string in the widget"""
        import re
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", json_str)
        # Basic JSON highlighting regex
        for match in re.finditer(r'"([^"]+)"\s*:', json_str):
            text_widget.tag_add("key", f"1.0 + {match.start()} chars", f"1.0 + {match.end()-1} chars")
        for match in re.finditer(r':\s*"([^"]*)"', json_str):
            text_widget.tag_add("string", f"1.0 + {match.start()+1} chars", f"1.0 + {match.end()} chars")
        for match in re.finditer(r'-?\d+(?:\.\d+)?', json_str):
            if not text_widget.tag_names(f"1.0 + {match.start()} chars"):
                text_widget.tag_add("number", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def generate_html(self, text_widget):
        """Converts text widget content with tags to an HTML string."""
        content = text_widget.get("1.0", tk.END)
        html = ['<div style="font-family: monospace; white-space: pre; background-color: #ffffff; padding: 10px;">']
        # Simplified HTML generator for brevity but restoring the feature
        html.append(content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        html.append('</div>')
        return "".join(html)

    def copy_to_clipboard(self, text_widget, override_text=None):
        """Copies plain text and HTML to clipboard in an OS-agnostic way."""
        content = override_text if override_text else text_widget.get("1.0", tk.END).strip()
        if not content: return
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        import platform, subprocess
        if platform.system() == "Darwin":
            try:
                applescript = f'set the clipboard to "{content.replace('"', '\\"').replace('\\', '\\\\')}"'
                subprocess.run(['osascript', '-e', applescript], check=True)
            except: pass
        messagebox.showinfo("Copied", "Content copied to clipboard!")

    def copy_truncated_json(self):
        if not self.last_data:
            messagebox.showwarning("No Data", "Please process a JSON first.")
            return
        import copy
        truncated = copy.deepcopy(self.last_data)
        self._truncate_recursive(truncated)
        truncated_str = json.dumps(truncated, indent=2, ensure_ascii=False)
        self.copy_to_clipboard(None, override_text=truncated_str)

    def _truncate_recursive(self, obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if k == "waypoints" and isinstance(v, list) and len(v) > 2:
                    obj[k] = [v[0], v[-1]]
                else: self._truncate_recursive(v)
        elif isinstance(obj, list):
            for item in obj: self._truncate_recursive(item)

    def clear_all(self):
        """Clears all text widgets."""
        self.input_text.delete("1.0", tk.END)
        self.pretty_text.delete("1.0", tk.END)
        self.geo_text.delete("1.0", tk.END)

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
            
            # 1. Output Pretty JSON with Highlighting
            pretty_json = json.dumps(data, indent=2, ensure_ascii=False)
            self.highlight_json(self.pretty_text, pretty_json)
            self.last_data = data

            # 2. Output GeoJSON
            geojson_data = convert_to_geojson_data(data)
            
            # Only show if there are actual features
            if geojson_data.get("features"):
                final_geojson = json.dumps(geojson_data, indent=2, ensure_ascii=False)
                self.highlight_json(self.geo_text, final_geojson)
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
                    self.map_widget.set_path(path_coords, color="#00FF00", width=4)
                    all_coords.extend(path_coords)
                    
                    # Create small dot icons using PIL for a cleaner look
                    try:
                        from PIL import Image, ImageTk
                        # Create 10x10 dots
                        start_dot = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
                        end_dot = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
                        
                        from PIL import ImageDraw
                        # Start (White with Green border)
                        draw_s = ImageDraw.Draw(start_dot)
                        draw_s.ellipse((1, 1, 8, 8), fill="#FFFFFF", outline="#00FF00", width=2)
                        # End (Green with Black border)
                        draw_e = ImageDraw.Draw(end_dot)
                        draw_e.ellipse((1, 1, 8, 8), fill="#00FF00", outline="#000000", width=1)
                        
                        start_icon = ImageTk.PhotoImage(start_dot)
                        end_icon = ImageTk.PhotoImage(end_dot)
                        
                        # Keep references to avoid garbage collection
                        if not hasattr(self, "_marker_icons"): self._marker_icons = []
                        self._marker_icons.extend([start_icon, end_icon])

                        self.map_widget.set_marker(path_coords[0][0], path_coords[0][1], text="Start", icon=start_icon)
                        self.map_widget.set_marker(path_coords[-1][0], path_coords[-1][1], text="End", icon=end_icon)
                    except Exception:
                        # Fallback to standard icons if PIL fails
                        self.map_widget.set_marker(path_coords[0][0], path_coords[0][1], text="Start")
                        self.map_widget.set_marker(path_coords[-1][0], path_coords[-1][1], text="End")
        
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
        # User requested bright green (#00FF00)
        return "#00FF00"

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
