# MIT License  -  Copyright (c) 2025 Vincenzo Natale

# Import necessary libraries
from flask import Flask, request, render_template_string, session, jsonify, flash, g, redirect, url_for
import pandas as pd
from datetime import datetime
import logging
import os
import sqlite3

# Initialize the Flask application
app = Flask(__name__)

# Set a secret key for session management
app.secret_key = os.getenv('SECRET_KEY', '9e9b5f8e7a2c4d1e6f8a9b0c3d2eff4')

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database configuration
DATABASE = 'likes.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                user_id TEXT PRIMARY KEY,
                likes INTEGER DEFAULT 0
            )
        ''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize the database
init_db()

# Define the HTML template for the web application
html_template = """

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Application para el Cálculo de los Intereses Compensatorios o Resarcitorios (no incluye Intereses Punitorios), para el Impuesto sobre los Ingresos Brutos de la CABA, AGIP - by Vincenzo Natale">
    <title>Web Application para el Cálculo de los Intereses Compensatorios o Resarcitorios</title>
    <style>
        /* General Styles */
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #f4f4f9, #e0e0e7); /* New gradient background */
            color: #333;
            margin: 0;
            padding: 0;
            line-height: 1.2;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        h1, h2 {
            color: #2c3e50;
            text-align: center;
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }

        h2 {
            font-size: 2rem;
            margin-top: 30px;
            margin-bottom: 10px;
        }

        p {
            font-size: 1.1rem;
            margin-bottom: 10px;
            text-align: center;
        }

        /* Form Styles */
        form {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 10px;
        }

        label {
            display: block;
            font-weight: bold;
            margin-bottom: 10px;
            color: #34495e;
        }

        input[type="date"],
        input[type="file"] {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }

        button[type="submit"] {
            background-color: #3498db;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button[type="submit"]:hover {
            background-color: #2980b9;
        }

        /* Table Styles */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            background-color: #fff;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        th, td {
            padding: 4px; /* Very compact padding */
            text-align: right;
            border: 1px solid #ddd;
            font-size: 0.8rem; /* Smaller font size */
            line-height: 1.1; /* Tighter line height */
        }

        th {
            background-color: #3498db;
            color: #fff;
            font-weight: bold;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr:hover {
            background-color: #f1f1f1;
        }
          


        /* File Status Messages */
        #tasa_file_status, #deuda_file_status {
            font-size: 0.9rem;
            color: #27ae60;
            margin-top: 10px;
        }

        /* Footer Styles */
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            background-color: #2c3e50;
            color: #fff;
            border-radius: 8px;
        }

        .footer a {
            color: #3498db;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        /* Like Button Styles */
        #likes {
            font-size: 1.2rem;
            color: #3498db;
            margin-top: 20px;
        }

        button#likeButton {
            background-color: #9874ff ;  
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        button#likeButton:hover {
            background-color: #c0392b;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Web Application para el Cálculo de los Intereses Compensatorios o Resarcitorios</h1>
        <p>Herramientas utilizadas: HTML, Python (librerías Flask y Pandas), Render Web Hosting, IA ChatGPT y DeepSeek.</p>

        <!-- Step 1: Set Calculation Date -->
        <div>
            <h2>Paso 1: Ingresa la Fecha hasta la cual (inclusive) los intereses serán calculados.</h2>
            <form action="/set_date" method="post">
                <label for="calc_date">Fecha de Cálculo:</label>
                <input type="date" name="calc_date" required>
                <button type="submit">Establecer Fecha de Cálculo</button>
            </form>
        </div>

        <!-- Step 2: Upload Tasa File -->
        <div>
            <h2>Paso 2: Carga el archivo Tasas.xlsx</h2>
            <p>Los títulos de las 3 columnas y su formato, por ejemplo, deben ser : F_Desde 01-01-2025   ,  F_Hasta_Inc. 30-06-2025  ,  Tasa 0,035700
.</p>
            <form action="/upload_tasa" method="post" enctype="multipart/form-data">
                <input type="file" name="tasa_file" accept=".xlsx" required>
                <button type="submit">Cargar Archivo</button>
            </form>
            <p id="tasa_file_status">{{ tasa_file_status }}</p>
        </div>

        <!-- Step 3: Upload Deuda File -->
        <div>
            <h2>Paso 3: Carga el archivo Deuda.xlsx</h2>
            <p>Los títulos de las 3 columnas y su formato, por ejemplo, deben ser : Mes y Año 01-11-2022  ,  Fecha_Vto 16-12-2022  ,  Importe_Deuda 2845086,27  (sin puntos y con coma para decimales)
.</p>
            <form action="/process" method="post" enctype="multipart/form-data">
                <input type="file" name="excel_file" accept=".xlsx" required>
                <button type="submit">Cargar Archivo</button>
            </form>
            <p id="deuda_file_status">{{ deuda_file_status }}</p>
        </div>

        <!-- Calculation Results -->
        {% if data %}
            <h2>Cálculo realizado: Valor nominal de la deuda, Intereses compensatorios y Deuda actualizada</h2>
            <h2>Fecha de Cálculo, inclusive: {{ calc_date }}</h2>
            <table>
                <tr>
                    <th>Mes y Año</th>
                    <th>Fecha_Vto</th>
                    <th>Importe_Deuda</th>
                    {% for column in extra_columns %}
                    <th>{{ column }}</th>
                    {% endfor %}
                    <th>Importe_Intereses</th>
                    <th>Deuda_Actualizada</th>
                </tr>
                {% for row in data %}
                <tr>
                    <td>{{ row['Mes y Año'] }}</td>
                    <td>{{ row['Fecha_Vto'] }}</td>
                    <td>{{ row['Importe_Deuda'] }}</td>
                    {% for column in extra_columns %}
                    <td>{{ row[column] }}</td>
                    {% endfor %}
                    <td>{{ row['Importe_Intereses'] }}</td>
                    <td>{{ row['Deuda_Actualizada'] }}</td>
                </tr>
                {% endfor %}
            </table>

            <h2>Subtotales por Año</h2>
            <table>
                <tr>
                    <th>Año</th>
                    <th>Subtotal Importe_Deuda</th>
                    <th>Subtotal Importe_Intereses</th>
                    <th>Subtotal Deuda_Actualizada</th>
                </tr>
                {% for row in subtotals %}
                <tr>
                    <td>{{ row['Año'] }}</td>
                    <td>{{ row['Subtotal_Importe_Deuda'] }}</td>
                    <td>{{ row['Subtotal_Importe_Intereses'] }}</td>
                    <td>{{ row['Subtotal_Deuda_Actualizada'] }}</td>
                </tr>
                {% endfor %}
            </table>

            <h2>Total General</h2>
            <table>
                <tr>
                    <th>Total Importe_Deuda</th>
                    <th>Total Importe_Intereses</th>
                    <th>Total Deuda_Actualizada</th>
                </tr>
                <tr>
                    <td>{{ totals['Total_Importe_Deuda'] }}</td>
                    <td>{{ totals['Total_Importe_Intereses'] }}</td>
                    <td>{{ totals['Total_Deuda_Actualizada'] }}</td>
                </tr>
            </table>
        {% endif %}

        <!-- Tasa Data Display -->
        {% if tasa_data %}
            <h2>Datos del Archivo Tasas.xlsx (tasa expresada en tanto por uno)</h2>
            <table>
                <tr>
                    <th>F_Desde</th>
                    <th>F_Hasta_Inc.</th>
                    <th>Tasa</th>
                </tr>
                {% for row in tasa_data %}
                <tr>
                    <td>{{ row['F_Desde'] }}</td>
                    <td>{{ row['F_Hasta_Inc'] }}</td>
                    <td>{{ row['Tasa'] }}</td>
                </tr>
                {% endfor %}
            </table>
        {% endif %}

        <!-- Like Button -->
        <div>
            <button id="likeButton" onclick="sendLike()">If this app has been useful to you, then I deserve a Like ❤️</button>
            <p id="likes">Likes: {{ likes }}</p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Contacto: <a href="mailto:vnatale52@gmail.com">Enviar un correo electrónico a Vincenzo Natale: vnatale52@gmail.com</a></p>
            <p>MIT License - Copyright (c) 2025 Vincenzo Natale</p>
        </div>
    </div>

    <script>
        function sendLike() {
            fetch('/like', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('likes').innerText = 'Likes: ' + data.likes;
                });
        }

        // Update file selection status for Tasas.xlsx
        document.querySelector('input[name="tasa_file"]').addEventListener('change', function () {
            document.getElementById('tasa_file_status').innerText = 'A file has been selected.';
        });

        // Update file selection status for Deuda.xlsx
        document.querySelector('input[name="excel_file"]').addEventListener('change', function () {
            document.getElementById('deuda_file_status').innerText = 'A file has been selected.';
        });
    </script>
</body>
</html>
"""

