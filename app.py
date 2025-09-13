# MIT License  -  Copyright (c) 2025 Vincenzo Natale

from flask import Flask, request, render_template, session, jsonify, g, send_file
import pandas as pd
from datetime import datetime
import logging
import os
import sqlite3
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '9e9b5f8e7a2c4d1e6f8a9b0c3d2eff4')

logging.basicConfig(level=logging.DEBUG)

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

init_db()

def format_number(value):
    return "{:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")

def validate_dataframe(df, required_columns):
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"Missing required columns: {required_columns}")

uploaded_tasa = None
calc_date_global = None

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# ...
# --- aquí va todo tu código anterior intacto hasta la exportación ---
# ...

@app.route("/export", methods=["POST"])
def export_to_excel():
    try:
        data = session.get('data', None)
        subtotals = session.get('subtotals', None)
        totals = session.get('totals', None)
        tasa_data = session.get('tasa_data', None)
        extra_columns = session.get('extra_columns', [])
        calc_date = session.get('calc_date', 'Fecha no disponible')

        if not data or not subtotals or not totals or not tasa_data:
            return jsonify({"success": False, "message": "No hay datos para exportar."})

        df_data = pd.DataFrame(data)
        df_subtotals = pd.DataFrame(subtotals)
        df_totals = pd.DataFrame([totals])
        df_tasa = pd.DataFrame(tasa_data)

        column_order = ['Mes y Año', 'Fecha_Vto', 'Importe_Deuda']
        column_order.extend(extra_columns)
        column_order.extend(['Importe_Intereses', 'Deuda_Actualizada'])
        df_data = df_data[column_order]

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine="xlsxwriter")

        def add_calc_date(sheet_name, df):
            calc_date_df = pd.DataFrame([
                f"Fecha de Cálculo (inclusive): {calc_date}  -  Formatea las columnas 'a tuo proprio piacere' : "
            ])
            calc_date_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=0)
            df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1)

        add_calc_date("Calculo_Intereses", df_data)
        add_calc_date("Subtotales", df_subtotals)
        add_calc_date("Totales", df_totals)
        add_calc_date("Tasas", df_tasa)

        # 🔑 Guardar y cerrar explícitamente
        writer.close()
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="Calculo_Intereses.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logging.error(f"Error exporting to Excel: {str(e)}")
        return jsonify({"success": False, "message": f"Error al exportar a Excel: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'false')
