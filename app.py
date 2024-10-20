from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = 'Shashank'

# Database connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="2005",
        database="supermarket_db1"
    )

# Home page
@app.route('/')
def index():
    return render_template('base.html')

# Add customer
@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['phone']
        phone = request.form['address']

        conn = connect_db()
        cursor = conn.cursor()

        # Check if customer exists based on phone number
        cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
        customer = cursor.fetchone()

        if customer:
            flash("Customer already exists!", "warning")
        else:
            # Insert new customer
            cursor.execute("INSERT INTO customers (name, phone, address) VALUES (%s, %s, %s)", (name, email, phone))
            conn.commit()
            flash("Customer added successfully!", "success")

        cursor.close()
        conn.close()
        return redirect(url_for('add_customer'))

    return render_template('add_customer.html')

# Retrieve customer by phone number
@app.route('/get_customer', methods=['POST'])
def get_customer():
    phone = request.form['phone']

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE phone = %s", (phone,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()

    if customer:
        return {'status': 'success', 'customer': customer}
    else:
        return {'status': 'error', 'message': 'Customer not found'}
# Billing process
# Billing process
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    conn = connect_db()
    cursor = conn.cursor()

    # Fetch customers and products for the initial load
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_ids = request.form.getlist('product_ids')
        quantities = request.form.getlist('quantities')

        total_amount = 0
        bill_items = []

        # Loop through the products selected and calculate total and items
        for i, product_id in enumerate(product_ids):
            quantity = int(quantities[i])
            cursor.execute("SELECT price, quantity FROM products WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()

            if result:
                product_price = result[0]
                stock_quantity = result[1]

                # Ensure there's enough stock before proceeding
                if quantity > stock_quantity:
                    flash(f"Not enough stock for product ID {product_id}. Available: {stock_quantity}", "error")
                    return redirect(url_for('billing'))

                # Calculate item total and accumulate total amount
                item_total = product_price * quantity
                total_amount += item_total
                bill_items.append((product_id, quantity, item_total))

        # Insert new bill into the 'bills' table
        cursor.execute("INSERT INTO bills (customer_id, total_amount) VALUES (%s, %s)", (customer_id, total_amount))
        bill_id = cursor.lastrowid

        # Insert each bill item into 'bill_items' and update stock quantity in 'products'
        for product_id, quantity, item_total in bill_items:
            # Insert into 'bill_items'
            cursor.execute("INSERT INTO bill_items (bill_id, stock_id, quantity, price) VALUES (%s, %s, %s, %s)",
                           (bill_id, product_id, quantity, item_total))

            # Update stock in 'products' by reducing the quantity
            cursor.execute("UPDATE products SET quantity = quantity - %s WHERE product_id = %s", (quantity, product_id))

        # Commit all changes to the database
        conn.commit()

        # Notify the user about successful billing
        flash(f"Bill created successfully! Total: ${total_amount:.2f}", "success")
        return redirect(url_for('billing'))

    # Fetch products to display for selection in the form
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('billing.html', customers=customers, products=products)


# Retrieve product by ID
# Retrieve product by ID
@app.route('/get_product', methods=['POST'])
def get_product():
    data = request.get_json()
    product_id = data['product_id']

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()
    cursor.close()
    conn.close()

    if product:
        return {'status': 'success', 'product': product}  # Return the product details
    else:
        return {'status': 'error', 'message': 'Product not found'}


# View products (formerly stock)
@app.route('/products')
def products():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('products.html', products=products)

# Add product (formerly stock)
@app.route('/new_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])

        conn = connect_db()
        cursor = conn.cursor()

        # Check if the product already exists based on the product name
        cursor.execute("SELECT product_id, quantity FROM products WHERE product_name = %s", (product_name,))
        product = cursor.fetchone()

        if product:
            # If the product exists, only update the quantity and do NOT modify the price
            product_id = product[0]
            existing_quantity = product[1]
            new_quantity = existing_quantity + quantity

            cursor.execute("UPDATE products SET quantity = %s WHERE product_id = %s", (new_quantity, product_id))
            flash(f"Product '{product_name}' already exists. Updated quantity to {new_quantity}.", "success")
        else:
            # If the product does not exist, insert a new product with price and quantity
            cursor.execute("INSERT INTO products (product_name, quantity, price) VALUES (%s, %s, %s)",
                           (product_name, quantity, price))
            flash("Product added to inventory!", "success")

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('add_product'))

    return render_template('new_product.html')

if __name__ == '__main__':
    app.run(debug=True)
