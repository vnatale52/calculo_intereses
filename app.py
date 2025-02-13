#  MIT License  -  Copyright (c) 2025 Vincenzo Natale

# Import necessary libraries
from flask import Flask, request, render_template_string, session, jsonify, flash, g
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
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="Application para el Cálculo de los Intereses Compensatorios o Resarcitorios para el Impuesto sobre los Ingresos Brutos de la CABA, AGIP - by Vincenzo Natale" />

    <title>Web Application para el Cálculo de los Intereses Compensatorios o Resarcitorios</title>
    <h1>Web Application para el Cálculo de Intereses Compensatorios - Versión en Desarrollo desde el 26-01-2025, by VN.</h1>
    <p>Herramientas utilizadas: HTML, Python (librerías Flask y Pandas), Render Web Hosting (que tarda varios segundos en correr), IA ChatGPT y DeepSeek. </p>
    <p>En caso de reproceso, asegurarse que la URL sea sólo https://calculo-intereses.onrender.com (sin ninguna subruta a continuación de .com , de lo contrario, dará un error)</p>
</head>
<body style="background-color: powderblue;">
    <h1>Paso 1: Ingresa la Fecha hasta la cual (inclusive) los intereses serán calculados.</h1>
    <form action="/set_date" method="post">
        <label for="calc_date">Fecha de Cálculo:</label>
        <input type="date" name="calc_date" required>
        <br><br>
        <button type="submit">Establecer Fecha de Cálculo</button>
    </form>

    <h1>Paso 2: Carga el archivo Tasas.xlsx. Los Títulos de las 3 columnas deben ser: F_Desde, F_Hasta_Inc., Tasa.</h1>
    <p>Las fechas deben estar en el formato dd-mm-yyyy y la tasa nominal mensual debe estar expresada en tanto por uno, para 30 días de plazo; el denominador utilizado es siempre 30 días y no hay capitalización de intereses.</p>
    <form action="/upload_tasa" method="post" enctype="multipart/form-data">
        <input type="file" name="tasa_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

    <h1>Paso 3: Carga el archivo Deuda.xlsx. Los Títulos de las 3 columnas deben ser: Mes y Año, Fecha_Vto, Importe_Deuda.</h1>
    <p>La columna "Mes y Año" debe estar en el formato mm-yyyy, "Fecha_Vto" en formato dd-mm-yyyy y la coma debe ser el separador decimal.</p>
    <form action="/process" method="post" enctype="multipart/form-data">
        <input type="file" name="excel_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

    {% if data %}
        <h2>Cálculo realizado:  Valor nominal de la deuda, Intereses compensatorios calculados y Deuda actualizada:</h2>
        <h2>Fecha de Cálculo, inclusive : {{ calc_date }}</h2>
        <p>Mediante un simple "Copy and Paste" se puede exportar su contenido a una WorkSheet. También, se puede generar una salida a PDF para su impresión.</p>
        <table border="1">
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
                <td style="text-align: right;">{{ row['Mes y Año'] }}</td>
                <td style="text-align: right;">{{ row['Fecha_Vto'] }}</td>
                <td style="text-align: right;">{{ row['Importe_Deuda'] }}</td>
                {% for column in extra_columns %}
                <td style="text-align: right;">{{ row[column] }}</td>
                {% endfor %}
                <td style="text-align: right;">{{ row['Importe_Intereses'] }}</td>
                <td style="text-align: right;">{{ row['Deuda_Actualizada'] }}</td>
            </tr>
            {% endfor %}
        </table>

        <h2>Subtotales por Año</h2>
        <table border="1">
            <tr>
                <th>Año</th>
                <th>Subtotal Importe_Deuda</th>
                <th>Subtotal Importe_Intereses</th>
                <th>Subtotal Deuda_Actualizada</th>
            </tr>
            {% for row in subtotals %}
            <tr>
                <td style="text-align: right;">{{ row['Año'] }}</td>
                <td style="text-align: right;">{{ row['Subtotal_Importe_Deuda'] }}</td>
                <td style="text-align: right;">{{ row['Subtotal_Importe_Intereses'] }}</td>
                <td style="text-align: right;">{{ row['Subtotal_Deuda_Actualizada'] }}</td>
            </tr>
            {% endfor %}
        </table>

        <h2>Total General</h2>
        <table border="1">
            <tr>
                <th>Total Importe_Deuda</th>
                <th>Total Importe_Intereses</th>
                <th>Total Deuda_Actualizada</th>
            </tr>
            <tr>
                <td style="text-align: right;">{{ totals['Total_Importe_Deuda'] }}</td>
                <td style="text-align: right;">{{ totals['Total_Importe_Intereses'] }}</td>
                <td style="text-align: right;">{{ totals['Total_Deuda_Actualizada'] }}</td>
            </tr>
        </table>
    {% endif %}

    {% if tasa_data %}
        <h2>Datos del Archivo Tasas.xlsx (tasa expresada en tanto por uno).</h2>
        <table border="1">
            <tr>
                <th>F_Desde</th>
                <th>F_Hasta_Inc.</th>
                <th>Tasa</th>
            </tr>
            {% for row in tasa_data %}
            <tr>
                <td style="text-align: right;">{{ row['F_Desde'] }}</td>
                <td style="text-align: right;">{{ row['F_Hasta_Inc'] }}</td>
                <td style="text-align: right;">{{ row['Tasa'] }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}

    {% if calc_date %}
        <p>Fecha de Cálculo {{ calc_date }} </p>
       {% endif %}
    
    <p>Contacto: <a href="mailto:vnatale52@gmail.com">Enviar un correo electrónico a Vincenzo Natale:   vnatale52@gmail.com  </a></p>
    <p>MIT License  -  Copyright (c) 2025 Vincenzo Natale </a></p>
    
    <button onclick="sendLike()">If it has been useful to you, I deserve a Like ❤️</button>
    <p id="likes">Likes: {{ likes }}</p>
    
    <script>
        function sendLike() {
            fetch('/like', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                document.getElementById('likes').innerText = 'Likes: ' + data.likes;
            });
        }
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
    return render_template_string(html_template, likes=likes)

