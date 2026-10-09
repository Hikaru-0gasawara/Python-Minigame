"""An illustrated, keyboard-accessible launch screen for the quiz crawler."""

import math
from pathlib import Path
import time
import tkinter as tk

from dungeon import MODES


BG = "#071015"
PANEL = "#0d1a21"
CARD = "#13262e"
LINE = "#25414a"
TEXT = "#edf8f8"
MUTED = "#95afb7"
TEAL = "#56eee5"
GOLD = "#efc788"
FONT = "Segoe UI"

MODE_COPY = {
    1: ("01 / DESCOBERTA", "No seu ritmo", "Mais tempo para pensar e encontrar seu caminho."),
    2: ("02 / DESAFIO", "Mantenha o combo", "Decisões rápidas. Acertos que viram combos."),
    3: ("03 / PRESSÃO", "Tempo é tudo", "Uma expedição intensa para quem aceita o risco."),
    4: ("04 / JORNADA", "Desafio crescente", "As perguntas ficam mais difíceis rumo ao núcleo."),
}


def _label(parent, text, size=10, color=TEXT, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size), **kwargs)


class Setup(tk.Frame):
    """All animation and bindings belong to this screen and die with it."""

    def __init__(self, app):
        super().__init__(app, bg=BG)
        self.app = app
        self.level = tk.IntVar(self, value=1)
        self.players = tk.IntVar(self, value=1)
        self.animation_job = None
        self.resize_job = None
        self.effects_trace = None
        self.art_loaded = False
        self._dead = False
        self._help = None
        self._photo = None
        self._started = time.monotonic()
        self.mode_buttons = []
        self.player_buttons = []
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=26, pady=(16, 12))
        _label(header, "◇  ECOS", 13, TEAL).pack(side="left")
        _label(header, "QUIZ  /  EXPLORAÇÃO  /  SOBREVIVÊNCIA", 9, MUTED).pack(side="left", padx=20)
        self.help_btn = self._button(header, "COMO JOGAR  ?", self._show_help)
        self.help_btn.configure(font=(FONT, 9, "bold"), pady=4, padx=12)
        self.help_btn.pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=20)
        body.columnconfigure(0, weight=56, uniform="body")
        body.columnconfigure(1, weight=44, uniform="body")
        body.rowconfigure(0, weight=1)
        self.hero = tk.Canvas(body, bg=BG, highlightthickness=1,
                              highlightbackground=LINE, takefocus=False)
        self.hero.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._hero_binding = self.hero.bind("<Configure>", self._queue_redraw)
        try:
            source = tk.PhotoImage(master=self, file=str(Path(__file__).resolve().parent / "assets" / "menu_observatory.png"))
            self._photo = source.subsample(2, 2)
            self.art_loaded = True
        except (tk.TclError, OSError):
            pass

        panel = tk.Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=LINE)
        panel.grid(row=0, column=1, sticky="nsew")
        form = tk.Frame(panel, bg=PANEL)
        form.pack(fill="x", expand=True, padx=20, pady=12)
        _label(form, "PREPARE SUA EXPEDIÇÃO", 9, TEAL, anchor="w").pack(fill="x")
        _label(form, "O próximo caminho\né uma resposta.", 20, TEXT,
               anchor="w", justify="left").pack(fill="x", pady=(5, 10))

        _label(form, "01  /  ESCOLHA O DESAFIO", 9, MUTED, anchor="w").pack(fill="x", pady=(0, 8))
        modes = tk.Frame(form, bg=PANEL)
        modes.pack(fill="x")
        for column in range(2):
            modes.columnconfigure(column, weight=1, uniform="mode")
        for value, (name, *_rest) in MODES.items():
            btn = self._button(modes, f"{name}\n{MODE_COPY[value][1]}",
                               lambda v=value: self._select_mode(v))
            btn.configure(anchor="w", justify="left", font=(FONT, 10, "bold"),
                          padx=10, pady=8)
            btn.grid(row=(value-1)//2, column=(value-1)%2, sticky="ew",
                     padx=(0, 6) if value % 2 else (6, 0), pady=3)
            self.mode_buttons.append(btn)

        self.mode_description = _label(form, "", 9, MUTED, anchor="w", justify="left", wraplength=370, height=2)
        self.mode_description.pack(fill="x", pady=(5, 3))
        stats = tk.Frame(form, bg=BG, padx=10, pady=7)
        stats.pack(fill="x")
        self.stat_values = []
        for i, name in enumerate(("EXPEDIÇÃO", "POR PERGUNTA", "SALAS")):
            stats.columnconfigure(i, weight=1, uniform="stat")
            value = _label(stats, "", 15, GOLD)
            value.grid(row=0, column=i)
            _label(stats, name, 8, MUTED).grid(row=1, column=i, pady=(3, 0))
            self.stat_values.append(value)

        _label(form, "02  /  SUA EQUIPE", 9, MUTED, anchor="w").pack(fill="x", pady=(12, 6))
        players = tk.Frame(form, bg=PANEL)
        players.pack(fill="x")
        for value in range(1, 5):
            players.columnconfigure(value-1, weight=1, uniform="player")
            btn = self._button(players, "1 · SOLO" if value == 1 else str(value),
                               lambda v=value: self._select_players(v))
            btn.configure(font=(FONT, 10, "bold"), padx=3, pady=6)
            btn.grid(row=0, column=value-1, sticky="ew", padx=(0 if value == 1 else 4, 0))
            self.player_buttons.append(btn)
        self.player_description = _label(form, "", 9, MUTED, anchor="w")
        self.player_description.pack(fill="x", pady=(5, 4))
        self.effects_toggle = tk.Checkbutton(
            form, text="Animações ambientes", variable=app.effects,
            bg=PANEL, fg=MUTED, activebackground=PANEL, activeforeground=TEXT,
            selectcolor=BG, font=(FONT, 10), borderwidth=0,
            highlightthickness=1, highlightbackground=PANEL, highlightcolor=TEAL,
            cursor="hand2", anchor="w", takefocus=True)
        self.effects_toggle.pack(fill="x", pady=(0, 3))
        self.effects_toggle.bind("<Return>", lambda event: self._invoke(self.effects_toggle))
        _label(form, "Desative para reduzir o movimento.", 8, MUTED,
               anchor="w").pack(fill="x", padx=4, pady=(0, 8))
        self.start_btn = self._button(form, "ENTRAR NA MASMORRA   →", self._start)
        self.start_btn.configure(bg=TEAL, fg=BG, activebackground="#b5fff5",
                                 activeforeground=BG, font=(FONT, 11, "bold"), pady=12)
        self.start_btn.pack(fill="x")
        _label(form, "5 vidas · acertos em sequência · caminhos imprevisíveis", 8,
               MUTED).pack(pady=(8, 0))

        footer = tk.Frame(self, bg=BG)
        footer.grid(row=2, column=0, sticky="ew", padx=25, pady=(12, 14))
        _label(footer, "TAB  navegar     ESPAÇO / ENTER  selecionar", 9, MUTED).pack(side="left")
        _label(footer, "Banco de perguntas e respostas em inglês", 9, MUTED).pack(side="right")
        self._select_mode(getattr(app, "menu_difficulty", 1))
        self._select_players(getattr(app, "menu_players", 1))
        self.effects_trace = app.effects.trace_add("write", self._effects_changed)
        self._effects_changed()

    def _button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command, bg=CARD, fg=TEXT,
                        activebackground="#23434b", activeforeground=TEXT,
                        relief="flat", bd=0, highlightthickness=1,
                        highlightbackground=LINE, highlightcolor=TEAL,
                        cursor="hand2", font=(FONT, 10, "bold"),
                        padx=12, pady=8, takefocus=True)
        btn.bind("<Return>", lambda event, widget=btn: self._invoke(widget))
        return btn

    @staticmethod
    def _invoke(widget):
        widget.invoke()
        return "break"

    def _select_mode(self, value):
        self.level.set(value)
        for i, btn in enumerate(self.mode_buttons, 1):
            selected = i == value
            name = MODES[i][0]
            btn.configure(bg="#193e45" if selected else CARD,
                          fg=TEAL if selected else TEXT,
                          highlightbackground=TEAL if selected else LINE,
                          text=f"{'●' if selected else '○'}  {name}\n{MODE_COPY[i][1]}")
        self.mode_description.configure(text=MODE_COPY[value][2])
        _name, size, duration, question = MODES[value]
        values = (f"{duration//60}:{duration%60:02}", "30 → 15s" if value == 4 else f"{question}s", str(3*(size-1)+2))
        for widget, text in zip(self.stat_values, values):
            widget.configure(text=text)

    def _select_players(self, value):
        self.players.set(value)
        for i, btn in enumerate(self.player_buttons, 1):
            btn.configure(bg="#193e45" if i == value else CARD,
                          fg=TEAL if i == value else TEXT,
                          highlightbackground=TEAL if i == value else LINE)
        text = "Você e o desconhecido." if value == 1 else f"{value} jogadores locais · respostas em turnos."
        self.player_description.configure(text=text)

    def _start(self):
        self.app.menu_difficulty = self.level.get()
        self.app.menu_players = self.players.get()
        self.app.start(self.level.get(), self.players.get())

    def _queue_redraw(self, _event=None):
        if self._dead:
            return
        if self.resize_job is not None:
            self.after_cancel(self.resize_job)
        self.resize_job = self.after(60, self._redraw)

    def _redraw(self):
        self.resize_job = None
        if self._dead:
            return
        canvas = self.hero
        w, h = canvas.winfo_width(), canvas.winfo_height()
        canvas.delete("scene")
        if self.art_loaded:
            canvas.create_image(w/2, h/2, image=self._photo, tags="scene")
        else:
            # Perspective architecture remains usable when the optional PNG is absent.
            cx, cy = w/2, h*.52
            for inset in range(0, 6):
                t = inset/6
                left, top = 18+(cx-95)*t, 175+(cy-95-175)*t
                right, bottom = w-left, h-35-(h-35-cy-95)*t
                canvas.create_rectangle(left, top, right, bottom, outline=LINE, width=2, tags="scene")
            for x in (0, w*.25, w*.75, w):
                canvas.create_line(x, h, cx, cy, fill=LINE, tags="scene")
            for radius in (85, 63, 30):
                canvas.create_polygon(cx, cy-radius, cx+radius, cy, cx, cy+radius,
                                      cx-radius, cy, outline=TEAL, fill=BG,
                                      width=2, tags="scene")
        # Quiet type on the art's dark upper and lower areas.
        canvas.create_text(30, 29, text="ARQUIVO  /  EXPEDIÇÃO ZERO", fill=TEAL,
                           font=(FONT, 9, "bold"), anchor="nw", tags="scene")
        canvas.create_text(26, 47, text="ECOS", fill=TEXT,
                           font=(FONT, 70, "bold"), anchor="nw", tags="scene")
        canvas.create_text(32, 156, text="A  M A S M O R R A  D O S  E C O S", fill=GOLD,
                           font=(FONT, 10, "bold"), anchor="nw", tags="scene")
        canvas.create_line(32, 188, 102, 188, fill=TEAL, width=2, tags="scene")
        canvas.create_rectangle(1, h-97, w-1, h-1, fill=BG, outline="", tags="scene")
        canvas.create_text(30, h-76, text="O CONHECIMENTO ABRE PORTAS.", fill=TEXT,
                           font=(FONT, 13, "bold"), anchor="nw", tags="scene")
        canvas.create_text(30, h-45, text="Encontre o núcleo. Faça cada resposta valer.", fill=MUTED,
                           font=(FONT, 10), anchor="nw", tags="scene")
        canvas.create_line(w-28, 25, w-28, 51, fill=GOLD, tags="scene")
        canvas.create_line(w-54, 25, w-28, 25, fill=GOLD, tags="scene")
        canvas.tag_lower("scene")

    def _effects_changed(self, *_args):
        if self._dead:
            return
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
            self.animation_job = None
        self.hero.delete("ambient")
        if self.app.effects.get():
            self._animate()

    def _animate(self):
        self.animation_job = None
        if self._dead or not self.app.effects.get():
            return
        canvas = self.hero
        w, h = canvas.winfo_width(), canvas.winfo_height()
        elapsed = time.monotonic()-self._started
        canvas.delete("ambient")
        available = max(1, h-330)
        for i in range(16):
            x = w*(.16+((i*37)%71)/100) + math.sin(elapsed*.25+i)*6
            y = 215+((i*83-elapsed*(5+i%4)) % available)
            radius = 1 if i % 3 else 1.5
            canvas.create_oval(x-radius, y-radius, x+radius, y+radius,
                               fill="#54888b" if i % 3 else GOLD, outline="", tags="ambient")
        self.animation_job = self.after(50, self._animate)

    def _show_help(self):
        if self._help is not None and self._help.winfo_exists():
            self._help.lift()
            return
        dialog = self._help = tk.Toplevel(self)
        dialog.title("Como jogar · ECOS")
        dialog.configure(bg=PANEL, padx=26, pady=24)
        dialog.transient(self.app)
        dialog.resizable(False, False)
        _label(dialog, "CADA RESPOSTA ABRE UM CAMINHO", 16, TEAL).pack(anchor="w", pady=(0, 18))
        for title, detail in (
            ("01  EXPLORE", "Escolha portas e descubra a masmorra pelo minimapa.\nAlt + setas: mover. Alt + Q/E: olhar para os lados."),
            ("02  RESPONDA", "Digite a resposta em inglês e pressione Enter.\nAcertos em sequência e velocidade aumentam os pontos."),
            ("03  ENCONTRE O NÚCLEO", "Vença seus 3 desafios antes que o tempo acabe.\nA equipe compartilha 5 vidas e o relógio da expedição."),
        ):
            _label(dialog, title, 10, GOLD).pack(anchor="w")
            _label(dialog, detail, 11, TEXT, justify="left").pack(anchor="w", pady=(5, 17))
        close = self._button(dialog, "ENTENDI   →", dialog.destroy)
        close.pack(fill="x", pady=(5, 0))
        dialog.bind("<Escape>", lambda event: dialog.destroy())
        dialog.grab_set()
        close.focus_set()

    def destroy(self):
        if self._dead:
            return
        self._dead = True
        for name in ("animation_job", "resize_job"):
            job = getattr(self, name)
            if job is not None:
                self.after_cancel(job)
                setattr(self, name, None)
        if self.effects_trace is not None:
            self.app.effects.trace_remove("write", self.effects_trace)
            self.effects_trace = None
        self.hero.unbind("<Configure>", self._hero_binding)
        if self._help is not None and self._help.winfo_exists():
            self._help.destroy()
        super().destroy()
