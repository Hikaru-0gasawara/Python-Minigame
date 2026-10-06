"""Animated, dependency-free Tkinter dungeon crawler."""

import math
import random
import time
import tkinter as tk

from dungeon import Dungeon, MODES, ROOMS

BG = "#0b101b"
PANEL = "#141d2e"
TEXT = "#edf1f8"
MUTED = "#94a4bd"
GOLD = "#f3c66b"
TEAL = "#66cde5"
RED = "#f57888"
FONT = "Segoe UI"


def label(parent, text="", size=11, color=TEXT, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                    font=(FONT, size), **kwargs)


def button(parent, text, command, primary=False):
    return tk.Button(parent, text=text, command=command, font=(FONT, 11, "bold"),
                     bg=GOLD if primary else "#24334b", fg=BG if primary else TEXT,
                     activebackground=TEAL, activeforeground=BG,
                     disabledforeground="#65748a", relief="flat", bd=0,
                     padx=14, pady=9, cursor="hand2", takefocus=True)


class DungeonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Trivia • A Masmorra dos Ecos")
        self.geometry("1240x850")
        self.minsize(1000, 760)
        self.configure(bg=BG)
        self.screen = None
        self.effects = tk.BooleanVar(value=True)
        self.show_setup()

    def swap(self, screen):
        if self.screen:
            self.screen.destroy()
        self.screen = screen
        screen.pack(fill="both", expand=True)

    def show_setup(self):
        self.swap(Setup(self))

    def start(self, difficulty, players):
        self.swap(Expedition(self, Dungeon(difficulty, players)))


class Setup(tk.Frame):
    def __init__(self, app):
        super().__init__(app, bg=BG)
        wrap = tk.Frame(self, bg=BG)
        wrap.place(relx=.5, rely=.5, anchor="center")
        label(wrap, "P Y T H O N   T R I V I A   /   D U N G E O N", 11, TEAL).pack()
        label(wrap, "A MASMORRA\nDOS ECOS", 40, GOLD, justify="center").pack(pady=12)
        label(wrap, "Três portas. Uma escolha. O relógio não espera.", 15).pack()
        label(wrap, "Acerte para abrir as portas. Explore rotas que se reencontram.\n"
                    "Alcance o guardião e vença seus 3 desafios antes do tempo acabar.\n"
                    "5 vidas compartilhadas · combos por acertos · bônus de velocidade",
              11, MUTED, justify="center").pack(pady=18)
        self.level = tk.IntVar(value=1)
        options = tk.Frame(wrap, bg=BG)
        options.pack(fill="x")
        for i, (name, floors, seconds, question_time) in MODES.items():
            text = f"{name}  /  {floors} níveis\n{seconds}s de expedição · {question_time}s por pergunta"
            if i == 4:
                text = f"{name}  /  {floors} níveis\n{seconds}s de expedição · perguntas de 30 → 15s"
            tk.Radiobutton(options, text=text, variable=self.level, value=i,
                           indicatoron=False, bg=PANEL, fg=TEXT, selectcolor="#31546a",
                           activebackground="#31546a", activeforeground=TEXT,
                           font=(FONT, 11), relief="flat", bd=0, padx=18, pady=14,
                           cursor="hand2").grid(row=(i-1)//2, column=(i-1)%2,
                                                sticky="ew", padx=4, pady=4)
        row = tk.Frame(wrap, bg=BG)
        row.pack(pady=15)
        label(row, "Aventureiros locais (cooperativo):", 11, MUTED).pack(side="left")
        self.players = tk.IntVar(value=1)
        tk.Spinbox(row, from_=1, to=4, textvariable=self.players, state="readonly",
                   width=3, font=(FONT, 12), readonlybackground=PANEL, fg=TEXT,
                   buttonbackground=PANEL).pack(side="left", padx=10)
        tk.Checkbutton(wrap, text="Efeitos animados (desative para movimento reduzido)",
                       variable=app.effects, bg=BG, fg=MUTED, selectcolor=PANEL,
                       activebackground=BG, activeforeground=TEXT).pack(pady=(0, 12))
        button(wrap, "ENTRAR NA MASMORRA  →",
               lambda: app.start(self.level.get(), self.players.get()), True).pack(fill="x")
        label(wrap, "As perguntas e respostas do banco atual estão em inglês.", 10, MUTED).pack(pady=12)


