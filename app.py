"""
PDA-226: Album Cover Studio
İzmir University of Economics – SE 226 Project
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
import io
import webbrowser
import requests
from urllib.parse import quote
from PIL import Image, ImageTk
import google.generativeai as genai


GEMINI_API_KEY  = "" #insert api key
LASTFM_API_KEY  = "" #insert api key
LASTFM_BASE_URL = "" #insert api key


# COLOUR PALETTE

BG        = "#0d0d0d"
PANEL     = "#161616"
CARD      = "#1e1e1e"
BORDER    = "#2a2a2a"
GREEN     = "#1db954"
GREEN_DIM = "#158a3e"
WHITE     = "#ffffff"
GREY1     = "#b3b3b3"
GREY2     = "#535353"
GREY3     = "#282828"
RED       = "#e22134"


def fetch_tracks_by_tag(tag: str, limit: int = 10) -> list:
    params = {
        "method": "tag.gettoptracks",
        "tag":    tag,
        "limit":  limit,
        "api_key": LASTFM_API_KEY,
        "format": "json",
    }
    headers = {"User-Agent": "AlbumCoverStudio/1.0"}
    response = requests.get(LASTFM_BASE_URL, params=params,
                            headers=headers, timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get("tracks", {}).get("track", [])


def generate_cover(prompt: str) -> Image.Image:
    encoded = quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{encoded}"
           f"?width=600&height=600&nologo=true")
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")



GENRE_VISUALS = {
    "Pop":         "bright, colorful, modern pop aesthetics, clean commercial look",
    "Rock":        "dark gritty textures, electric energy, raw power",
    "Hip-Hop / Rap": "urban street art, bold typography, city lights",
    "Electronic":  "neon glows, digital patterns, futuristic cyberpunk",
    "Indie":       "lo-fi film grain, vintage tones, artistic and intimate",
    "R&B / Soul":  "warm golden tones, sensual atmosphere, smooth gradients",
    "Jazz":        "smoke, low-key lighting, classic smoky bar atmosphere",
    "Metal":       "dark and ominous, skulls, lightning, chaos, heavy",
    "Türk Pop":    "vibrant Mediterranean colors, modern Turkish aesthetic",
    "Klasik":      "elegant, orchestral, timeless classical painting style",
}

def call_gemini(journal: str, genre: str, era: str, track_count: int) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name="gemini-2.5-flash")

    prompt = f"""You are a creative music curator. Based on the journal entry below, create a fictional album.
Return ONLY a valid JSON object — no extra text, no markdown fences — with EXACTLY this schema:
{{
  "album_name": "string (creative fictional album name)",
  "artist_name": "string (fictional artist/band name)",
  "year": "string (a year in the {era} era)",
  "label": "string (fictional record label name)",
  "mood_description": "string (2-3 sentence poetic description of the album mood)",
  "cover_prompt": "string (a vivid Stable Diffusion / image-gen prompt for the album artwork, {GENRE_VISUALS.get(genre, '')})",
  "lastfm_tags": ["array of 5-7 lowercase Last.fm-compatible tag strings that match the mood and genre"]
}}

