"""
NeoBank GUI - a modern, dark-themed Tkinter desktop application.

This is a thin presentation layer over ``BankService``: it collects input,
renders a polished UI, and delegates every banking operation to the service.
No business logic, storage or hashing lives here.

Screens
-------
* Welcome / Login / Register  (account-number + PIN auth)
* Dashboard with sidebar navigation:
    - Overview  (balance card + quick actions)
    - Deposit / Withdraw / Transfer
    - Statement (styled transaction table)
    - Settings  (change PIN, close account)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from ..exceptions import BankError
from ..models import AccountType
from ..repository import JsonAccountRepository
from ..services import BankService
from ..utils import money
from .theme import C, Button, Card, Field, fonts, round_rect


class NeoBankApp(tk.Tk):
    def __init__(self, service: Optional[BankService] = None):
        super().__init__()
        self.service = service or BankService(JsonAccountRepository())
        self.f = fonts()
        self.current_account: Optional[str] = None
        self.current_pin: Optional[str] = None

        self.title("NeoBank  -  Digital Banking")
        self.geometry("1040x680")
        self.minsize(940, 620)
        self.configure(bg=C.BG)
        self._center()
        self._init_ttk_style()

        self.container = tk.Frame(self, bg=C.BG)
        self.container.pack(fill="both", expand=True)
        self.show_welcome()

    # ----- window helpers --------------------------------------------- #
    def _center(self):
        self.update_idletasks()
        w, h = 1040, 680
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _init_ttk_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        # Treeview (transaction table) styling
        style.configure(
            "Neo.Treeview", background=C.CARD, fieldbackground=C.CARD,
            foreground=C.TEXT, rowheight=30, borderwidth=0, font=self.f["body"],
        )
        style.configure(
            "Neo.Treeview.Heading", background=C.SIDEBAR, foreground=C.MUTED,
            font=self.f["small"], borderwidth=0, relief="flat",
        )
        style.map("Neo.Treeview", background=[("selected", C.CARD_HI)],
                  foreground=[("selected", C.ACCENT)])
        style.map("Neo.Treeview.Heading", background=[("active", C.SIDEBAR)])

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    # ----- toast notification ----------------------------------------- #
    def toast(self, message: str, kind: str = "info"):
        color = {"info": C.BLUE, "success": C.GOOD, "error": C.BAD}.get(kind, C.BLUE)
        icon = {"info": "i", "success": "\u2713", "error": "\u2715"}.get(kind, "i")
        t = tk.Toplevel(self)
        t.overrideredirect(True)
        t.configure(bg=C.CARD)
        t.attributes("-topmost", True)
        self.update_idletasks()
        cv = Card(t, 360, 56, fill=C.CARD, stroke=color, radius=14)
        cv.pack()
        cv.create_oval(16, 18, 40, 42, fill=color, outline=color)
        cv.create_text(28, 30, text=icon, fill="#06231F", font=self.f["body_b"])
        cv.create_text(54, 28, text=message, fill=C.TEXT, font=self.f["body"],
                       anchor="w", width=290)
        x = self.winfo_rootx() + self.winfo_width() - 390
        y = self.winfo_rooty() + 24
        t.geometry(f"360x56+{x}+{y}")
        t.after(2600, t.destroy)

    # ================================================================= #
    #  WELCOME / AUTH
    # ================================================================= #
    def show_welcome(self):
        self._clear()
        wrap = tk.Frame(self.container, bg=C.BG)
        wrap.pack(fill="both", expand=True)

        # ---- left brand panel (gradient) ---- #
        left = tk.Canvas(wrap, width=440, bg=C.GRAD_TOP, highlightthickness=0)
        left.pack(side="left", fill="y")
        left.update_idletasks()
        self._paint_brand(left)

        # ---- right auth panel ---- #
        right = tk.Frame(wrap, bg=C.BG)
        right.pack(side="left", fill="both", expand=True)
        self._auth_panel(right)

    def _paint_brand(self, cv: tk.Canvas):
        cv.update_idletasks()
        h = self.winfo_height() or 680
        # gradient
        r1, g1, b1 = cv.winfo_rgb(C.VIOLET)
        r2, g2, b2 = cv.winfo_rgb(C.GRAD_BOT)
        for i in range(h):
            r = int(r1 + (r2 - r1) * i / h) >> 8
            g = int(g1 + (g2 - g1) * i / h) >> 8
            b = int(b1 + (b2 - b1) * i / h) >> 8
            cv.create_line(0, i, 440, i, fill=f"#{r:02x}{g:02x}{b:02x}")
        # decorative circles
        cv.create_oval(300, -60, 520, 160, outline=C.TINT_LIGHT, width=2)
        cv.create_oval(-80, 420, 160, 660, outline=C.TINT_SOFT, width=2)
        # logo + tagline
        cv.create_oval(60, 120, 108, 168, fill=C.ACCENT, outline="")
        cv.create_text(84, 144, text="N", fill="#06231F", font=self.f["display"])
        cv.create_text(120, 144, text="NeoBank", fill="white", anchor="w",
                       font=self.f["logo"])
        cv.create_text(62, 230, text="Banking,\nreimagined.", fill="white",
                       anchor="nw", font=(self.f["display"][0], 30, "bold"),
                       justify="left")
        cv.create_text(62, 340, anchor="nw", fill="#E9E4FF", width=320,
                       font=self.f["body"], justify="left",
                       text=("Secure accounts, instant transfers and a clean, "
                             "modern experience - powered by a production-grade "
                             "Python engine."))
        for i, feat in enumerate(["Salted PIN encryption",
                                  "Atomic, crash-safe transfers",
                                  "Real-time statements"]):
            y = 440 + i * 38
            cv.create_oval(62, y, 78, y + 16, fill=C.ACCENT, outline="")
            cv.create_text(70, y + 8, text="\u2713", fill="#06231F",
                           font=self.f["small"])
            cv.create_text(94, y + 8, text=feat, fill="white", anchor="w",
                           font=self.f["body"])

    def _auth_panel(self, parent, mode="login"):
        for w in parent.winfo_children():
            w.destroy()
        center = tk.Frame(parent, bg=C.BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        title = "Welcome back" if mode == "login" else "Create your account"
        sub = ("Sign in to access your account."
               if mode == "login" else "Open a NeoBank account in seconds.")
        tk.Label(center, text=title, bg=C.BG, fg=C.TEXT,
                 font=self.f["h1"]).pack(anchor="w")
        tk.Label(center, text=sub, bg=C.BG, fg=C.MUTED,
                 font=self.f["body"]).pack(anchor="w", pady=(2, 22))

        fields = {}
        if mode == "register":
            fields["name"] = Field(center, "Full name")
            fields["name"].pack(fill="x", pady=7)

            type_row = tk.Frame(center, bg=C.BG)
            type_row.pack(fill="x", pady=7)
            tk.Label(type_row, text="ACCOUNT TYPE", bg=C.BG, fg=C.MUTED,
                     font=self.f["small"]).pack(anchor="w")
            self._acc_type = tk.StringVar(value="SAVINGS")
            seg = tk.Frame(type_row, bg=C.BG)
            seg.pack(fill="x", pady=(4, 0))
            for t in ("SAVINGS", "CURRENT"):
                tk.Radiobutton(
                    seg, text=t.title(), value=t, variable=self._acc_type,
                    bg=C.BG, fg=C.TEXT, selectcolor=C.CARD, activebackground=C.BG,
                    activeforeground=C.ACCENT, font=self.f["body"],
                    indicatoron=True,
                ).pack(side="left", padx=(0, 18))
        else:
            fields["acc"] = Field(center, "Account number")
            fields["acc"].pack(fill="x", pady=7)

        fields["pin"] = Field(center, "PIN", show="\u2022")
        fields["pin"].pack(fill="x", pady=7)
        if mode == "register":
            fields["opening"] = Field(center, "Opening deposit (optional)")
            fields["opening"].set("0")
            fields["opening"].pack(fill="x", pady=7)

        def do_login():
            try:
                acc = fields["acc"].get()
                pin = fields["pin"].get()
                self.service.get_balance(acc, pin)  # validates auth
                self.current_account, self.current_pin = acc, pin
                self.toast("Signed in successfully", "success")
                self.show_dashboard()
            except BankError as e:
                self.toast(str(e), "error")

        def do_register():
            try:
                name = fields["name"].get()
                atype = AccountType(self._acc_type.get())
                pin = fields["pin"].get()
                opening = float(fields["opening"].get() or 0)
                acc = self.service.open_account(name, atype, pin, opening)
                self.current_account, self.current_pin = acc.account_number, pin
                self.toast(f"Account {acc.account_number} created!", "success")
                self.show_dashboard()
            except (BankError, ValueError) as e:
                self.toast(str(e), "error")

        Button(center, "Sign in" if mode == "login" else "Create account",
               do_login if mode == "login" else do_register,
               width=320, height=46).pack(pady=(22, 10))

        switch = tk.Frame(center, bg=C.BG)
        switch.pack()
        q = ("New to NeoBank?" if mode == "login" else "Already have an account?")
        link = ("Create an account" if mode == "login" else "Sign in")
        tk.Label(switch, text=q, bg=C.BG, fg=C.MUTED,
                 font=self.f["small"]).pack(side="left")
        lbl = tk.Label(switch, text=" " + link, bg=C.BG, fg=C.ACCENT,
                       font=self.f["small"], cursor="hand2")
        lbl.pack(side="left")
        lbl.bind("<Button-1>", lambda _:
                 self._auth_panel(parent, "register" if mode == "login" else "login"))

    # ================================================================= #
    #  DASHBOARD
    # ================================================================= #
    def show_dashboard(self):
        self._clear()
        root = tk.Frame(self.container, bg=C.BG)
        root.pack(fill="both", expand=True)

        # ---- sidebar ---- #
        side = tk.Frame(root, bg=C.SIDEBAR, width=230)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        logo = tk.Frame(side, bg=C.SIDEBAR)
        logo.pack(fill="x", pady=(26, 30), padx=22)
        dot = tk.Canvas(logo, width=34, height=34, bg=C.SIDEBAR,
                        highlightthickness=0)
        dot.pack(side="left")
        dot.create_oval(2, 2, 32, 32, fill=C.ACCENT, outline="")
        dot.create_text(17, 17, text="N", fill="#06231F", font=self.f["h2"])
        tk.Label(logo, text="NeoBank", bg=C.SIDEBAR, fg=C.TEXT,
                 font=self.f["h2"]).pack(side="left", padx=10)

        self.nav_buttons = {}
        nav = [("Overview", "\u25C9"), ("Deposit", "\u2193"),
               ("Withdraw", "\u2191"), ("Transfer", "\u21C4"),
               ("Statement", "\u2630"), ("Settings", "\u2699")]
        for name, icon in nav:
            self._nav_item(side, name, icon)

        # logout pinned to bottom
        spacer = tk.Frame(side, bg=C.SIDEBAR)
        spacer.pack(fill="both", expand=True)
        out = tk.Label(side, text="   \u2190   Sign out", bg=C.SIDEBAR,
                       fg=C.MUTED, font=self.f["body"], anchor="w", cursor="hand2")
        out.pack(fill="x", padx=18, pady=18, ipady=6)
        out.bind("<Button-1>", lambda _: self._logout())
        out.bind("<Enter>", lambda _: out.config(fg=C.BAD))
        out.bind("<Leave>", lambda _: out.config(fg=C.MUTED))

        # ---- main content area ---- #
        self.content = tk.Frame(root, bg=C.BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._select_nav("Overview")

    def _nav_item(self, parent, name, icon):
        item = tk.Label(parent, text=f"   {icon}    {name}", bg=C.SIDEBAR,
                        fg=C.MUTED, font=self.f["body"], anchor="w", cursor="hand2")
        item.pack(fill="x", padx=14, pady=3, ipady=9)
        item.bind("<Button-1>", lambda _: self._select_nav(name))
        item.bind("<Enter>", lambda _: item.config(fg=C.TEXT)
                  if self._active != name else None)
        item.bind("<Leave>", lambda _: item.config(fg=C.MUTED)
                  if self._active != name else None)
        self.nav_buttons[name] = item

    _active = "Overview"

    def _select_nav(self, name):
        self._active = name
        for n, btn in self.nav_buttons.items():
            if n == name:
                btn.config(fg=C.ACCENT, bg=C.CARD)
            else:
                btn.config(fg=C.MUTED, bg=C.SIDEBAR)
        {
            "Overview": self._page_overview,
            "Deposit": lambda: self._page_money("Deposit"),
            "Withdraw": lambda: self._page_money("Withdraw"),
            "Transfer": self._page_transfer,
            "Statement": self._page_statement,
            "Settings": self._page_settings,
        }[name]()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _header(self, title, subtitle):
        bar = tk.Frame(self.content, bg=C.BG)
        bar.pack(fill="x", padx=36, pady=(28, 6))
        tk.Label(bar, text=title, bg=C.BG, fg=C.TEXT,
                 font=self.f["h1"]).pack(anchor="w")
        tk.Label(bar, text=subtitle, bg=C.BG, fg=C.MUTED,
                 font=self.f["body"]).pack(anchor="w", pady=(2, 0))

    def _account(self):
        return self.service.get_account(self.current_account, self.current_pin)

    # ----- Overview ---------------------------------------------------- #
    def _page_overview(self):
        self._clear_content()
        acc = self._account()
        self._header(f"Hello, {acc.holder_name.split()[0]}",
                     "Here's your account at a glance.")

        body = tk.Frame(self.content, bg=C.BG)
        body.pack(fill="both", expand=True, padx=36, pady=10)

        # balance card (gradient)
        bal = tk.Canvas(body, width=440, height=180, bg=C.BG,
                        highlightthickness=0)
        bal.pack(anchor="w")
        r1, g1, b1 = bal.winfo_rgb(C.VIOLET)
        r2, g2, b2 = bal.winfo_rgb(C.BLUE)
        # rounded gradient fill emulation: draw rounded base then text
        round_rect(bal, 0, 0, 440, 180, r=22, fill=C.VIOLET, outline="")
        bal.create_oval(300, -40, 520, 130, fill=C.TINT_CARD, outline="")
        bal.create_text(28, 30, text="TOTAL BALANCE", fill="#E9E4FF",
                        anchor="w", font=self.f["small"])
        bal.create_text(28, 70, text=money(acc.balance), fill="white",
                        anchor="w", font=(self.f["display"][0], 30, "bold"))
        bal.create_text(28, 120, text=f"Account  {acc.account_number}",
                        fill="#E9E4FF", anchor="w", font=self.f["body"])
        bal.create_text(28, 148, text=f"{acc.account_type.value} ACCOUNT  \u2022  "
                        f"{acc.status.value}", fill="#CBD5F5", anchor="w",
                        font=self.f["small"])

        # quick stat cards
        stats = tk.Frame(body, bg=C.BG)
        stats.pack(fill="x", pady=22)
        txns = acc.transactions
        deposits = sum(t.amount for t in txns if t.type.value in ("DEPOSIT", "TRANSFER_IN"))
        spent = sum(t.amount for t in txns if t.type.value in ("WITHDRAWAL", "TRANSFER_OUT"))
        for label, value, color in [
            ("Total in", money(deposits), C.GOOD),
            ("Total out", money(spent), C.BAD),
            ("Transactions", str(len(txns)), C.ACCENT),
        ]:
            self._stat_card(stats, label, value, color)

        # quick actions
        actions = tk.Frame(body, bg=C.BG)
        actions.pack(fill="x", pady=6)
        Button(actions, "Deposit", lambda: self._select_nav("Deposit"),
               width=150, icon="\u2193").pack(side="left", padx=(0, 12))
        Button(actions, "Withdraw", lambda: self._select_nav("Withdraw"),
               width=150, fill=C.VIOLET, hover="#7C3AED", fg="white",
               icon="\u2191").pack(side="left", padx=12)
        Button(actions, "Transfer", lambda: self._select_nav("Transfer"),
               width=150, fill=C.BLUE, hover="#2563EB", fg="white",
               icon="\u21C4").pack(side="left", padx=12)

    def _stat_card(self, parent, label, value, color):
        card = Card(parent, 190, 92, fill=C.CARD, stroke=C.STROKE, radius=16)
        card.pack(side="left", padx=(0, 16))
        card.create_text(20, 26, text=label.upper(), fill=C.MUTED,
                         anchor="w", font=self.f["small"])
        card.create_text(20, 58, text=value, fill=color, anchor="w",
                         font=self.f["h2"])

    # ----- Deposit / Withdraw ----------------------------------------- #
    def _page_money(self, kind):
        self._clear_content()
        self._header(kind, f"{kind} money {'into' if kind=='Deposit' else 'from'} "
                           "your account.")
        host = tk.Frame(self.content, bg=C.BG)
        host.pack(padx=36, pady=18, anchor="w")
        card_holder = tk.Frame(host, bg=C.BG)
        card_holder.pack(anchor="w")

        panel = tk.Frame(card_holder, bg=C.CARD)
        panel.pack()
        inner = tk.Frame(panel, bg=C.CARD)
        inner.pack(padx=28, pady=26)
        amount = Field(inner, "Amount", width=24)
        amount.pack(fill="x", pady=6)
        amount.focus()

        def submit():
            try:
                amt = float(amount.get())
                if kind == "Deposit":
                    txn = self.service.deposit(self.current_account,
                                               self.current_pin, amt)
                else:
                    txn = self.service.withdraw(self.current_account,
                                                self.current_pin, amt)
                self.toast(f"{kind} of {money(amt)} successful. "
                           f"Balance: {money(txn.balance_after)}", "success")
                self._select_nav("Overview")
            except (BankError, ValueError) as e:
                self.toast(str(e), "error")

        Button(inner, f"Confirm {kind}", submit, width=260,
               fill=C.ACCENT if kind == "Deposit" else C.VIOLET,
               hover=C.ACCENT_DK if kind == "Deposit" else "#7C3AED",
               fg="#06231F" if kind == "Deposit" else "white").pack(pady=(18, 4))

    # ----- Transfer ---------------------------------------------------- #
    def _page_transfer(self):
        self._clear_content()
        self._header("Transfer", "Send money instantly to another account.")
        host = tk.Frame(self.content, bg=C.BG)
        host.pack(padx=36, pady=18, anchor="w")
        panel = tk.Frame(host, bg=C.CARD)
        panel.pack()
        inner = tk.Frame(panel, bg=C.CARD)
        inner.pack(padx=28, pady=26)
        target = Field(inner, "Recipient account number", width=26)
        target.pack(fill="x", pady=6)
        amount = Field(inner, "Amount", width=26)
        amount.pack(fill="x", pady=6)

        def submit():
            try:
                amt = float(amount.get())
                debit, _ = self.service.transfer(
                    self.current_account, self.current_pin, target.get(), amt)
                self.toast(f"Sent {money(amt)} to {target.get()}. "
                           f"Balance: {money(debit.balance_after)}", "success")
                self._select_nav("Overview")
            except (BankError, ValueError) as e:
                self.toast(str(e), "error")

        Button(inner, "Send money", submit, width=260, fill=C.BLUE,
               hover="#2563EB", fg="white").pack(pady=(18, 4))

    # ----- Statement --------------------------------------------------- #
    def _page_statement(self):
        self._clear_content()
        self._header("Statement", "Your most recent transactions.")
        wrap = tk.Frame(self.content, bg=C.BG)
        wrap.pack(fill="both", expand=True, padx=36, pady=10)

        cols = ("date", "type", "amount", "balance", "note")
        tree = ttk.Treeview(wrap, columns=cols, show="headings",
                            style="Neo.Treeview", height=14)
        headings = {"date": "Date (UTC)", "type": "Type", "amount": "Amount",
                    "balance": "Balance", "note": "Note"}
        widths = {"date": 150, "type": 120, "amount": 110, "balance": 120,
                  "note": 220}
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")

        txns = self.service.get_statement(self.current_account,
                                          self.current_pin, limit=25)
        if not txns:
            tk.Label(wrap, text="No transactions yet.", bg=C.BG, fg=C.MUTED,
                     font=self.f["body"]).pack(pady=40)
            return
        tree.tag_configure("in", foreground=C.GOOD)
        tree.tag_configure("out", foreground=C.BAD)
        for t in txns:
            inflow = t.type.value in ("DEPOSIT", "TRANSFER_IN", "INTEREST")
            sign = "+" if inflow else "-"
            tree.insert("", "end", tags=("in" if inflow else "out"), values=(
                t.timestamp.replace("T", " ")[:19], t.type.value,
                f"{sign}{t.amount:,.2f}", f"{t.balance_after:,.2f}",
                (t.note or "-")[:32]))
        tree.pack(fill="both", expand=True)

    # ----- Settings ---------------------------------------------------- #
    def _page_settings(self):
        self._clear_content()
        self._header("Settings", "Manage your account security.")
        host = tk.Frame(self.content, bg=C.BG)
        host.pack(padx=36, pady=14, anchor="w", fill="x")

        # change pin
        p1 = tk.Frame(host, bg=C.CARD)
        p1.pack(anchor="w", pady=8)
        inner = tk.Frame(p1, bg=C.CARD)
        inner.pack(padx=24, pady=20)
        tk.Label(inner, text="Change PIN", bg=C.CARD, fg=C.TEXT,
                 font=self.f["h2"]).pack(anchor="w", pady=(0, 8))
        newpin = Field(inner, "New PIN (4-6 digits)", show="\u2022", width=24)
        newpin.pack(fill="x", pady=4)

        def change_pin():
            try:
                acc = self._account()
                from ..utils import validate_pin
                validate_pin(newpin.get())
                acc.change_pin(newpin.get())
                self.service._repo.update(acc)
                self.current_pin = newpin.get()
                self.toast("PIN updated successfully", "success")
                newpin.set("")
            except (BankError, ValueError) as e:
                self.toast(str(e), "error")

        Button(inner, "Update PIN", change_pin, width=200).pack(pady=(14, 2))

        # danger zone
        p2 = tk.Frame(host, bg=C.CARD)
        p2.pack(anchor="w", pady=14)
        inner2 = tk.Frame(p2, bg=C.CARD)
        inner2.pack(padx=24, pady=20)
        tk.Label(inner2, text="Close account", bg=C.CARD, fg=C.BAD,
                 font=self.f["h2"]).pack(anchor="w")
        tk.Label(inner2, text="This will permanently deactivate your account.",
                 bg=C.CARD, fg=C.MUTED, font=self.f["small"]).pack(anchor="w",
                                                                   pady=(2, 10))

        def close_account():
            try:
                self.service.close_account(self.current_account, self.current_pin)
                self.toast("Account closed. Signing out...", "info")
                self.after(1200, self._logout)
            except BankError as e:
                self.toast(str(e), "error")

        Button(inner2, "Close my account", close_account, width=200,
               fill=C.BAD, hover="#EF4444", fg="white").pack(pady=2)

    def _logout(self):
        self.current_account = self.current_pin = None
        self.show_welcome()


def launch(service: Optional[BankService] = None):
    """Create and run the NeoBank desktop application."""
    app = NeoBankApp(service)
    app.mainloop()


if __name__ == "__main__":
    launch()
