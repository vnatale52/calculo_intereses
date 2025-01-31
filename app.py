# Import necessary libraries
from flask import Flask, request, render_template_string  # Flask para la aplicación web, request para manejar solicitudes HTTP, render_template_string para renderizar plantillas HTML
import pandas as pd  # Pandas para manipulación y análisis de datos
from datetime import datetime  # Datetime para manejar operaciones de fecha y hora

# Inicializar la aplicación Flask
app = Flask(__name__)

# Definir la plantilla HTML para la aplicación web
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Web Application para el Cálculo de los Intereses Compensatorios</title>
    <h1>Web Application para el Cálculo de los Intereses Compensatorios - Versión en Desarrollo desde el 26-01-2025, by VN.</h1>
    <p>Herramientas utilizadas: HTML, Python (librerías Flask y Pandas), GitHubPages, Render Web Hosting y ChatGPT.</p>
    <p>(En caso de reproceso, asegurarse que la URL sea sólo https://calculo-intereses.onrender.com (sin ninguna subruta a continuación de .com; de lo contrario, dará un error)</p>
</head>
<body>
    <h1>Paso 1: Ingresa la Fecha hasta la cual (inclusive) los intereses serán calculados.</h1>
    <form action="/set_date" method="post">
        <label for="calc_date">Fecha de Cálculo:</label>
        <input type="date" name="calc_date" required>
        <br><br>
        <button type="submit">Establecer Fecha</button>
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
        <p>Mediante un simple "Copy and Paste" se puede exportar su contenido a Excel.También, se puede generar una salida a PDF para su impresión --  </p>
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
        <h2>Datos del Archivo Tasa.xlsx</h2>
        <table border="1">
            <tr>
                <th>F_Desde</th>
                <th>F_Hasta_Inc.</th>
                <th>Tasa</th>
            </tr>
            {% for row in tasa_data %}
            <tr>
                <td style="text-align: right;">{{ row['F_Desde'] }}</td>
                <td style="text-align: right;">{{ row['F_Hasta_Inc.'] }}</td>
                <td style="text-align: right;">{{ row['Tasa'] }}</td>
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

# Variables globales para almacenar los datos de tasa cargados y la fecha de cálculo
uploaded_tasa = None
calc_date_global = None

# Ruta para la página de inicio
@app.route("/", methods=["GET"])
def upload_file():
    # Renderizar la plantilla HTML
    return render_template_string(html_template)

# Ruta para manejar la carga del archivo de tasas
@app.route("/upload_tasa", methods=["POST"])
def upload_tasa_file():
    global uploaded_tasa
    # Obtener el archivo cargado
    file = request.files["tasa_file"]
    if not file:
        return "No se subió ningún archivo.", 400

    try:
        # Leer el archivo Excel en un DataFrame
        df_tasa = pd.read_excel(file)
        # Eliminar espacios en blanco al principio y al final de los nombres de las columnas
        df_tasa.columns = df_tasa.columns.str.strip()
        # Definir las columnas requeridas
        required_columns = ["F_Desde", "F_Hasta_Inc.", "Tasa"]
        # Verificar si todas las columnas requeridas están presentes
        if not all(col in df_tasa.columns for col in required_columns):
            return "El archivo no contiene las columnas esperadas.", 400
        # Convertir las columnas de fecha al formato datetime
        df_tasa["F_Desde"] = pd.to_datetime(df_tasa["F_Desde"], format="%d-%m-%Y", errors="coerce")
        df_tasa["F_Hasta_Inc."] = pd.to_datetime(df_tasa["F_Hasta_Inc."], format="%d-%m-%Y", errors="coerce")
        # Almacenar el DataFrame en la variable global
        uploaded_tasa = df_tasa
        # Renderizar la plantilla con los datos de tasa
        return render_template_string(
            html_template,
            tasa_data=df_tasa.assign(
                F_Desde=df_tasa["F_Desde"].dt.strftime("%d-%m-%Y"),
                F_Hasta_Inc=df_tasa["F_Hasta_Inc."].dt.strftime("%d-%m-%Y")  # Asegurar formato dd-mm-yyyy
            ).to_dict(orient="records")
        )
    except Exception as e:
        # Manejar cualquier error durante el procesamiento del archivo
        return f"Error al procesar el archivo: {str(e)}", 400

# Ruta para establecer la fecha de cálculo
@app.route("/set_date", methods=["POST"])
def set_date():
    global calc_date_global
    # Obtener la fecha de cálculo del formulario
    calc_date = request.form.get("calc_date")
    if not calc_date:
        return "No se proporcionó ninguna fecha.", 400
    try:
        # Convertir la cadena de fecha a un objeto datetime
        calc_date_global = datetime.strptime(calc_date, "%Y-%m-%d")
        # Renderizar la plantilla con la fecha de cálculo
        return render_template_string(html_template, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except ValueError:
        # Manejar formato de fecha no válido
        return "Formato de fecha no válido.", 400

# Ruta para procesar el archivo de deuda cargado
@app.route("/process", methods=["POST"])
def process_file():
    global uploaded_tasa, calc_date_global
    # Obtener el archivo cargado
    file = request.files["excel_file"]

    if not file:
        return "No se cargó ningún archivo.", 400

    if uploaded_tasa is None:
        return "No se ha cargado el archivo Tasa.xlsx.", 400

    if calc_date_global is None:
        return "No se ha establecido la fecha de cálculo.", 400

    try:
        # Leer el archivo Excel en un DataFrame
        df = pd.read_excel(file)
        # Eliminar espacios en blanco al principio y al final de los nombres de las columnas
        df.columns = df.columns.str.strip()
        # Definir los nombres de las columnas esperadas
        column_mapping = {"Mes y Año": "Mes y Año", "Fecha_Vto": "Fecha_Vto", "Importe_Deuda": "Importe_Deuda"}
        # Verificar si todas las columnas requeridas están presentes
        if not all(col in df.columns for col in column_mapping.keys()):
            return f"El archivo no contiene las columnas esperadas. Columnas detectadas: {list(df.columns)}", 400
        # Renombrar las columnas para estandarizarlas
        df = df.rename(columns=column_mapping)

        # Convertir la columna de fecha de vencimiento al formato datetime
        df["Fecha_Vto"] = pd.to_datetime(df["Fecha_Vto"], format="%d-%m-%Y", errors="coerce")
        # Verificar si alguna fecha no es válida o está ausente
        if df["Fecha_Vto"].isnull().any():
            return "Algunas fechas de vencimiento no son válidas o están ausentes.", 400

        # Función para calcular el número de días transcurridos
        def calcular_dias_transcurridos(row, tasa_row):
            f_desde = tasa_row["F_Desde"]
            f_hasta = tasa_row["F_Hasta_Inc."]
            vencimiento = row["Fecha_Vto"]

            if pd.isnull(vencimiento) or pd.isnull(f_desde) or pd.isnull(f_hasta):
                return None

            dias_transcurridos = (min(calc_date_global, f_hasta) - max(vencimiento, f_desde)).days + 1

            return max(0, dias_transcurridos)

        # Inicializar la lista para almacenar columnas adicionales
        extra_columns = []
        # Definir el nombre de la columna para el coeficiente acumulado
        coef_acumulado_col = 'Coef_Acumulado'

        # Iterar sobre cada fila en el DataFrame de tasas
        for _, tasa_row in uploaded_tasa.iterrows():
            tasa_name = f"Cant_Días ({tasa_row['Tasa']})"
            extra_columns.append(tasa_name)

            # Calcular el número de días transcurridos para cada fila en el DataFrame de deuda
            df[tasa_name] = df.apply(lambda row: calcular_dias_transcurridos(row, tasa_row), axis=1)

        # Inicializar la columna de coeficiente acumulado
        df[coef_acumulado_col] = 0
        # Calcular el coeficiente acumulado para cada fila
        for i in range(len(df)):
            for tasa_row in uploaded_tasa.itertuples():
                tasa_name = f"Cant_Días ({tasa_row.Tasa})"
                if not pd.isna(df.at[i, tasa_name]):
                    df.at[i, coef_acumulado_col] += (df.at[i, tasa_name] * tasa_row.Tasa) / 30

        # Agregar la columna de coeficiente acumulado a la lista de columnas adicionales si no está presente
        if coef_acumulado_col not in extra_columns:
            extra_columns.append(coef_acumulado_col)

        # Calcular el monto de intereses y la deuda actualizada
        df["Importe_Intereses"] = (df["Importe_Deuda"] * df[coef_acumulado_col]).round(2)
        df["Deuda_Actualizada"] = (df["Importe_Deuda"] + df["Importe_Intereses"]).round(2)

        # Formatear las columnas Importe_Deuda, Importe_Intereses y Deuda_Actualizada
        df["Importe_Deuda"] = df["Importe_Deuda"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        df["Importe_Intereses"] = df["Importe_Intereses"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        df["Deuda_Actualizada"] = df["Deuda_Actualizada"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))

        # Reemplazar el punto por la coma en la columna coef_acumulado_col
        df[coef_acumulado_col] = df[coef_acumulado_col].apply(lambda x: "{:,.8f}".format(x).replace(".", ","))  # coef redondeado a 8 decimales y coma como separador.

        # Extraer el año de la columna "Mes y Año"
        df["Año"] = pd.to_datetime(df["Mes y Año"], format="%m-%Y", errors="coerce").dt.year
        # Calcular subtotales por año
        subtotals = df.groupby("Año").agg(
            Subtotal_Importe_Deuda=("Importe_Deuda", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Importe_Intereses=("Importe_Intereses", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Deuda_Actualizada=("Deuda_Actualizada", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x))
        ).reset_index()

        # Formatear los subtotales
        subtotals["Subtotal_Importe_Deuda"] = subtotals["Subtotal_Importe_Deuda"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        subtotals["Subtotal_Importe_Intereses"] = subtotals["Subtotal_Importe_Intereses"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        subtotals["Subtotal_Deuda_Actualizada"] = subtotals["Subtotal_Deuda_Actualizada"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))

        # Calcular los totales generales
        totals = {
            "Total_Importe_Deuda": "{:,.2f}".format(df["Importe_Deuda"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", "."),
            "Total_Importe_Intereses": "{:,.2f}".format(df["Importe_Intereses"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", "."),
            "Total_Deuda_Actualizada": "{:,.2f}".format(df["Deuda_Actualizada"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", ".")
        }

        # Formatear las columnas "Mes y Año" y "Fecha_Vto"
        df["Mes y Año"] = pd.to_datetime(df["Mes y Año"], errors="coerce").dt.strftime("%m-%Y")
        df["Fecha_Vto"] = df["Fecha_Vto"].dt.strftime("%d-%m-%Y")

        # Convertir el DataFrame a una lista de diccionarios para renderizar en la plantilla
        data = df.to_dict(orient="records")
        subtotals = subtotals.to_dict(orient="records")

        # Renderizar la plantilla con los datos procesados y la fecha de cálculo
        return render_template_string(html_template, data=data, extra_columns=extra_columns, subtotals=subtotals, totals=totals, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except Exception as e:
        # Manejar cualquier error durante el procesamiento del archivo
        return f"Error al procesar el archivo: {str(e)}", 400

# Ejecutar la aplicación Flask
if __name__ == "__main__":
    app.run()