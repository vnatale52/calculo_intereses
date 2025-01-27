from flask import Flask, request, render_template_string
import pandas as pd
from datetime import datetime

app = Flask(__name__)

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title> Web Application para el Cálculo de los Intereses Compensatorios </title>
     <h1> Web Application para el Cálculo de los Intereses Compensatorios - Versión en Desarrollo desde el 26-01-2025, by VN </h1>
    <p> Herramientas utilizadas:  HTML, Python (librerías Flask y Pandas), GitHubPages, Render Web Hosting y ChatGPT </p>
</head>
<body>

    <h1>Paso 1 : Ingresa la Fecha hasta la cual (inclusive) los intereses serán calculados</h1>
    <form action="/set_date" method="post">
        <label for="calc_date">Fecha de Cálculo:</label>
        <input type="date" name="calc_date" required>
        <br><br>
        <button type="submit">Establecer Fecha</button>
    </form>

<h1>Paso 2 : Carga el archivo Tasas.xlsx. Los Títulos de las 3 columnas deben ser :  F_Desde , F_Hasta_Inc. , Tasa </h1>
 <p> Las fechas deben estar en el formato dd-mm-yyyy  y la tasa nominal mensual debe estar expresada en tanto por uno, para 30 días de plazo; el denominador utilizado es siempre 30 días y no hay capitalización de intereses </p>
    <form action="/upload_tasa" method="post" enctype="multipart/form-data">
        <input type="file" name="tasa_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

 <h1>Paso 3 : Carga el archivo Deuda.xlsx . Los Títulos de las 3 columnas deben ser : Mes y Año , Fecha_Vto , Importe_Deuda</h1>
 <p> La columna "Mes y Año" debe estar en el formato mm-yyyy ,  "Fecha_Vto" en formato dd-mm-yyyy y la coma debe ser el separador decimal </p>
    <form action="/process" method="post" enctype="multipart/form-data">
        <input type="file" name="excel_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

    {% if data %}
        <h2>Datos del Archivo Deuda.xlsx</h2>
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
        <table border="1">
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
        <table border="1">
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

    {% if tasa_data %}
        <h2>Datos del Archivo Tasa.xlsx</h2>
        <table border="1">
            <tr>
                <th>F_Desde</th>
                <th>F_Hasta_Inc.</th>
                <th>Tasa</th>
            </tr>
            {% for row in tasa_data %}
            <tr>
                <td>{{ row['F_Desde'] }}</td>
                <td>{{ row['F_Hasta_Inc.'] }}</td>
                <td>{{ row['Tasa'] }}</td>
            </tr>
            {% endfor %}
        </table>
    {% endif %}

    {% if calc_date %}
        <h2>Fecha de Cálculo</h2>
        <p>{{ calc_date }}</p>
    {% endif %}
</body>
</html>
"""

uploaded_tasa = None
calc_date_global = None

@app.route("/", methods=["GET"])
def upload_file():
    return render_template_string(html_template)

@app.route("/upload_tasa", methods=["POST"])
def upload_tasa_file():
    global uploaded_tasa
    file = request.files["tasa_file"]
    if not file:
        return "No se subió ningún archivo.", 400

    try:
        df_tasa = pd.read_excel(file)
        df_tasa.columns = df_tasa.columns.str.strip()
        required_columns = ["F_Desde", "F_Hasta_Inc.", "Tasa"]
        if not all(col in df_tasa.columns for col in required_columns):
            return "El archivo no contiene las columnas esperadas.", 400
        df_tasa["F_Desde"] = pd.to_datetime(df_tasa["F_Desde"], format="%d-%m-%Y", errors="coerce")
        df_tasa["F_Hasta_Inc."] = pd.to_datetime(df_tasa["F_Hasta_Inc."], format="%d-%m-%Y", errors="coerce")
        uploaded_tasa = df_tasa
        return render_template_string(
            html_template,
            tasa_data=df_tasa.assign(
                F_Desde=df_tasa["F_Desde"].dt.strftime("%d-%m-%Y"),
                F_Hasta_Inc=df_tasa["F_Hasta_Inc."].dt.strftime("%d-%m-%Y")
            ).to_dict(orient="records")
        )
    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}", 400

@app.route("/set_date", methods=["POST"])
def set_date():
    global calc_date_global
    calc_date = request.form.get("calc_date")
    if not calc_date:
        return "No se proporcionó ninguna fecha.", 400
    try:
        calc_date_global = datetime.strptime(calc_date, "%Y-%m-%d")
        return render_template_string(html_template, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except ValueError:
        return "Formato de fecha no válido.", 400

@app.route("/process", methods=["POST"])
def process_file():
    global uploaded_tasa, calc_date_global
    file = request.files["excel_file"]

    if not file:
        return "No se cargó ningún archivo.", 400

    if uploaded_tasa is None:
        return "No se ha cargado el archivo Tasa.xlsx.", 400

    if calc_date_global is None:
        return "No se ha establecido la fecha de cálculo.", 400

    try:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()
        column_mapping = {"Mes y Año": "Mes y Año", "Fecha_Vto": "Fecha_Vto", "Importe_Deuda": "Importe_Deuda"}
        if not all(col in df.columns for col in column_mapping.keys()):
            return f"El archivo no contiene las columnas esperadas. Columnas detectadas: {list(df.columns)}", 400
        df = df.rename(columns=column_mapping)

        df["Fecha_Vto"] = pd.to_datetime(df["Fecha_Vto"], format="%d-%m-%Y", errors="coerce")
        if df["Fecha_Vto"].isnull().any():
            return "Algunas fechas de vencimiento no son válidas o están ausentes.", 400

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

        df["Año"] = pd.to_datetime(df["Mes y Año"], format="%m-%Y", errors="coerce").dt.year
        subtotals = df.groupby("Año").agg(
            Subtotal_Importe_Deuda=("Importe_Deuda", "sum"),
            Subtotal_Importe_Intereses=("Importe_Intereses", "sum"),
            Subtotal_Deuda_Actualizada=("Deuda_Actualizada", "sum")
        ).reset_index().to_dict(orient="records")

        totals = {
            "Total_Importe_Deuda": df["Importe_Deuda"].sum(),
            "Total_Importe_Intereses": df["Importe_Intereses"].sum(),
            "Total_Deuda_Actualizada": df["Deuda_Actualizada"].sum()
        }

        df["Mes y Año"] = pd.to_datetime(df["Mes y Año"], errors="coerce").dt.strftime("%m-%Y")
        df["Fecha_Vto"] = df["Fecha_Vto"].dt.strftime("%d-%m-%Y")
        df[coef_acumulado_col] = df[coef_acumulado_col].round(6)

        data = df.to_dict(orient="records")

        return render_template_string(html_template, data=data, extra_columns=extra_columns, subtotals=subtotals, totals=totals)
    except Exception as e:
        return f"Error al procesar el archivo: {str(e)}", 400

if __name__ == "__main__":
    #  app.run(debug=True)
       app.run()