# Helper function to format numbers
def format_number(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

# Helper function to validate DataFrame columns
def validate_dataframe(df, required_columns):
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")

# Global variables to store uploaded tasa data and calculation date
uploaded_tasa = None
calc_date_global = None

# Route for the home page
@app.route("/", methods=["GET"])
def home():
    user_id = session.get('user_id', 'default_user')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT likes FROM likes WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    likes = result[0] if result else 0

    # Retrieve calculation results from the session
    data = session.pop('data', None)
    extra_columns = session.pop('extra_columns', None)
    subtotals = session.pop('subtotals', None)
    totals = session.pop('totals', None)
    calc_date = session.pop('calc_date', None)

    # File selection status
    tasa_file_status = session.pop('tasa_file_status', ' ')     # colocado ' '  en lugar de "File selected"
    deuda_file_status = session.pop('deuda_file_status', ' ')   # colocado ' '  en lugar de "File selected"

    return render_template_string(
        html_template,
        likes=likes,
        data=data,
        extra_columns=extra_columns,
        subtotals=subtotals,
        totals=totals,
        calc_date=calc_date,
        tasa_file_status=tasa_file_status,
        deuda_file_status=deuda_file_status
    )

# Route to handle file upload for tasa data
@app.route("/upload_tasa", methods=["POST"])
def upload_tasa_file():
    global uploaded_tasa
    file = request.files["tasa_file"]
    if not file:
        flash("No se subió ningún archivo.", "error")
        return redirect(url_for('home'))  # Redirect to home if no file is uploaded

    try:
        df_tasa = pd.read_excel(file)
        df_tasa.columns = df_tasa.columns.str.strip()
        required_columns = ["F_Desde", "F_Hasta_Inc.", "Tasa"]
        validate_dataframe(df_tasa, required_columns)

        df_tasa["F_Desde"] = pd.to_datetime(df_tasa["F_Desde"], format="%d-%m-%Y", errors="coerce")
        df_tasa["F_Hasta_Inc."] = pd.to_datetime(df_tasa["F_Hasta_Inc."], format="%d-%m-%Y", errors="coerce")

        uploaded_tasa = df_tasa
        flash("Archivo de tasas cargado exitosamente.", "success")
        session['tasa_file_status'] = 'A file has been selected.'  # Update file selection status
        return redirect(url_for('home'))  # Redirect to home after successful upload
    except Exception as e:
        logging.error(f"Error processing tasa file: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}", "error")
        return redirect(url_for('home'))  # Redirect to home if there's an error

# Route to set the calculation date
@app.route("/set_date", methods=["POST"])
def set_date():
    global calc_date_global
    calc_date = request.form.get("calc_date")
    if not calc_date:
        flash("No se proporcionó ninguna fecha.", "error")
        return redirect(url_for('home'))  # Redirect to home if no date is provided

    try:
        calc_date_global = datetime.strptime(calc_date, "%Y-%m-%d")
        flash(f"Fecha de cálculo establecida: {calc_date_global.strftime('%d-%m-%Y')}", "success")
        return redirect(url_for('home'))  # Redirect to home after setting the date
    except ValueError:
        flash("Formato de fecha no válido.", "error")
        return redirect(url_for('home'))  # Redirect to home if the date format is invalid

# Route to process the uploaded debt file
@app.route("/process", methods=["POST"])
def process_file():
    global uploaded_tasa, calc_date_global
    file = request.files["excel_file"]

    if not file:
        flash("No se cargó ningún archivo.", "error")
        return redirect(url_for('home'))  # Redirect to home if no file is uploaded

    if uploaded_tasa is None:
        flash("No se ha cargado el archivo Tasa.xlsx.", "error")
        return redirect(url_for('home'))  # Redirect to home if tasa file is not uploaded

    if calc_date_global is None:
        flash("No se ha establecido la fecha de cálculo.", "error")
        return redirect(url_for('home'))  # Redirect to home if calculation date is not set

    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        required_columns = ["Mes y Año", "Fecha_Vto", "Importe_Deuda"]
        validate_dataframe(df, required_columns)

        df["Fecha_Vto"] = pd.to_datetime(df["Fecha_Vto"], format="%d-%m-%Y", errors="coerce")
        if df["Fecha_Vto"].isnull().any():
            flash("Algunas fechas de vencimiento no son válidas o están ausentes.", "error")
            return redirect(url_for('home'))  # Redirect to home if there are invalid dates

        def calcular_dias_transcurridos(row, tasa_row):
            f_desde = tasa_row["F_Desde"]
            f_hasta = tasa_row["F_Hasta_Inc."]
            vencimiento = row["Fecha_Vto"]

            if pd.isnull(vencimiento) or pd.isnull(f_desde) or pd.isnull(f_hasta):
                return None

            dias_transcurridos = (min(calc_date_global, f_hasta) - max(vencimiento, f_desde)).days + 1
            return max(0, dias_transcurridos)

        extra_columns = []
        coef_acumulado_col = 'Coef_Acumulado'

        for _, tasa_row in uploaded_tasa.iterrows():
            tasa_name = f"Cant_Días ({tasa_row['Tasa']})"
            extra_columns.append(tasa_name)
            df[tasa_name] = df.apply(lambda row: calcular_dias_transcurridos(row, tasa_row), axis=1)

        df[coef_acumulado_col] = 0
        for i in range(len(df)):
            for tasa_row in uploaded_tasa.itertuples():
                tasa_name = f"Cant_Días ({tasa_row.Tasa})"
                if not pd.isna(df.at[i, tasa_name]):
                    df.at[i, coef_acumulado_col] += (df.at[i, tasa_name] * tasa_row.Tasa) / 30

        if coef_acumulado_col not in extra_columns:
            extra_columns.append(coef_acumulado_col)

        df["Importe_Intereses"] = (df["Importe_Deuda"] * df[coef_acumulado_col]).round(2)
        df["Deuda_Actualizada"] = (df["Importe_Deuda"] + df["Importe_Intereses"]).round(2)

        df["Importe_Deuda"] = df["Importe_Deuda"].apply(format_number)
        df["Importe_Intereses"] = df["Importe_Intereses"].apply(format_number)
        df["Deuda_Actualizada"] = df["Deuda_Actualizada"].apply(format_number)
        df[coef_acumulado_col] = df[coef_acumulado_col].apply(lambda x: "{:,.8f}".format(x).replace(".", ","))

        df["Año"] = pd.to_datetime(df["Mes y Año"], format="%m-%Y", errors="coerce").dt.year
        subtotals = df.groupby("Año").agg(
            Subtotal_Importe_Deuda=("Importe_Deuda", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Importe_Intereses=("Importe_Intereses", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Deuda_Actualizada=("Deuda_Actualizada", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x))
        ).reset_index()

        subtotals["Subtotal_Importe_Deuda"] = subtotals["Subtotal_Importe_Deuda"].apply(format_number)
        subtotals["Subtotal_Importe_Intereses"] = subtotals["Subtotal_Importe_Intereses"].apply(format_number)
        subtotals["Subtotal_Deuda_Actualizada"] = subtotals["Subtotal_Deuda_Actualizada"].apply(format_number)

        totals = {
            "Total_Importe_Deuda": format_number(df["Importe_Deuda"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()),
            "Total_Importe_Intereses": format_number(df["Importe_Intereses"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()),
            "Total_Deuda_Actualizada": format_number(df["Deuda_Actualizada"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum())
        }

        df["Mes y Año"] = pd.to_datetime(df["Mes y Año"], errors="coerce").dt.strftime("%m-%Y")
        df["Fecha_Vto"] = df["Fecha_Vto"].dt.strftime("%d-%m-%Y")

        # Store the results in the session
        session['data'] = df.to_dict(orient="records")
        session['extra_columns'] = extra_columns
        session['subtotals'] = subtotals.to_dict(orient="records")
        session['totals'] = totals
        session['calc_date'] = calc_date_global.strftime("%d-%m-%Y")
        session['deuda_file_status'] = 'A file has been selected.'  # Update file selection status

        flash("Cálculo realizado exitosamente.", "success")
        return redirect(url_for('home'))  # Redirect to home after successful processing
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}", "error")
        return redirect(url_for('home'))  # Redirect to home if there's an error

# Route to handle likes
@app.route("/like", methods=["POST"])
def like():
    user_id = session.get('user_id', 'default_user')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT OR IGNORE INTO likes (user_id, likes) VALUES (?, 0)', (user_id,))
    cursor.execute('UPDATE likes SET likes = likes + 1 WHERE user_id = ?', (user_id,))
    db.commit()
    cursor.execute('SELECT likes FROM likes WHERE user_id = ?', (user_id,))
    likes = cursor.fetchone()[0]
    return jsonify({"likes": likes})

# Run the application
if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true')
