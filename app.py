import os, json, functools
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, send_from_directory
)
from database import get_db, init_db, get_setting, set_setting
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "cafe-ponte-secret-2024"

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ── helpers ────────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ── kiosk (cliente) ────────────────────────────────────────────────────────────

@app.route("/")
def kiosk():
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()
    store_name = get_setting("store_name") or "Cantina"
    db.close()
    return render_template("kiosk.html", categories=categories, store_name=store_name)


@app.route("/api/products")
def api_products():
    cat_id = request.args.get("category_id", type=int)
    db = get_db()
    if cat_id:
        rows = db.execute(
            "SELECT * FROM products WHERE category_id=? AND active=1 ORDER BY name",
            (cat_id,)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM products WHERE active=1 ORDER BY category_id, name"
        ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/order", methods=["POST"])
def api_place_order():
    data = request.get_json()
    customer = (data.get("customer") or "").strip()
    items = data.get("items", [])

    if not customer:
        return jsonify({"error": "Nome obrigatório"}), 400
    if not items:
        return jsonify({"error": "Carrinho vazio"}), 400

    db = get_db()
    try:
        # verify stock
        for item in items:
            row = db.execute(
                "SELECT quantity FROM products WHERE id=? AND active=1", (item["id"],)
            ).fetchone()
            if not row:
                return jsonify({"error": f"Produto não encontrado: {item['id']}"}), 400
            if row["quantity"] < item["qty"]:
                return jsonify({"error": f"Estoque insuficiente para {item['name']}"}), 400

        total = sum(i["price"] * i["qty"] for i in items)

        cur = db.execute(
            "INSERT INTO orders (customer, total, status, created_at) VALUES (?,?,?,datetime('now','localtime'))",
            (customer, total, "open"),
        )
        order_id = cur.lastrowid

        for item in items:
            db.execute(
                "INSERT INTO order_items (order_id, product_id, name, price, quantity) VALUES (?,?,?,?,?)",
                (order_id, item["id"], item["name"], item["price"], item["qty"]),
            )
            db.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id=?",
                (item["qty"], item["id"]),
            )

        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

    return jsonify({"order_id": order_id, "total": total})


# ── caixa ──────────────────────────────────────────────────────────────────────

@app.route("/caixa")
def cashier():
    store_name = get_setting("store_name") or "Cantina"
    return render_template("cashier.html", store_name=store_name)


@app.route("/api/orders")
def api_orders():
    status = request.args.get("status", "open")
    search = request.args.get("q", "").strip()
    db = get_db()
    if search:
        rows = db.execute(
            "SELECT * FROM orders WHERE status=? AND customer LIKE ? ORDER BY created_at DESC",
            (status, f"%{search}%"),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM orders WHERE status=? ORDER BY created_at DESC",
            (status,),
        ).fetchall()
    result = []
    for r in rows:
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id=?", (r["id"],)
        ).fetchall()
        result.append({**dict(r), "items": [dict(i) for i in items]})
    db.close()
    return jsonify(result)


@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def api_update_order_status(order_id):
    data = request.get_json()
    new_status = data.get("status")
    if new_status not in ("open", "preparing", "completed", "cancelled"):
        return jsonify({"error": "Status inválido"}), 400
    db = get_db()

    # if cancelling, restore stock (from open or preparing)
    if new_status == "cancelled":
        order = db.execute("SELECT status FROM orders WHERE id=?", (order_id,)).fetchone()
        if order and order["status"] in ("open", "preparing"):
            items = db.execute(
                "SELECT product_id, quantity FROM order_items WHERE order_id=?", (order_id,)
            ).fetchall()
            for it in items:
                db.execute(
                    "UPDATE products SET quantity = quantity + ? WHERE id=?",
                    (it["quantity"], it["product_id"]),
                )

    db.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    db.commit()
    db.close()
    return jsonify({"ok": True})


