"""
ТехноМаркет — простой магазин техники.
Только стандартная библиотека Python 3.8+ (tkinter + sqlite3).
Запуск:  python main.py
База (shop.db) и картинки (папка images) создаются автоматически.
"""
import os
import shutil
import sqlite3
import struct
import tkinter as tk
import zlib
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog, ttk

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "shop.db")
IMG_DIR = os.path.join(BASE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

CATEGORIES = ["Смартфоны", "Ноутбуки", "Планшеты", "Наушники", "Телевизоры"]

SEED = [
    ("Смартфон Nova X12", "Смартфоны", 49990, 15, "6.7\" AMOLED, 8/256 ГБ, тройная камера 50 Мп."),
    ("Смартфон Pixel Lite", "Смартфоны", 29990, 25, "6.1\" OLED, 6/128 ГБ, быстрая зарядка 33 Вт."),
    ("Смартфон Aero Pro", "Смартфоны", 79990, 8, "Флагман: 12/512 ГБ, камера 108 Мп, 120 Гц."),
    ("Ноутбук ProBook 15", "Ноутбуки", 69990, 10, "15.6\" IPS, Core i5, 16 ГБ ОЗУ, SSD 512 ГБ."),
    ("Ноутбук UltraSlim 14", "Ноутбуки", 89990, 6, "14\" 2.8K, Ryzen 7, 16 ГБ, вес 1.2 кг."),
    ("Игровой ноутбук Titan", "Ноутбуки", 129990, 4, "17\" 165 Гц, RTX 4060, 32 ГБ, SSD 1 ТБ."),
    ("Планшет Tab S10", "Планшеты", 34990, 12, "10.5\" 2K, 8/128 ГБ, стилус в комплекте."),
    ("Планшет Mini 8", "Планшеты", 19990, 20, "8.3\" экран, 4/64 ГБ, лёгкий и компактный."),
    ("Наушники AirBuds", "Наушники", 5990, 40, "Беспроводные, шумоподавление, до 24 ч работы."),
    ("Наушники StudioMax", "Наушники", 12990, 14, "Полноразмерные, Hi-Res звук, Bluetooth 5.3."),
    ("Телевизор Vision 43\"", "Телевизоры", 31990, 9, "43\" 4K UHD, Smart TV, HDR10."),
    ("Телевизор OLED 55\"", "Телевизоры", 99990, 3, "55\" OLED, 120 Гц, Dolby Vision и Atmos."),
]


# ───────────────────────── Генерация картинок (без Pillow) ─────────────────────────
class Pic:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [bytearray(w * 3) for _ in range(h)]

    def rect(self, x0, y0, x1, y1, c):
        x0, x1 = max(0, x0), min(self.w, x1)
        if x1 <= x0:
            return
        chunk = bytes(c) * (x1 - x0)
        for y in range(max(0, y0), min(self.h, y1)):
            self.rows[y][x0 * 3:x1 * 3] = chunk

    def circle(self, cx, cy, r, c):
        for y in range(max(0, cy - r), min(self.h, cy + r + 1)):
            dx = int((r * r - (y - cy) ** 2) ** 0.5)
            self.rect(cx - dx, y, cx + dx + 1, y + 1, c)

    def save(self, path):
        raw = b"".join(b"\x00" + bytes(r) for r in self.rows)

        def chunk(tag, data):
            body = tag + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


PALETTE = [(255, 183, 77), (129, 199, 132), (100, 181, 246), (240, 98, 146),
           (149, 117, 205), (77, 208, 225), (255, 138, 101), (174, 213, 129)]


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_image(path, category, name):
    base = PALETTE[zlib.crc32(name.encode()) % len(PALETTE)]
    W, H = 260, 200
    p = Pic(W, H)
    for y in range(H):
        p.rect(0, y, W, y + 1, mix(base, (255, 255, 255), y / H * 0.6))
    dark, screen = (38, 42, 52), mix(base, (20, 30, 60), 0.35)
    light = (210, 214, 222)
    if category == "Смартфоны":
        p.rect(95, 22, 165, 178, dark)
        p.rect(100, 34, 160, 164, screen)
        p.circle(130, 28, 2, (90, 90, 100))
    elif category == "Ноутбуки":
        p.rect(55, 35, 205, 135, dark)
        p.rect(62, 42, 198, 128, screen)
        p.rect(35, 138, 225, 150, light)
        p.rect(105, 138, 155, 142, (160, 164, 172))
    elif category == "Планшеты":
        p.rect(60, 28, 200, 172, dark)
        p.rect(68, 36, 192, 164, screen)
        p.circle(130, 32, 2, (90, 90, 100))
    elif category == "Наушники":
        p.rect(78, 40, 182, 50, dark)
        p.rect(78, 40, 88, 120, dark)
        p.rect(172, 40, 182, 120, dark)
        p.circle(83, 128, 26, dark)
        p.circle(177, 128, 26, dark)
        p.circle(83, 128, 14, screen)
        p.circle(177, 128, 14, screen)
    else:  # Телевизоры и всё остальное
        p.rect(35, 38, 225, 150, dark)
        p.rect(42, 45, 218, 143, screen)
        p.rect(120, 150, 140, 168, (120, 124, 132))
        p.rect(85, 168, 175, 175, (120, 124, 132))
    p.save(path)


# ───────────────────────── База данных ─────────────────────────
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def image_name(name):
    return "auto_%08x.png" % (zlib.crc32(name.encode()) & 0xFFFFFFFF)


def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL,
            price REAL NOT NULL, stock INTEGER NOT NULL,
            description TEXT DEFAULT '', image TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT, phone TEXT, total REAL, created TEXT);
        CREATE TABLE IF NOT EXISTS order_items(
            order_id INTEGER, product_id INTEGER, name TEXT, qty INTEGER, price REAL);
        """)
        if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            for n, c, pr, st, d in SEED:
                con.execute("INSERT INTO products(name,category,price,stock,description,image) VALUES(?,?,?,?,?,?)",
                            (n, c, pr, st, d, image_name(n)))


def money(v):
    return f"{v:,.0f} ₽".replace(",", " ")


# ───────────────────────── Форма товара ─────────────────────────
class ProductForm(tk.Toplevel):
    def __init__(self, master, on_save, product=None):
        super().__init__(master)
        self.title("Товар")
        self.resizable(False, False)
        self.on_save, self.product = on_save, product
        self.custom_image = None
        self.transient(master)
        self.grab_set()

        p = product
        self.name = tk.StringVar(value=p["name"] if p else "")
        self.cat = tk.StringVar(value=p["category"] if p else CATEGORIES[0])
        self.price = tk.StringVar(value=str(int(p["price"])) if p else "")
        self.stock = tk.StringVar(value=str(p["stock"]) if p else "1")
        self.img_label = tk.StringVar(value="(картинка создастся автоматически)")

        f = ttk.Frame(self, padding=12)
        f.pack()
        for i, (t, w) in enumerate([
            ("Название", ttk.Entry(f, textvariable=self.name, width=40)),
            ("Категория", ttk.Combobox(f, textvariable=self.cat, values=CATEGORIES, width=37)),
            ("Цена, ₽", ttk.Entry(f, textvariable=self.price, width=40)),
            ("В наличии, шт", ttk.Entry(f, textvariable=self.stock, width=40)),
        ]):
            ttk.Label(f, text=t).grid(row=i, column=0, sticky="w", pady=3)
            w.grid(row=i, column=1, pady=3)
        ttk.Label(f, text="Описание").grid(row=4, column=0, sticky="nw", pady=3)
        self.desc = tk.Text(f, width=40, height=5, wrap="word")
        self.desc.grid(row=4, column=1, pady=3)
        if p:
            self.desc.insert("1.0", p["description"] or "")
        ttk.Button(f, text="Выбрать картинку (PNG/GIF)…", command=self.pick).grid(row=5, column=0, pady=6, sticky="w")
        ttk.Label(f, textvariable=self.img_label, foreground="gray").grid(row=5, column=1, sticky="w")
        ttk.Button(f, text="Сохранить", command=self.save).grid(row=6, column=1, sticky="e", pady=8)

    def pick(self):
        path = filedialog.askopenfilename(filetypes=[("Картинки", "*.png *.gif")])
        if path:
            self.custom_image = path
            self.img_label.set(os.path.basename(path))

    def save(self):
        name = self.name.get().strip()
        try:
            price, stock = float(self.price.get().replace(",", ".")), int(self.stock.get())
            assert name and price >= 0 and stock >= 0
        except Exception:
            messagebox.showerror("Ошибка", "Проверьте название, цену и количество.", parent=self)
            return
        cat, desc = self.cat.get().strip() or CATEGORIES[0], self.desc.get("1.0", "end").strip()
        image = self.product["image"] if self.product else image_name(name)
        if self.custom_image:
            image = "user_%d_%s" % (int(datetime.now().timestamp()), os.path.basename(self.custom_image))
            shutil.copy(self.custom_image, os.path.join(IMG_DIR, image))
        elif not self.product or not image.startswith("user_"):
            image = image_name(name)
        with db() as con:
            if self.product:
                con.execute("UPDATE products SET name=?,category=?,price=?,stock=?,description=?,image=? WHERE id=?",
                            (name, cat, price, stock, desc, image, self.product["id"]))
            else:
                con.execute("INSERT INTO products(name,category,price,stock,description,image) VALUES(?,?,?,?,?,?)",
                            (name, cat, price, stock, desc, image))
        self.on_save()
        self.destroy()


# ───────────────────────── Главное окно ─────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ТехноМаркет")
        self.geometry("1020x600")
        self.minsize(860, 520)
        self.cart = {}      # product_id -> qty
        self.photos = {}    # кэш картинок
        self.rows = {}      # iid -> product
        self.admin_win = None
        self.build()
        self.load()

    # --- интерфейс
    def build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="🛒 ТехноМаркет", font=("Arial", 16, "bold")).pack(side="left")
        self.cart_btn = ttk.Button(top, text="Корзина (0)", command=self.open_cart)
        self.cart_btn.pack(side="right")
        ttk.Button(top, text="Управление", command=self.open_admin).pack(side="right", padx=6)

        flt = ttk.Frame(self, padding=(8, 0))
        flt.pack(fill="x")
        self.search = tk.StringVar()
        self.cat_filter = tk.StringVar(value="Все")
        ttk.Label(flt, text="Поиск:").pack(side="left")
        ttk.Entry(flt, textvariable=self.search, width=30).pack(side="left", padx=6)
        self.cat_box = ttk.Combobox(flt, textvariable=self.cat_filter, state="readonly", width=18)
        self.cat_box.pack(side="left")
        self.search.trace_add("write", lambda *_: self.load())
        self.cat_box.bind("<<ComboboxSelected>>", lambda e: self.load())

        body = ttk.Frame(self, padding=8)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        cols = ("name", "cat", "price", "stock")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        for c, t, w in [("name", "Название", 260), ("cat", "Категория", 110), ("price", "Цена", 90), ("stock", "Склад", 60)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="w" if c in ("name", "cat") else "e")
        sb = ttk.Scrollbar(left, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.show_detail)
        self.tree.bind("<Double-1>", lambda e: self.add_to_cart())

        right = ttk.Frame(body, padding=(14, 0), width=300)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self.img_lbl = ttk.Label(right)
        self.img_lbl.pack(pady=4)
        self.d_name = ttk.Label(right, font=("Arial", 13, "bold"), wraplength=280)
        self.d_name.pack(anchor="w")
        self.d_price = ttk.Label(right, font=("Arial", 15), foreground="#2e7d32")
        self.d_price.pack(anchor="w", pady=2)
        self.d_stock = ttk.Label(right, foreground="gray")
        self.d_stock.pack(anchor="w")
        self.d_desc = ttk.Label(right, wraplength=280, justify="left")
        self.d_desc.pack(anchor="w", pady=8)
        self.add_btn = ttk.Button(right, text="В корзину", command=self.add_to_cart, state="disabled")
        self.add_btn.pack(fill="x", pady=6)

    def photo(self, p):
        key = p["image"] or image_name(p["name"])
        if key not in self.photos:
            path = os.path.join(IMG_DIR, key)
            if not os.path.exists(path):
                make_image(path, p["category"], p["name"])
            try:
                img = tk.PhotoImage(file=path)
                k = max(1, -(-img.width() // 260), -(-img.height() // 200))
                if k > 1:
                    img = img.subsample(k)
            except tk.TclError:
                img = tk.PhotoImage(width=1, height=1)
            self.photos[key] = img
        return self.photos[key]

    # --- каталог
    def load(self):
        with db() as con:
            items = con.execute("SELECT * FROM products ORDER BY category, name").fetchall()
        cats = ["Все"] + sorted({r["category"] for r in items})
        self.cat_box["values"] = cats
        if self.cat_filter.get() not in cats:
            self.cat_filter.set("Все")
        q, cat = self.search.get().strip().lower(), self.cat_filter.get()
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for r in items:
            if cat != "Все" and r["category"] != cat:
                continue
            if q and q not in r["name"].lower() and q not in (r["description"] or "").lower():
                continue
            iid = self.tree.insert("", "end", values=(r["name"], r["category"], money(r["price"]), r["stock"]))
            self.rows[iid] = r
        self.show_detail()
        self.cart_btn.config(text=f"Корзина ({sum(self.cart.values())})")

    def current(self):
        sel = self.tree.selection()
        return self.rows.get(sel[0]) if sel else None

    def show_detail(self, _=None):
        p = self.current()
        if not p:
            self.img_lbl.config(image="")
            for l in (self.d_name, self.d_price, self.d_stock, self.d_desc):
                l.config(text="")
            self.add_btn.config(state="disabled")
            return
        self.img_lbl.config(image=self.photo(p))
        self.d_name.config(text=p["name"])
        self.d_price.config(text=money(p["price"]))
        self.d_stock.config(text=f"В наличии: {p['stock']} шт." if p["stock"] else "Нет в наличии")
        self.d_desc.config(text=p["description"] or "")
        self.add_btn.config(state="normal" if p["stock"] else "disabled")

    def add_to_cart(self):
        p = self.current()
        if not p:
            return
        if self.cart.get(p["id"], 0) >= p["stock"]:
            messagebox.showinfo("Корзина", "Больше нет в наличии.")
            return
        self.cart[p["id"]] = self.cart.get(p["id"], 0) + 1
        self.cart_btn.config(text=f"Корзина ({sum(self.cart.values())})")

    # --- корзина
    def open_cart(self):
        win = tk.Toplevel(self)
        win.title("Корзина")
        win.geometry("600x380")
        tree = ttk.Treeview(win, columns=("n", "q", "p", "s"), show="headings", selectmode="browse")
        for c, t, w in [("n", "Товар", 260), ("q", "Кол-во", 70), ("p", "Цена", 100), ("s", "Сумма", 110)]:
            tree.heading(c, text=t)
            tree.column(c, width=w, anchor="w" if c == "n" else "e")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        total_lbl = ttk.Label(win, font=("Arial", 13, "bold"))
        total_lbl.pack(anchor="e", padx=10)
        bar = ttk.Frame(win, padding=8)
        bar.pack(fill="x")

        def items():
            if not self.cart:
                return []
            with db() as con:
                q = ",".join("?" * len(self.cart))
                return con.execute(f"SELECT * FROM products WHERE id IN ({q})", list(self.cart)).fetchall()

        def refresh():
            tree.delete(*tree.get_children())
            total = 0
            for r in items():
                qty = self.cart[r["id"]]
                total += qty * r["price"]
                tree.insert("", "end", iid=str(r["id"]),
                            values=(r["name"], qty, money(r["price"]), money(qty * r["price"])))
            total_lbl.config(text="Итого: " + money(total))
            self.cart_btn.config(text=f"Корзина ({sum(self.cart.values())})")
            return total

        def change(d):
            sel = tree.selection()
            if not sel:
                return
            pid = int(sel[0])
            stock = next(r["stock"] for r in items() if r["id"] == pid)
            new = self.cart[pid] + d
            if new <= 0:
                del self.cart[pid]
            elif new <= stock:
                self.cart[pid] = new
            refresh()

        def remove():
            sel = tree.selection()
            if sel:
                self.cart.pop(int(sel[0]), None)
                refresh()

        def checkout():
            if not self.cart:
                return
            name = simpledialog.askstring("Оформление", "Ваше имя:", parent=win)
            if not name:
                return
            phone = simpledialog.askstring("Оформление", "Телефон:", parent=win)
            if not phone:
                return
            rows = items()
            for r in rows:
                if self.cart[r["id"]] > r["stock"]:
                    messagebox.showerror("Ошибка", f"Недостаточно на складе: {r['name']}", parent=win)
                    return
            total = sum(self.cart[r["id"]] * r["price"] for r in rows)
            with db() as con:
                oid = con.execute("INSERT INTO orders(customer,phone,total,created) VALUES(?,?,?,?)",
                                  (name, phone, total, datetime.now().strftime("%d.%m.%Y %H:%M"))).lastrowid
                for r in rows:
                    q = self.cart[r["id"]]
                    con.execute("INSERT INTO order_items VALUES(?,?,?,?,?)", (oid, r["id"], r["name"], q, r["price"]))
                    con.execute("UPDATE products SET stock=stock-? WHERE id=?", (q, r["id"]))
            self.cart.clear()
            messagebox.showinfo("Готово", f"Заказ №{oid} оформлен!\nСумма: {money(total)}", parent=win)
            win.destroy()
            self.load()

        for t, cmd in [("+", lambda: change(1)), ("−", lambda: change(-1)), ("Удалить", remove)]:
            ttk.Button(bar, text=t, command=cmd, width=8).pack(side="left", padx=2)
        ttk.Button(bar, text="Оформить заказ", command=checkout).pack(side="right")
        refresh()

    # --- управление
    def open_admin(self):
        if self.admin_win and self.admin_win.winfo_exists():
            self.admin_win.lift()
            return
        win = self.admin_win = tk.Toplevel(self)
        win.title("Управление товарами")
        win.geometry("640x420")
        tree = ttk.Treeview(win, columns=("n", "c", "p", "s"), show="headings", selectmode="browse")
        for c, t, w in [("n", "Название", 260), ("c", "Категория", 110), ("p", "Цена", 90), ("s", "Склад", 60)]:
            tree.heading(c, text=t)
            tree.column(c, width=w)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        def refresh():
            tree.delete(*tree.get_children())
            with db() as con:
                for r in con.execute("SELECT * FROM products ORDER BY category, name"):
                    tree.insert("", "end", iid=str(r["id"]), values=(r["name"], r["category"], money(r["price"]), r["stock"]))
            self.load()

        def selected():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("Выбор", "Сначала выберите товар.", parent=win)
                return None
            with db() as con:
                return con.execute("SELECT * FROM products WHERE id=?", (int(sel[0]),)).fetchone()

        def edit():
            p = selected()
            if p:
                ProductForm(win, refresh, p)

        def delete():
            p = selected()
            if p and messagebox.askyesno("Удаление", f"Удалить «{p['name']}»?", parent=win):
                with db() as con:
                    con.execute("DELETE FROM products WHERE id=?", (p["id"],))
                self.cart.pop(p["id"], None)
                refresh()

        def orders():
            ow = tk.Toplevel(win)
            ow.title("Заказы")
            ow.geometry("620x340")
            t = ttk.Treeview(ow, columns=("id", "d", "c", "p", "t"), show="headings")
            for c, h, w in [("id", "№", 40), ("d", "Дата", 120), ("c", "Клиент", 150), ("p", "Телефон", 110), ("t", "Сумма", 100)]:
                t.heading(c, text=h)
                t.column(c, width=w)
            t.pack(fill="both", expand=True, padx=8, pady=8)
            with db() as con:
                for o in con.execute("SELECT * FROM orders ORDER BY id DESC"):
                    t.insert("", "end", iid=str(o["id"]), values=(o["id"], o["created"], o["customer"], o["phone"], money(o["total"])))

            def details(_):
                sel = t.selection()
                if sel:
                    with db() as con:
                        its = con.execute("SELECT * FROM order_items WHERE order_id=?", (int(sel[0]),)).fetchall()
                    messagebox.showinfo(f"Заказ №{sel[0]}", "\n".join(f"{i['name']} × {i['qty']} = {money(i['qty'] * i['price'])}" for i in its), parent=ow)
            t.bind("<Double-1>", details)
            ttk.Label(ow, text="Двойной клик — состав заказа", foreground="gray").pack(pady=(0, 6))

        bar = ttk.Frame(win, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="Добавить", command=lambda: ProductForm(win, refresh)).pack(side="left", padx=2)
        ttk.Button(bar, text="Изменить", command=edit).pack(side="left", padx=2)
        ttk.Button(bar, text="Удалить", command=delete).pack(side="left", padx=2)
        ttk.Button(bar, text="Заказы", command=orders).pack(side="right")
        refresh()


if __name__ == "__main__":
    init_db()
    App().mainloop()
