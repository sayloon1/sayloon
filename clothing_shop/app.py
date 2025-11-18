from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from functools import wraps
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "minimal_clothing_secret_2025"
DATABASE = 'clothing.db'



def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database with user and sales tables."""

    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            );
        """)


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price_per_item REAL NOT NULL,
                sale_date TEXT NOT NULL,
                revenue REAL NOT NULL 
            );
        """)


        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'password123'))

        conn.commit()
        conn.close()



init_db()



def load_user(username):
    """Loads a user's details from the database."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user


def save_user(username, password):
    """Saves a new user to the database."""
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in to access the Clothing Sales Tracker.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function



BASE_CSS = """
<style>
    :root {
        --primary-color: #333333; /* Dark Charcoal */
        --secondary-color: #6c757d; /* Muted Grey */
        --success-color: #28a745;
        --danger-color: #dc3545;
        --bg-light: #f4f4f4; /* Very Light Grey Background */
        --bg-white: #ffffff;
    }
    body { font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: var(--bg-light); color: var(--primary-color); }
    .container { max-width: 800px; margin: 50px auto; padding: 30px; border-radius: 8px; background-color: var(--bg-white); box-shadow: 0 4px 8px rgba(0,0,0,0.05); }
    h1, h2 { color: var(--primary-color); border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; font-weight: 300; }
    h1 { font-size: 2em; }
    h2 { font-size: 1.5em; }

    /* Forms and Inputs */
    input[type="text"], input[type="number"], input[type="date"], input[type="password"] { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; transition: border-color 0.3s; font-size: 0.9em; }
    input[type="text"]:focus, input[type="number"]:focus, input[type="date"]:focus, input[type="password"]:focus { border-color: var(--primary-color); outline: none; }

    /* Buttons */
    input[type="submit"], .btn { background-color: var(--primary-color); color: var(--bg-white); padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin-top: 10px; font-weight: 400; transition: background-color 0.3s, opacity 0.3s; }
    input[type="submit"]:hover, .btn:hover { background-color: #555555; opacity: 0.9; }
    .btn-danger { background-color: var(--danger-color); color: white; }
    .btn-danger:hover { background-color: #c82333; }
    .btn-secondary { background-color: var(--secondary-color); color: white; }
    .btn-secondary:hover { background-color: #5a6268; }


    /* Messages */
    .message { padding: 10px 15px; margin-bottom: 15px; border-radius: 4px; font-weight: 500; border: 1px solid; }
    .success { background-color: #d4edda; color: #155724; border-color: var(--success-color); }
    .danger { background-color: #f8d7da; color: #721c24; border-color: var(--danger-color); }
    .info { background-color: #cce5ff; color: #004085; border-color: #007bff; }
    .warning { background-color: #fff3cd; color: #856404; border-color: #ffc107; }

    /* Table Styling */
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }
    th { background-color: var(--bg-light); color: var(--primary-color); font-weight: 500; text-transform: uppercase; font-size: 0.8em; }
    tr:nth-child(even) { background-color: #fafafa; }
    tr:hover { background-color: #f0f0f0; }

    /* Totals Box */
    .total-box { margin-top: 25px; padding: 20px; background-color: var(--bg-light); border: 1px solid #ddd; border-radius: 4px; text-align: center; }
    .total-box p { margin: 0; font-size: 1.1em; font-weight: 400; color: var(--primary-color); }

    /* Layout for adding sale */
    .add-batch-form { display: grid; grid-template-columns: 2fr 1fr 1fr 1.5fr auto; gap: 10px; align-items: end; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 400; font-size: 0.9em; }
    .form-group input { margin: 0; }
</style>
"""

LOGIN_TEMPLATE = BASE_CSS + """
<div class="container">
    <h2>👔 Minimalist Clothing Sales Tracker 👖</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="message {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    <form method="POST">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required>
        <label for="password">Password:</label>
        <input type="password" id="password" name="password" required>
        <input type="submit" value="Log In">
    </form>
    <p style="margin-top: 20px; font-size: 0.9em;">Don't have an account? <a href="{{ url_for('register') }}" style="color: var(--primary-color);">Register here</a>.</p>
</div>
"""

REGISTER_TEMPLATE = BASE_CSS + """
<div class="container">
    <h2>Register New Account</h2>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="message {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    <form method="POST">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required>
        <label for="password">Password (min 4 chars):</label>
        <input type="password" id="password" name="password" required>
        <input type="submit" value="Register">
    </form>
    <p style="margin-top: 20px; font-size: 0.9em;">Already have an account? <a href="{{ url_for('login') }}" style="color: var(--primary-color);">Login here</a>.</p>
</div>
"""