Genre: {genre}
Era: {era}
Requested track count: {track_count}
Journal entry:
\"\"\"{journal}\"\"\"
"""
    response = model.generate_content(prompt)
    text = response.text.strip()

    if text.startswith("```"):
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except Exception:
                continue
        raise ValueError("Could not parse JSON from Gemini response.")

    return json.loads(text)



class AlbumCoverStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Album Cover Studio")
        self.configure(bg=BG)
        self.minsize(1050, 680)
        self.resizable(True, True)

        self._setup_style()
        self._build_ui()

        # State
        self._album_data   = None
        self._tracklist    = []
        self._cover_image  = None   # PIL Image
        self._cover_tk     = None   # PhotoImage reference

    # Style
    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame",       background=BG)
        style.configure("Card.TFrame",  background=CARD)
        style.configure("Panel.TFrame", background=PANEL)

        style.configure("TLabel",
                        background=BG, foreground=WHITE,
                        font=("Helvetica", 11))
        style.configure("Title.TLabel",
                        background=BG, foreground=WHITE,
                        font=("Helvetica", 22, "bold"))
        style.configure("Sub.TLabel",
                        background=BG, foreground=GREY1,
                        font=("Helvetica", 10))
        style.configure("Green.TLabel",
                        background=BG, foreground=GREEN,
                        font=("Helvetica", 10, "bold"))
        style.configure("AlbumTitle.TLabel",
                        background=CARD, foreground=WHITE,
                        font=("Helvetica", 20, "bold"))
        style.configure("AlbumSub.TLabel",
                        background=CARD, foreground=GREY1,
                        font=("Helvetica", 10))
        style.configure("AlbumMood.TLabel",
                        background=CARD, foreground=GREY1,
                        font=("Helvetica", 10, "italic"),
                        wraplength=380)
        style.configure("Tag.TLabel",
                        background=CARD, foreground=GREEN,
                        font=("Helvetica", 9))
        style.configure("TrackNum.TLabel",
                        background=GREY3, foreground=GREY1,
                        font=("Helvetica", 10))
        style.configure("TrackTitle.TLabel",
                        background=GREY3, foreground=WHITE,
                        font=("Helvetica", 10, "bold"))
        style.configure("TrackArtist.TLabel",
                        background=GREY3, foreground=GREY1,
                        font=("Helvetica", 9))

        style.configure("TCombobox",
                        fieldbackground=GREY3, background=GREY3,
                        foreground=WHITE, selectbackground=GREEN,
                        arrowcolor=GREEN)
        style.map("TCombobox", fieldbackground=[("readonly", GREY3)],
                  foreground=[("readonly", WHITE)])

        style.configure("TSpinbox",
                        fieldbackground=GREY3, background=GREY3,
                        foreground=WHITE, arrowcolor=GREEN)

        style.configure("Generate.TButton",
                        background=GREEN, foreground=BG,
                        font=("Helvetica", 12, "bold"),
                        padding=10, relief="flat", borderwidth=0)
        style.map("Generate.TButton",
                  background=[("active", GREEN_DIM),
                               ("pressed", GREEN_DIM)])

        style.configure("Save.TButton",
                        background=GREEN, foreground=BG,
                        font=("Helvetica", 10, "bold"),
                        padding=8, relief="flat", borderwidth=0)
        style.map("Save.TButton",
                  background=[("active", GREEN_DIM)])

        style.configure("Listen.TButton",
                        background=GREY2, foreground=WHITE,
                        font=("Helvetica", 8, "bold"),
                        padding=4, relief="flat", borderwidth=0)
        style.map("Listen.TButton",
                  background=[("active", GREEN)])

    # ── UI Build ───────────────────────────────
    def _build_ui(self):
        # ── TOP BAR ──
        top = tk.Frame(self, bg=PANEL, height=56)
        top.pack(fill=tk.X, side=tk.TOP)
        tk.Label(top, text="  🎵  Album Cover Studio",
                 bg=PANEL, fg=WHITE,
                 font=("Helvetica", 16, "bold")).pack(side=tk.LEFT, padx=12, pady=12)
        tk.Label(top, text="Describe your mood, enjoy the generated tracklist.",
                 bg=PANEL, fg=GREY1,
                 font=("Helvetica", 10)).pack(side=tk.LEFT, padx=6)

        # ── MAIN AREA ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill=tk.BOTH, expand=True)

        # Left panel (inputs)
        left = tk.Frame(main, bg=BG, width=340)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(18, 0), pady=18)
        left.pack_propagate(False)
        self._build_left(left)

        # Separator
        sep = tk.Frame(main, bg=BORDER, width=1)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=12)

        # Right panel (results)
        right = tk.Frame(main, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 18), pady=18)
        self._build_right(right)

    def _build_left(self, parent):
        # Journal
        tk.Label(parent, text="Your Mood (English or Turkish)",
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.journal_text = tk.Text(
            parent, height=8, width=36,
            bg=GREY3, fg=WHITE, insertbackground=WHITE,
            relief="flat", font=("Helvetica", 10),
            wrap=tk.WORD, padx=8, pady=8)
        self.journal_text.pack(fill=tk.X, pady=(4, 14))
        self.journal_text.insert("1.0",
            "I was looking at the sea in İzmir. It was raining softly, "
            "and an old song was playing through my headphones. "
            "I felt both peaceful and melancholic…")

        # Genre
        tk.Label(parent, text="Genre",
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.genre_var = tk.StringVar(value="Pop")
        genres = ["Pop","Rock","Hip-Hop / Rap","Electronic","Indie",
                  "R&B / Soul","Jazz","Metal","Türk Pop","Klasik"]
        genre_cb = ttk.Combobox(parent, textvariable=self.genre_var,
                                values=genres, state="readonly", width=34)
        genre_cb.pack(fill=tk.X, pady=(4, 12))

        # Era
        tk.Label(parent, text="Era",
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.era_var = tk.StringVar(value="2000s")
        era_cb = ttk.Combobox(parent, textvariable=self.era_var,
                              values=["1970s","1980s","1990s","2000s","2010s","2020s"],
                              state="readonly", width=34)
        era_cb.pack(fill=tk.X, pady=(4, 12))

        # Track count
        tk.Label(parent, text="Track Count",
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.track_count_var = tk.IntVar(value=10)
        ttk.Spinbox(parent, from_=6, to=14,
                    textvariable=self.track_count_var,
                    width=6).pack(anchor="w", pady=(4, 16))

        # Generate button
        ttk.Button(parent, text="GENERATE ALBUM",
                   style="Generate.TButton",
                   command=self._on_generate).pack(fill=tk.X, pady=(4, 12))

        # Status label
        self.status_var = tk.StringVar(value="")
        tk.Label(parent, textvariable=self.status_var,
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 9, "italic"),
                 wraplength=320, justify="left").pack(anchor="w")

    def _build_right(self, parent):
        # Album header area
        self.header_frame = tk.Frame(parent, bg=BG)
        self.header_frame.pack(fill=tk.X, pady=(0, 12))

        # Cover image placeholder
        self.cover_label = tk.Label(
            self.header_frame,
            bg=GREY3, width=180, height=180,
            text="🎵", font=("Helvetica", 48),
            fg=GREY2)
        self.cover_label.pack(side=tk.LEFT)

        # Album metadata
        meta = tk.Frame(self.header_frame, bg=BG)
        meta.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(16, 0))

        tk.Label(meta, text="ALBUM • CURATED PLAYLIST",
                 bg=BG, fg=GREY2,
                 font=("Helvetica", 8, "bold")).pack(anchor="w")
        self.album_name_var = tk.StringVar(value="")
        tk.Label(meta, textvariable=self.album_name_var,
                 bg=BG, fg=WHITE,
                 font=("Helvetica", 22, "bold"),
                 wraplength=380, justify="left").pack(anchor="w")

        self.mood_var = tk.StringVar(value="")
        tk.Label(meta, textvariable=self.mood_var,
                 bg=BG, fg=GREY1,
                 font=("Helvetica", 10, "italic"),
                 wraplength=380, justify="left").pack(anchor="w", pady=(4, 4))

        self.meta_var = tk.StringVar(value="")
        tk.Label(meta, textvariable=self.meta_var,
                 bg=BG, fg=GREY1,
                 font=("Helvetica", 10)).pack(anchor="w")

        self.tags_var = tk.StringVar(value="")
        tk.Label(meta, textvariable=self.tags_var,
                 bg=BG, fg=GREEN,
                 font=("Helvetica", 9),
                 wraplength=380, justify="left").pack(anchor="w", pady=(4, 0))

        # Tracklist area (scrollable)
        tk.Label(parent, text="  #    TITLE",
                 bg=BG, fg=GREY2,
                 font=("Helvetica", 9, "bold")).pack(fill=tk.X, pady=(6, 2))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill=tk.X)

        scroll_frame = tk.Frame(parent, bg=BG)
        scroll_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        self.canvas = tk.Canvas(scroll_frame, bg=BG,
                                highlightthickness=0)
        vsb = ttk.Scrollbar(scroll_frame, orient="vertical",
                            command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.track_container = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.track_container, anchor="nw")

        self.track_container.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")))
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(
                self.canvas_window, width=e.width))

        # Placeholder
        self.placeholder = tk.Label(
            self.track_container,
            text="Generated tracklist will be shown here.",
            bg=BG, fg=GREY2,
            font=("Helvetica", 12))
        self.placeholder.pack(pady=40)

        # Save button (initially hidden)
        self.save_btn = ttk.Button(parent, text="SAVE ALBUM  (JSON + PNG)",
                                   style="Save.TButton",
                                   command=self._on_save)
        self.save_btn.pack(fill=tk.X, pady=(0, 4))
        self.save_btn.pack_forget()

    # ── Event handlers ─────────────────────────
    def _on_generate(self):
        journal = self.journal_text.get("1.0", tk.END).strip()
        if not journal:
            messagebox.showwarning("Input needed", "Please enter a mood or journal entry.")
            return

        if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
            messagebox.showerror("API Key Missing",
                "Please open app.py and set your GEMINI_API_KEY.")
            return
        if LASTFM_API_KEY == "YOUR_LASTFM_API_KEY_HERE":
            messagebox.showerror("API Key Missing",
                "Please open app.py and set your LASTFM_API_KEY.")
            return

        self._clear_results()
        self.status_var.set("🤖  Gemini is thinking…")
        threading.Thread(target=self._generate_worker,
                         args=(journal,), daemon=True).start()

    def _generate_worker(self, journal: str):
        genre       = self.genre_var.get()
        era         = self.era_var.get()
        track_count = self.track_count_var.get()

        try:
            # 1. Gemini – album metadata
            self.after(0, self.status_var.set, "🤖  Gemini is thinking…")
            album = call_gemini(journal, genre, era, track_count)

            # 2. Last.fm – real tracks
            self.after(0, self.status_var.set, "🎵  Fetching real tracks from Last.fm…")
            tags   = album.get("lastfm_tags", [])
            tracks = []
            seen   = set()
            for tag in tags:
                try:
                    raw = fetch_tracks_by_tag(tag, limit=20)
                    for t in raw:
                        key = (t.get("name","").lower(),
                               t.get("artist",{}).get("name","").lower())
                        if key not in seen:
                            seen.add(key)
                            tracks.append(t)
                except Exception:
                    pass
                if len(tracks) >= track_count * 3:
                    break

            # Trim to requested length
            tracks = tracks[:track_count]

            # 3. Image generation
            self.after(0, self.status_var.set, "🎨  Generating cover artwork…")
            cover_prompt = album.get("cover_prompt", genre + " album cover")
            genre_hint   = GENRE_VISUALS.get(genre, "")
            full_prompt  = f"{cover_prompt}, {genre_hint}, album cover art, square"
            cover_img    = generate_cover(full_prompt)

            self._album_data  = album
            self._tracklist   = tracks
            self._cover_image = cover_img

            self.after(0, self._display_results)

        except Exception as exc:
            self.after(0, self.status_var.set, f"❌  Error: {exc}")
            self.after(0, messagebox.showerror, "Generation Failed", str(exc))

    def _display_results(self):
        album  = self._album_data
        tracks = self._tracklist
        img    = self._cover_image

        # Cover image
        thumb = img.resize((180, 180), Image.LANCZOS)
        self._cover_tk = ImageTk.PhotoImage(thumb)
        self.cover_label.config(image=self._cover_tk, text="",
                                width=180, height=180)

        # Metadata
        self.album_name_var.set(album.get("album_name", "Unknown"))
        self.mood_var.set(album.get("mood_description", ""))
        year   = album.get("year", "")
        artist = album.get("artist_name", "")
        label  = album.get("label", "")
        self.meta_var.set(f"{year}  •  {len(tracks)} songs  •  {label}")
        tags_str = "  ".join(f"#{t}" for t in album.get("lastfm_tags", []))
        self.tags_var.set(tags_str)

        # Tracklist
        for w in self.track_container.winfo_children():
            w.destroy()

        for i, track in enumerate(tracks, start=1):
            title  = track.get("name", "Unknown")
            artist = track.get("artist", {})
            if isinstance(artist, dict):
                artist = artist.get("name", "Unknown")
            url = track.get("url", "")
            self._add_track_row(i, title, artist, url)

        # Status
        self.status_var.set(f"✓  {len(tracks)} real songs loaded")

        # Show save button
        self.save_btn.pack(fill=tk.X, pady=(0, 4))

    def _add_track_row(self, num: int, title: str, artist: str, url: str):
        row = tk.Frame(self.track_container, bg=GREY3,
                       pady=6, padx=8)
        row.pack(fill=tk.X, pady=2)

        # Row hover effect
        def on_enter(e, r=row): r.configure(bg="#333333")
        def on_leave(e, r=row): r.configure(bg=GREY3)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        tk.Label(row, text=f"{num:2d}", bg=GREY3, fg=GREY2,
                 font=("Helvetica", 10), width=3,
                 anchor="e").pack(side=tk.LEFT)

        info = tk.Frame(row, bg=GREY3)
        info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        tk.Label(info, text=title, bg=GREY3, fg=WHITE,
                 font=("Helvetica", 10, "bold"),
                 anchor="w").pack(anchor="w")
        tk.Label(info, text=artist, bg=GREY3, fg=GREY1,
                 font=("Helvetica", 9),
                 anchor="w").pack(anchor="w")

        if url:
            btn = ttk.Button(row, text="LISTEN",
                             style="Listen.TButton",
                             command=lambda u=url: webbrowser.open(u))
            btn.pack(side=tk.RIGHT, padx=(8, 0))

    def _on_save(self):
        if not self._album_data:
            return
        folder = filedialog.askdirectory(title="Choose save folder")
        if not folder:
            return
        try:
            album_name = self._album_data.get("album_name", "album")
            safe_name  = "".join(c if c.isalnum() or c in " _-" else "_"
                                 for c in album_name).strip()

            # Save JSON
            export_data = dict(self._album_data)
            export_data["tracklist"] = [
                {"title":  t.get("name", ""),
                 "artist": t.get("artist", {}).get("name", "")
                           if isinstance(t.get("artist"), dict)
                           else str(t.get("artist", "")),
                 "url":    t.get("url", "")}
                for t in self._tracklist
            ]
            json_path = os.path.join(folder, f"{safe_name}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            # Save PNG
            png_path = os.path.join(folder, f"{safe_name}_cover.png")
            self._cover_image.save(png_path)

            messagebox.showinfo("Saved",
                f"Album saved to:\n{folder}\n\n"
                f"• {safe_name}.json\n"
                f"• {safe_name}_cover.png")
        except Exception as exc:
            messagebox.showerror("Save Failed", str(exc))

    def _clear_results(self):
        self.album_name_var.set("")
        self.mood_var.set("")
        self.meta_var.set("")
        self.tags_var.set("")
        self.cover_label.config(image="", text="🎵",
                                font=("Helvetica", 48),
                                fg=GREY2,
                                width=180, height=180)
        self._cover_tk = None
        for w in self.track_container.winfo_children():
            w.destroy()
        self.placeholder = tk.Label(
            self.track_container,
            text="Generated tracklist will be shown here.",
            bg=BG, fg=GREY2,
            font=("Helvetica", 12))
        self.placeholder.pack(pady=40)
        self.save_btn.pack_forget()



# ENTRY POINT

if __name__ == "__main__":
    app = AlbumCoverStudio()
    app.mainloop()
