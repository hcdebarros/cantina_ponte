# Church Canteen — Order System

A Python/Flask point-of-sale app for church food stands, with a customer kiosk, cashier panel, and admin dashboard.

## First-time setup

1. Run `instalar.bat` to install dependencies (requires Python)
2. Run `iniciar_servidor.bat` to start the server

## URLs

| Screen | URL |
|--------|-----|
| Customer kiosk | http://localhost:5000 |
| Cashier | http://localhost:5000/caixa |
| Admin | http://localhost:5000/admin |

Default admin password: `admin123` — change it in **Admin → Settings**.

## Kiosk mode (customer device)

Run `abrir_kiosk.bat` to open Chrome fullscreen with no close button. Adjust the Chrome path inside the file if needed.

## Cashier on a second device

Open a browser on the second device and go to:

```
http://[SERVER-IP]:5000/caixa
```

To find the server IP: open Command Prompt and run `ipconfig`, then look for **IPv4 Address** (e.g. `192.168.1.100`). Both devices must be on the same Wi-Fi network.

## Order flow

1. Customer uses the kiosk — picks items, adds to cart, enters their name
2. Order appears in the Cashier panel as **Em Aberto**
3. Cashier collects payment → clicks **Em Preparo**
4. Food is prepared → clicks **Concluído**

## Thermal printer

The system attempts to print via ESC/POS automatically. If no thermal printer is found it falls back to the browser's print dialog (`Ctrl+P`). To configure your printer, edit `app.py` and set the correct USB vendor/product ID for your model.

## File structure

```
app.py              # Flask server
database.py         # SQLite database
cafe_ponte.db       # Database file (auto-created)
templates/          # HTML screens
static/images/      # Product photos (uploaded via admin)
requirements.txt    # Python dependencies
```