# MODIFIED: Sales Tracker Dashboard
SALES_TRACKER_TEMPLATE = BASE_CSS + """
<div class="container">
    <h1>👕 Clothing Sales Dashboard</h1>
    <p style="text-align: right; font-size: 0.9em;"><a href="{{ url_for('logout') }}" class="btn btn-danger">Logout ({{ session.username }})</a></p>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="message {{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <h2>Record New Sale</h2>
    <form method="POST" class="add-batch-form">
        <div class="form-group">
            <label for="item_name">Item Name</label>
            <input type="text" id="item_name" name="item_name" required placeholder="e.g., Slim Fit Jeans">
        </div>
        <div class="form-group">
            <label for="quantity">Quantity (Units)</label>
            <input type="number" id="quantity" name="quantity" required step="1" min="1" placeholder="e.g., 5">
        </div>
        <div class="form-group">
            <label for="price_per_item">Price Per Item ($)</label>
            <input type="number" id="price_per_item" name="price_per_item" required step="0.01" min="0.01" placeholder="e.g., 49.99">
        </div>
        <div class="form-group">
            <label for="date">Date</label>
            <input type="date" id="date" name="date" required value="{{ today }}">
        </div>
        <input type="submit" value="Record Sale">
    </form>

    <div class="total-box">
        <p>Total Revenue Recorded: <strong>${{ "{:,.2f}".format(total_revenue) }}</strong></p>
        <p>Total Items Sold: <strong>{{ "{:,.0f}".format(total_quantity) }}</strong></p>
    </div>

    <h2 style="margin-top: 40px;">Sales History</h2>
    <p>
        <a href="{{ url_for('sales_history') }}" class="btn btn-secondary">
            View Detailed Sales History
        </a>
    </p>
</div>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const dateInput = document.getElementById('date');
        if (!dateInput.value) {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            dateInput.value = `${year}-${month}-${day}`;
        }
    });
</script>
"""

# NEW: Sales History Template
HISTORY_CONTENT = """
<div class="container">
    <h1 style="color: var(--primary-color);">📈 Sales History</h1>
    <p><a href="{{ url_for('sales_tracker') }}" class="btn btn-secondary" style="background-color: #5a6268;">← Back to Dashboard</a></p>

    {% if batches %}
        <table>
            <thead>
                <tr>
                    <th>Item Name</th>
                    <th>Date</th>
                    <th>Quantity</th>
                    <th>Price/Item</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody>
                {% for batch in batches %}
                    <tr>
                        <td>{{ batch.item_name }}</td>
                        <td>{{ batch.sale_date }}</td>
                        <td>{{ "{:,.0f}".format(batch.quantity) }}</td>
                        <td>${{ "{:,.2f}".format(batch.price_per_item) }}</td>
                        <td><strong>${{ "{:,.2f}".format(batch.revenue) }}</strong></td>
                    </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <p>No sales recorded yet. Please add entries via the dashboard.</p>
    {% endif %}
</div>
"""
HISTORY_TEMPLATE = BASE_CSS + HISTORY_CONTENT


# === FLASK ROUTES ===

@app.route("/", methods=["GET", "POST"])
@login_required
def sales_tracker():
    """Main Clothing Sales Tracker app route."""
    conn = get_db_connection()

    if request.method == "POST":
        item_name = request.form.get('item_name')
        quantity_str = request.form.get('quantity')
        price_str = request.form.get('price_per_item')
        date = request.form.get('date')

        try:
            quantity = int(quantity_str)
            price_per_item = float(price_str)

            if quantity <= 0:
                raise ValueError("Quantity must be a positive whole number.")
            if price_per_item <= 0:
                raise ValueError("Price per item must be positive.")

            # Validate date format
            datetime.strptime(date, '%Y-%m-%d')

            revenue = quantity * price_per_item

            # Insert into database - uses the 'revenue' column
            conn.execute(
                'INSERT INTO sales (item_name, quantity, price_per_item, sale_date, revenue) VALUES (?, ?, ?, ?, ?)',
                (item_name.strip(), quantity, price_per_item, date, revenue)
            )
            conn.commit()

            flash(f"Sale of {quantity} x {item_name} recorded! Revenue: ${revenue:,.2f}", "success")

        except ValueError as e:
            flash(f"Invalid input: {e}", "danger")

        except Exception:
            flash("Invalid input. Please check all fields (quantity must be a whole number, price/item a number).",
                  "danger")

        finally:
            conn.close()
            return redirect(url_for('sales_tracker'))

    # Calculate totals for GET request - queries the 'revenue' column
    try:
        total_data = conn.execute(
            'SELECT SUM(revenue) as total_revenue, SUM(quantity) as total_quantity FROM sales'
        ).fetchone()

        total_revenue = total_data['total_revenue'] if total_data['total_revenue'] is not None else 0.0
        total_quantity = total_data['total_quantity'] if total_data['total_quantity'] is not None else 0.0

    finally:
        conn.close()

    today_date = datetime.now().strftime('%Y-%m-%d')

    return render_template_string(
        SALES_TRACKER_TEMPLATE,
        total_revenue=total_revenue,
        total_quantity=total_quantity,
        today=today_date
    )


@app.route("/history")
@login_required
def sales_history():
    """Display the detailed sales history in a separate view."""
    conn = get_db_connection()
    try:
        # Fetch all sales, ordered by date descending - queries the 'revenue' column
        batches = conn.execute('SELECT * FROM sales ORDER BY sale_date DESC, id DESC').fetchall()
    finally:
        conn.close()

    # Convert to a list of dictionaries for easier template rendering
    sales_list = [dict(batch) for batch in batches] if batches else []

    return render_template_string(
        HISTORY_TEMPLATE,
        batches=sales_list
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page."""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        user = load_user(username)

        if user and user['password'] == password:
            session["logged_in"] = True
            session["username"] = username
            flash(f"Welcome back, {username}! Redirecting to Clothing Sales Tracker.", "success")
            return redirect(url_for("sales_tracker"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template_string(LOGIN_TEMPLATE)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Registration page."""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if load_user(username):
            flash("Username already exists. Please choose another.", "danger")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "danger")
        else:
            if save_user(username, password):
                flash("Account created successfully! You can now log in.", "success")
                return redirect(url_for("login"))
            else:
                flash("An unexpected error occurred during registration.", "danger")

    return render_template_string(REGISTER_TEMPLATE)


@app.route("/logout")
def logout():
    """Logs the user out."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# === RUN APP ===
if __name__ == "__main__":
    app.run(debug=True)