# Route to handle file upload for tasa data
@app.route("/upload_tasa", methods=["POST"])
def upload_tasa_file():
    global uploaded_tasa
    file = request.files["tasa_file"]
    if not file:
        flash("No se subió ningún archivo.", "error")
        return render_template_string(html_template)

    try:
        df_tasa = pd.read_excel(file)
        df_tasa.columns = df_tasa.columns.str.strip()
        required_columns = ["F_Desde", "F_Hasta_Inc.", "Tasa"]
        validate_dataframe(df_tasa, required_columns)

        df_tasa["F_Desde"] = pd.to_datetime(df_tasa["F_Desde"], format="%d-%m-%Y", errors="coerce")
        df_tasa["F_Hasta_Inc."] = pd.to_datetime(df_tasa["F_Hasta_Inc."], format="%d-%m-%Y", errors="coerce")

        uploaded_tasa = df_tasa
        flash("Archivo de tasas cargado exitosamente.", "success")
        return render_template_string(
            html_template,
            tasa_data=df_tasa.assign(
                F_Desde=df_tasa["F_Desde"].dt.strftime("%d-%m-%Y"),
                F_Hasta_Inc=df_tasa["F_Hasta_Inc."].dt.strftime("%d-%m-%Y"),
                Tasa=df_tasa["Tasa"].apply(lambda x: "{:,.4f}".format(x).replace(".", ","))
            ).to_dict(orient="records")
        )
    except Exception as e:
        logging.error(f"Error processing tasa file: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}", "error")
        return render_template_string(html_template)

# Route to set the calculation date
@app.route("/set_date", methods=["POST"])
def set_date():
    global calc_date_global
    calc_date = request.form.get("calc_date")
    if not calc_date:
        flash("No se proporcionó ninguna fecha.", "error")
        return render_template_string(html_template)

    try:
        calc_date_global = datetime.strptime(calc_date, "%Y-%m-%d")
        flash(f"Fecha de cálculo establecida: {calc_date_global.strftime('%d-%m-%Y')}", "success")
        return render_template_string(html_template, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except ValueError:
        flash("Formato de fecha no válido.", "error")
        return render_template_string(html_template)

# Route to process the uploaded debt file
@app.route("/process", methods=["POST"])
def process_file():
    global uploaded_tasa, calc_date_global
    file = request.files["excel_file"]

    if not file:
        flash("No se cargó ningún archivo.", "error")
        return render_template_string(html_template)

    if uploaded_tasa is None:
        flash("No se ha cargado el archivo Tasa.xlsx.", "error")
        return render_template_string(html_template)

    if calc_date_global is None:
        flash("No se ha establecido la fecha de cálculo.", "error")
        return render_template_string(html_template)

    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        required_columns = ["Mes y Año", "Fecha_Vto", "Importe_Deuda"]
        validate_dataframe(df, required_columns)

        df["Fecha_Vto"] = pd.to_datetime(df["Fecha_Vto"], format="%d-%m-%Y", errors="coerce")
        if df["Fecha_Vto"].isnull().any():
            flash("Algunas fechas de vencimiento no son válidas o están ausentes.", "error")
            return render_template_string(html_template)

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

        data = df.to_dict(orient="records")
        subtotals = subtotals.to_dict(orient="records")

        return render_template_string(html_template, data=data, extra_columns=extra_columns, subtotals=subtotals, totals=totals, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}", "error")
        return render_template_string(html_template)

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
