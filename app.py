# MIT License  -  Copyright (c) 2025 Vincenzo Natale

# Import necessary libraries
from flask import Flask, request, render_template, session, jsonify, flash, g, redirect, url_for, send_file
import pandas as pd
from datetime import datetime
import logging
import os
import sqlite3
from io import BytesIO

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
    data = session.get('data', None)
    extra_columns = session.get('extra_columns', None)
    subtotals = session.get('subtotals', None)
    totals = session.get('totals', None)
    calc_date = session.get('calc_date', None)
    tasa_data = session.get('tasa_data', None)

    # File selection status
    tasa_file_status = session.get('tasa_file_status', ' ')     # colocado ' '  en lugar de "File selected"
    deuda_file_status = session.get('deuda_file_status', ' ')   # colocado ' '  en lugar de "File selected"

    return render_template(
        'index.html',
        likes=likes,
        data=data,
        extra_columns=extra_columns,
        subtotals=subtotals,
        totals=totals,
        calc_date=calc_date,
        tasa_file_status=tasa_file_status,
        deuda_file_status=deuda_file_status,
        tasa_data=tasa_data
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
        session['tasa_data'] = df_tasa.to_dict(orient="records")  # Store tasa data in session
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

# Route to export data to Excel
@app.route("/export", methods=["POST"])
def export_to_excel():
    try:
        # Retrieve data from the session
        data = session.get('data', None)
        subtotals = session.get('subtotals', None)
        totals = session.get('totals', None)
        tasa_data = session.get('tasa_data', None)

        if not data or not subtotals or not totals or not tasa_data:
            flash("No hay datos para exportar.", "error")
            return redirect(url_for('home'))

        # Convert session data back to DataFrames
        df_data = pd.DataFrame(data)
        df_subtotals = pd.DataFrame(subtotals)
        df_totals = pd.DataFrame([totals])
        df_tasa = pd.DataFrame(tasa_data)

        # Create a BytesIO buffer to store the Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_data.to_excel(writer, sheet_name='Calculo_Intereses', index=False)
            df_subtotals.to_excel(writer, sheet_name='Subtotales', index=False)
            df_totals.to_excel(writer, sheet_name='Totales', index=False)
            df_tasa.to_excel(writer, sheet_name='Tasas', index=False)

        output.seek(0)

        # Return the Excel file as a response
        return send_file(output, as_attachment=True, download_name='Calculo_Intereses.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        flash(f"Error al exportar a Excel: {str(e)}", "error")
        return redirect(url_for('home'))

# Run the application
if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true')