class Expedition(tk.Frame):
    def __init__(self, app, game):
        super().__init__(app, bg=BG)
        self.app, self.game = app, game
        self.job = None
        self.resume_at = 0
        self.particles = []
        self.popups = []
        self.display_score = 0
        self.last_frame = time.monotonic()
        self.hover = None
        self.finished = False
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=22, pady=(16, 12))
        label(header, "ECOS / DUNGEON", 19, GOLD).pack(side="left")
        self.stats = label(header, "", 13)
        self.stats.pack(side="right")

        main = tk.Frame(self, bg=BG)
        main.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 18))
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        self.room_title = label(main, "", 13, TEAL, anchor="w")
        self.room_title.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.scene = tk.Canvas(main, bg=BG, height=320, highlightthickness=1,
                               highlightbackground="#28364c")
        self.scene.grid(row=1, column=0, sticky="nsew")
        self.scene.bind("<Motion>", self.motion)
        self.scene.bind("<Leave>", lambda e: setattr(self, "hover", None))
        self.scene.bind("<Button-1>", self.scene_click)

        doors = tk.Frame(main, bg=BG)
        doors.grid(row=2, column=0, sticky="ew", pady=8)
        self.door_buttons = []
        for i, name in enumerate(("← ESQUERDA", "↑ EM FRENTE", "DIREITA →")):
            doors.columnconfigure(i, weight=1, uniform="door")
            btn = button(doors, name, lambda d=i: self.enter(d))
            btn.configure(font=(FONT, 10, "bold"), padx=3)
            btn.grid(row=0, column=i, sticky="ew", padx=3)
            self.door_buttons.append(btn)

        challenge = tk.Frame(main, bg=PANEL, padx=16, pady=12)
        challenge.grid(row=3, column=0, sticky="ew")
        self.q_meta = label(challenge, "", 10, TEAL, anchor="w")
        self.q_meta.pack(fill="x")
        self.q_text = label(challenge, "", 13, justify="left", anchor="w", wraplength=640)
        self.q_text.pack(fill="x", pady=(7, 8))
        challenge.bind("<Configure>", lambda e: self.q_text.configure(wraplength=max(250, e.width - 34)))
        answer_row = tk.Frame(challenge, bg=PANEL)
        answer_row.pack(fill="x")
        self.answer = tk.Entry(answer_row, bg="#0b1321", fg=TEXT, insertbackground=TEXT,
                               relief="flat", font=(FONT, 13), disabledbackground="#182237")
        self.answer.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 8))
        self.answer.bind("<Return>", lambda e: self.submit())
        self.submit_btn = button(answer_row, "RESPONDER ↵", self.submit, True)
        self.submit_btn.pack(side="right")
        self.q_bar = tk.Canvas(challenge, height=4, bg="#263047", highlightthickness=0)
        self.q_bar.pack(fill="x", pady=(10, 0))
        self.feedback = label(main, "A entrada está segura. Escolha sua primeira porta.",
                              11, GOLD, anchor="w", justify="left", wraplength=680)
        self.feedback.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        main.bind("<Configure>", lambda e: self.feedback.configure(wraplength=max(250, e.width - 10)))

        side = tk.Frame(self, bg=PANEL, width=290, padx=16, pady=14)
        side.grid(row=1, column=1, sticky="ns", padx=(0, 20), pady=(0, 18))
        side.pack_propagate(False)
        label(side, "TEMPO DA EXPEDIÇÃO", 10, MUTED).pack(anchor="w")
        self.clock_label = label(side, "", 28, GOLD)
        self.clock_label.pack(anchor="w")
        label(side, "O tempo corre também entre as portas.", 9, MUTED).pack(anchor="w")
        self.score_label = label(side, "0", 26)
        self.score_label.pack(anchor="w", pady=(8, 0))
        self.combo_label = label(side, "PONTOS  /  COMBO ×1,00", 10, TEAL)
        self.combo_label.pack(anchor="w")
        label(side, "MAPA DE ROTAS / NÍVEIS", 10, MUTED).pack(anchor="w", pady=(10, 4))
        self.map = tk.Canvas(side, width=258, height=220, bg="#0e1726", highlightthickness=0)
        self.map.pack(fill="x")
        label(side, "● Você   ·   ○ Revelada   ·   ◆ Guardião",
              9, MUTED, justify="left").pack(anchor="w", pady=6)
        self.roster = label(side, "", 10, justify="left", anchor="w")
        self.roster.pack(fill="x", pady=(4, 6))
        self.back_btn = button(side, "↓ Porta às suas costas", self.back)
        self.back_btn.pack(fill="x", pady=4)
        tk.Checkbutton(side, text="Efeitos animados", variable=app.effects,
                       bg=PANEL, fg=MUTED, selectcolor=BG,
                       activebackground=PANEL, activeforeground=TEXT).pack(anchor="w", pady=5)
        button(side, "Nova expedição", app.show_setup).pack(fill="x", side="bottom")
        side.bind("<Configure>", self.resize_map)
        self.refresh()
        self.frame()

    def destroy(self):
        if self.job is not None:
            self.after_cancel(self.job)
            self.job = None
        super().destroy()

    def resize_map(self, event):
        side = self.map.master
        used = 28  # Sidebar's vertical padding.
        for widget in side.winfo_children():
            if widget is self.map:
                continue
            pad = widget.pack_info().get("pady", 0)
            used += widget.winfo_reqheight() + (sum(pad) if isinstance(pad, tuple) else 2*int(pad))
        self.map.configure(height=max(80, min(240, event.height-used)))

    def enter(self, door):
        if self.game.enter(door):
            self.resume_at = 0
            self.feedback.configure(text=ROOMS[self.game.current.kind][1], fg=MUTED)
            self.refresh()

    def back(self):
        if self.game.back():
            self.feedback.configure(text="De volta à sala anterior. Você pode explorar outra rota.", fg=MUTED)
            self.refresh()

    def submit(self):
        if not self.game.question:
            return
        result = self.game.submit(self.answer.get())
        if result:
            self.result(result)

    def result(self, result):
        good = result["correct"]
        self.feedback.configure(text=result["message"], fg=GOLD if good else RED)
        self.resume_at = time.monotonic() + (1.3 if good else 3.0)
        caption = f"+{result['points']:,}" if good else "−1 VIDA" if "answer" in result else "TEMPO ESGOTADO"
        self.popups.append([caption,
                            .5, .42, 1.6, GOLD if good else RED])
        if good and self.app.effects.get():
            for _ in range(48):
                angle = random.random() * math.tau
                speed = random.uniform(.12, .6)
                self.particles.append([.5, .5, math.cos(angle)*speed,
                                       math.sin(angle)*speed, random.uniform(.5, 1.4),
                                       random.choice((GOLD, TEAL, "#ffffff"))])
        self.refresh()

    def refresh(self):
        g = self.game
        playing = g.status == "playing"
        ready = playing and g.current.cleared
        self.room_title.configure(text=f"NÍVEL {g.current.depth:02}/{g.floors:02}  /  "
                                  f"{ROOMS[g.current.kind][0].upper()}  /  {g.name.upper()}")
        exits = g.exits()
        for i, btn in enumerate(self.door_buttons):
            direction = ("← ESQUERDA", "↑ EM FRENTE", "DIREITA →")[i]
            kind = exits[i].kind if exits else "boss"
            hint = {"elite": "×2 pts / −25% tempo", "treasure": "×1,5 pontos",
                    "clock": "+12 segundos", "sanctuary": "+1 vida",
                    "combat": "Desafio comum", "boss": "3 acertos para vencer"}[kind]
            btn.configure(text=f"{direction}\n{ROOMS[kind][0]}\n{hint}",
                          fg=ROOMS[kind][2], state="normal" if ready and exits else "disabled")
        self.back_btn.configure(state="normal" if ready and g.history else "disabled")
        self.answer.configure(state="normal" if g.question and playing else "disabled")
        self.submit_btn.configure(state="normal" if g.question and playing else "disabled")
        if g.question:
            self.answer.delete(0, "end")
            self.q_text.configure(text=g.question["question"])
            self.answer.focus_set()
        elif not playing:
            self.q_text.configure(text="O guardião caiu. A masmorra é sua!" if g.status == "won"
                                  else "A expedição terminou. Uma nova rota espera por você.")
        elif g.current.cleared:
            self.q_text.configure(text="Sala liberada! Escolha uma das três portas para descer.")
        else:
            self.q_text.configure(text="Prepare-se para o próximo desafio…")
        if not playing:
            self.finished = True
            self.particles.clear()
        self.draw_map()

    def draw_map(self):
        c, g = self.map, self.game
        c.delete("all")
        w = max(c.winfo_width(), 258)
        h = max(c.winfo_height(), 80)
        step = (h-35)/6
        start = max(0, min(g.current.depth - 3, g.floors - 6))
        end = min(g.floors, start + 6)
        positions = {key: (54 + key[1] * (w - 100)/2, h-15 - (key[0] - start)*step)
                     for key in g.revealed if start <= key[0] <= end}
        for key, (x, y) in positions.items():
            if key in g.visited:
                for target, (tx, ty) in positions.items():
                    if target[0] == key[0] + 1:
                        c.create_line(x, y, tx, ty, fill="#26394c", width=1)
        for depth in range(start, end + 1):
            c.create_text(16, h-15 - (depth-start)*step, text=f"{depth:02}", fill=MUTED, font=(FONT, 8))
        for key, (x, y) in positions.items():
            room = g.rooms[key]
            current = key == g.current.key
            color = GOLD if current else ROOMS[room.kind][2]
            if current:
                c.create_oval(x-10, y-10, x+10, y+10, outline=GOLD, width=2)
            c.create_oval(x-5, y-5, x+5, y+5,
                          fill=color if room.cleared or current else "#0e1726", outline=color, width=2)
            if room.kind == "boss":
                c.create_text(x, y-13, text="◆", fill=RED)
        c.create_text(w-8, 12, text="PROFUNDEZA ↑", anchor="ne", fill=MUTED, font=(FONT, 8))

    def door_at(self, event):
        w, h = max(self.scene.winfo_width(), 1), max(self.scene.winfo_height(), 1)
        x, y = event.x / w, event.y / h
        for i, (left, top, right, bottom) in enumerate(self.door_bounds()):
            if left <= x <= right and top <= y <= bottom:
                return i
        return None

    @staticmethod
    def door_bounds():
        return ((.07, .30, .26, .81), (.40, .25, .60, .69), (.74, .30, .93, .81))

    def motion(self, event):
        self.hover = self.door_at(event)
        self.scene.configure(cursor="hand2" if self.hover is not None else "")

    def scene_click(self, event):
        door = self.door_at(event)
        if door is not None:
            self.enter(door)

    def draw_scene(self, now):
        c, g = self.scene, self.game
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        def polygon(points, **kw):
            return c.create_polygon(*[v * (w if i % 2 == 0 else h) for i, v in enumerate(points)], **kw)
        def line(points, **kw):
            return c.create_line(*[v * (w if i % 2 == 0 else h) for i, v in enumerate(points)], **kw)
        def text(x, y, value, color=MUTED, size=10, **kw):
            return c.create_text(x*w, y*h, text=value, fill=color, font=(FONT, size), **kw)
        polygon([0,0,1,0,.72,.18,.28,.18], fill="#0e1422")
        polygon([0,0,.28,.18,.28,.70,0,1], fill="#1b2538")
        polygon([1,0,.72,.18,.72,.70,1,1], fill="#162033")
        polygon([.28,.18,.72,.18,.72,.70,.28,.70], fill="#202c40")
        polygon([0,1,.28,.70,.72,.70,1,1], fill="#111b2c")
        for y in (.3, .43, .56, .69):
            line([.28,y,.72,y], fill="#2a384e")
        for x in (.32, .43, .56, .67):
            line([x,.18,x,.70], fill="#26344a")
        for x in (-.8, -.2, .3, .7, 1.2, 1.8):
            line([.5,.60,x,1], fill="#28354a")
        for y in (.75, .85, .98):
            line([0,y,1,y], fill="#26344a")
        exits = g.exits()
        for i, (left, top, right, bottom) in enumerate(self.door_bounds()):
            kind = exits[i].kind if exits else "boss"
            color = ROOMS[kind][2]
            active = g.current.cleared and g.status == "playing" and bool(exits)
            outline = color if active else "#48516a"
            width = 4 if self.hover == i and active else 2
            polygon([left,top+.07,left+.04,top,right-.04,top,right,top+.07,
                     right,bottom,left,bottom], fill="#080e1a", outline=outline, width=width)
            for j in range(1, 4):
                x = left + (right-left)*j/4
                line([x,top+.09,x,bottom-.02], fill="#273249", width=2)
            text((left+right)/2, top+.14, ("I", "II", "III")[i], outline, 19)
            text((left+right)/2, bottom-.14, "ABERTA" if active else "SELADA", outline, 9)
            text((left+right)/2, bottom+.055, ROOMS[kind][0].upper(), color, 10)
        # Torches and ambient embers; no flashing fullscreen overlays.
        for x in (.32, .68):
            flicker = math.sin(now*5 + x*20)*.008 if self.app.effects.get() else 0
            line([x,.39,x,.50], fill="#836146", width=5)
            polygon([x-.014,.39,x,.32+flicker,x+.014,.39,x,.42], fill=GOLD)
            if self.app.effects.get():
                for j in range(4):
                    y = .36 - ((now*.06+j*.065) % .22)
                    c.create_oval(x*w-1, y*h-1, x*w+1, y*h+1, fill=GOLD, outline="")
        text(.5,.09, "TRÊS ROTAS • UM DESTINO", MUTED, 10)
        text(.5,.95, "↓ ENTRADA ÀS SUAS COSTAS", MUTED, 9)
        if not g.current.cleared and g.status == "playing":
            color = ROOMS[g.current.kind][2]
            cy = .51 + (math.sin(now*2)*.012 if self.app.effects.get() else 0)
            polygon([.5,cy-.095,.55,cy,.5,cy+.095,.45,cy], fill="#26374e", outline=color, width=3)
            text(.5,cy,"?" if g.current.kind != "boss" else str(3-g.current.hits),color,24)
            text(.5,.77, "RESPONDA PARA ROMPER O SELO", color, 11)
        if self.app.effects.get():
            for x, y, vx, vy, life, color in self.particles:
                r = max(1, life*3)
                c.create_oval(x*w-r,y*h-r,x*w+r,y*h+r,fill=color,outline="")
            for value, x, y, life, color in self.popups:
                text(x,y,value,color,32)
        if self.finished:
            c.create_rectangle(w*.13,h*.25,w*.87,h*.75,fill=BG,outline=GOLD,width=2)
            won = g.status == "won"
            text(.5,.37,"MASMORRA CONQUISTADA" if won else "FIM DA EXPEDIÇÃO",GOLD if won else RED,22)
            text(.5,.50,f"{sum(g.scores):,} PONTOS",TEXT,30)
            text(.5,.63,f"Melhor combo: {g.best_combo}  ·  Salas visitadas: {len(g.visited)}",MUTED,11)

    def frame(self):
        now = time.monotonic()
        dt = min(.1, now-self.last_frame)
        self.last_frame = now
        result = self.game.tick()
        if result:
            self.result(result)
        if self.resume_at and now >= self.resume_at:
            self.resume_at = 0
            self.game.ask()
            self.refresh()
        g = self.game
        self.stats.configure(text=f"VIDAS {'♥' * g.lives}{'♡' * (5-g.lives)}    /    NÍVEL {g.current.depth:02}")
        seconds = math.ceil(g.remaining)
        self.clock_label.configure(text=f"{seconds//60:02}:{seconds%60:02}", fg=RED if seconds <= 30 else GOLD)
        target = sum(g.scores)
        self.display_score = min(target, self.display_score + max(1, int((target-self.display_score)*.18))) if self.app.effects.get() else target
        self.score_label.configure(text=f"{self.display_score:,}")
        multiplier = 1 + min(max(g.combo-1, 0), 9)*.25
        self.combo_label.configure(text=f"COMBO {g.combo}  /  MULTIPLICADOR ×{multiplier:.2f}")
        self.roster.configure(text="\n".join(f"{'›' if i == g.player else ' '} J{i+1}    {s:,} pts" for i,s in enumerate(g.scores)))
        qleft = g.question_remaining if g.question else 0
        meta = f"JOGADOR {g.player+1}  /  {math.ceil(qleft)}s PARA RESPONDER" if g.question else "ESCOLHA SUA ROTA" if g.status == "playing" else "RESULTADO DA EXPEDIÇÃO"
        if g.current.kind == "boss" and g.status == "playing":
            meta += f"  /  GUARDIÃO {g.current.hits}/3"
        self.q_meta.configure(text=meta, fg=RED if g.question and qleft<5 else TEAL)
        self.q_bar.delete("all")
        if g.question:
            self.q_bar.create_rectangle(0,0,self.q_bar.winfo_width()*qleft/g.question_duration,4,
                                        fill=RED if qleft<5 else TEAL,outline="")
        for p in self.particles:
            p[0] += p[2]*dt
            p[1] += p[3]*dt
            p[3] += .4*dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4]>0]
        for p in self.popups:
            p[2] -= .12*dt
            p[3] -= dt
        self.popups = [p for p in self.popups if p[3]>0]
        self.draw_scene(now)
        self.draw_map()
        self.job = self.after(33 if self.app.effects.get() else 100, self.frame)


def main():
    DungeonApp().mainloop()


if __name__ == "__main__":
    main()