@app.route("/api/orders/<int:order_id>")
def api_get_order(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    items = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    db.close()
    return jsonify({**dict(order), "items": [dict(i) for i in items]})


# ── admin ──────────────────────────────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        pwd = request.form.get("password", "")
        if pwd == get_setting("admin_password"):
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Senha incorreta"
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()
    products = db.execute(
        """SELECT p.*, c.name as cat_name
           FROM products p JOIN categories c ON c.id=p.category_id
           ORDER BY c.id, p.name"""
    ).fetchall()
    orders_today = db.execute(
        "SELECT COUNT(*) as n, SUM(total) as t FROM orders WHERE status IN ('preparing','completed') AND date(created_at)=date('now','localtime')"
    ).fetchone()
    store_name = get_setting("store_name") or "Cantina"
    db.close()
    return render_template(
        "admin.html",
        categories=categories,
        products=products,
        orders_today=orders_today,
        store_name=store_name,
    )


@app.route("/admin/product/add", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form["name"].strip()
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])
    category_id = int(request.form["category_id"])
    image_filename = None

    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_filename = filename

    db = get_db()
    db.execute(
        "INSERT INTO products (category_id, name, price, quantity, image) VALUES (?,?,?,?,?)",
        (category_id, name, price, quantity, image_filename),
    )
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/product/<int:pid>/edit", methods=["POST"])
@admin_required
def admin_edit_product(pid):
    name = request.form["name"].strip()
    price = float(request.form["price"])
    quantity = int(request.form["quantity"])
    active = 1 if request.form.get("active") else 0

    db = get_db()
    prod = db.execute("SELECT image FROM products WHERE id=?", (pid,)).fetchone()
    image_filename = prod["image"] if prod else None

    if "image" in request.files:
        file = request.files["image"]
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_filename = filename

    db.execute(
        "UPDATE products SET name=?, price=?, quantity=?, active=?, image=? WHERE id=?",
        (name, price, quantity, active, image_filename, pid),
    )
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/product/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_delete_product(pid):
    db = get_db()
    db.execute("UPDATE products SET active=0 WHERE id=?", (pid,))
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/settings", methods=["POST"])
@admin_required
def admin_settings():
    store_name = request.form.get("store_name", "").strip()
    new_password = request.form.get("new_password", "").strip()
    if store_name:
        set_setting("store_name", store_name)
    if new_password:
        set_setting("admin_password", new_password)
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/history")
@admin_required
def admin_history():
    db = get_db()
    orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    result = []
    for o in orders:
        items = db.execute("SELECT * FROM order_items WHERE order_id=?", (o["id"],)).fetchall()
        result.append({**dict(o), "items": [dict(i) for i in items]})
    db.close()
    store_name = get_setting("store_name") or "Cantina"
    return render_template("admin_history.html", orders=result, store_name=store_name)


@app.route("/api/print", methods=["POST"])
def api_print():
    """Tenta imprimir na impressora térmica via ESC/POS."""
    data = request.get_json()
    order_id = data.get("order_id")

    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        db.close()
        return jsonify({"error": "Pedido não encontrado"}), 404
    items = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    db.close()

    try:
        from escpos.printer import Usb, Network, Serial
        store_name = get_setting("store_name") or "Cantina"

        # tenta USB genérico (ajuste vendor_id/product_id conforme sua impressora)
        # Exemplo: Elgin i9 = 0x0483 / 0x5740 ; Bematech = 0x0dd4 / 0x0186
        p = Usb(0x0483, 0x5740, timeout=0, in_ep=0x81, out_ep=0x03)
        p.set(align="center", bold=True, height=2, width=2)
        p.text(store_name + "\n")
        p.set(align="center", bold=False, height=1, width=1)
        p.text(f"Pedido #{str(order_id).zfill(4)}\n")
        p.text(f"Cliente: {order['customer']}\n")
        p.text("-" * 32 + "\n")
        p.set(align="left")
        for it in items:
            line = f"{it['quantity']}x {it['name']}"
            price = f"R${(it['price']*it['quantity']):.2f}"
            p.text(f"{line:<22}{price:>10}\n")
        p.text("-" * 32 + "\n")
        p.set(bold=True)
        total = f"R${order['total']:.2f}"
        p.text(f"{'TOTAL':<22}{total:>10}\n")
        p.set(bold=False)
        p.text("\nObrigado! Deus abençoe!\n\n\n")
        p.cut()
        return jsonify({"ok": True, "method": "thermal"})
    except Exception as e:
        # impressora não configurada — frontend usa window.print()
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    init_db()
    print("\n" + "="*50)
    print("  🏪  Cantina da Igreja — iniciando...")
    print("  Kiosk (cliente):  http://localhost:5000")
    print("  Caixa:            http://localhost:5000/caixa")
    print("  Admin:            http://localhost:5000/admin")
    print("  Senha admin:      admin123")
    print("="*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
