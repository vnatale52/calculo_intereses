# Import necessary libraries
from flask import Flask, request, render_template_string  # Flask for web application, request to handle HTTP requests, render_template_string to render HTML templates
import pandas as pd  # Pandas for data manipulation and analysis
from datetime import datetime  # Datetime for handling date and time operations

# Initialize the Flask application
app = Flask(__name__)

# Define the HTML template for the web application
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title> Web Application para el Cálculo de los Intereses Compensatorios </title>
     <h1> Web Application para el Cálculo de los Intereses Compensatorios - Versión en Desarrollo desde el 26-01-2025, by VN. </h1>
    <p> Herramientas utilizadas:  HTML, Python (librerías Flask y Pandas), GitHubPages, Render Web Hosting y ChatGPT. </p>
    <p> (En caso de reproceso, asegurarse que la URL sea sólo  https://calculo-intereses.onrender.com  (sin ninguna subruta a continuación de .com   ; de lo contrario, dará un error) <p>

</head>
<body>

    <h1>Paso 1 : Ingresa la Fecha hasta la cual (inclusive) los intereses serán calculados.</h1>
    <form action="/set_date" method="post">
        <label for="calc_date">Fecha de Cálculo:</label>
        <input type="date" name="calc_date" required>
        <br><br>
        <button type="submit">Establecer Fecha</button>
    </form>

<h1>Paso 2 : Carga el archivo Tasas.xlsx. Los Títulos de las 3 columnas deben ser :  F_Desde , F_Hasta_Inc. , Tasa. </h1>
 <p> Las fechas deben estar en el formato dd-mm-yyyy  y la tasa nominal mensual debe estar expresada en tanto por uno, para 30 días de plazo; el denominador utilizado es siempre 30 días y no hay capitalización de intereses. </p>
    <form action="/upload_tasa" method="post" enctype="multipart/form-data">
        <input type="file" name="tasa_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

 <h1>Paso 3 : Carga el archivo Deuda.xlsx . Los Títulos de las 3 columnas deben ser : Mes y Año , Fecha_Vto , Importe_Deuda.</h1>
 <p> La columna "Mes y Año" debe estar en el formato mm-yyyy ,  "Fecha_Vto" en formato dd-mm-yyyy y la coma debe ser el separador decimal. </p>
    <form action="/process" method="post" enctype="multipart/form-data">
        <input type="file" name="excel_file" accept=".xlsx" required>
        <br><br>
        <button type="submit">Cargar Archivo</button>
    </form>

    {% if data %}
        <h2>Valor nominal de la deuda, Intereses compensatorios calculados y deuda actualizada : </h2>
        <p> Fecha de Cálculo: {{ calc_date }} </p>
        <p> Mediante un simple copy and paste se puede copiar y pegar este cuadro a una hoja en Excel </p>
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

# Global variables to store uploaded tasa data and calculation date
uploaded_tasa = None
calc_date_global = None

# Route for the home page
@app.route("/", methods=["GET"])
def upload_file():
    # Render the HTML template
    return render_template_string(html_template)

# Route to handle the upload of the tasa file
@app.route("/upload_tasa", methods=["POST"])
def upload_tasa_file():
    global uploaded_tasa
    # Get the uploaded file
    file = request.files["tasa_file"]
    if not file:
        return "No se subió ningún archivo.", 400

    try:
        # Read the Excel file into a DataFrame
        df_tasa = pd.read_excel(file)
        # Strip any leading/trailing whitespace from column names
        df_tasa.columns = df_tasa.columns.str.strip()
        # Define the required columns
        required_columns = ["F_Desde", "F_Hasta_Inc.", "Tasa"]
        # Check if all required columns are present
        if not all(col in df_tasa.columns for col in required_columns):
            return "El archivo no contiene las columnas esperadas.", 400
        # Convert date columns to datetime format
        df_tasa["F_Desde"] = pd.to_datetime(df_tasa["F_Desde"], format="%d-%m-%Y", errors="coerce")
        df_tasa["F_Hasta_Inc."] = pd.to_datetime(df_tasa["F_Hasta_Inc."], format="%d-%m-%Y", errors="coerce")
        # Store the DataFrame in the global variable
        uploaded_tasa = df_tasa
        # Render the template with the tasa data
        return render_template_string(
            html_template,
            tasa_data=df_tasa.assign(
                F_Desde=df_tasa["F_Desde"].dt.strftime("%d-%m-%Y"),
                F_Hasta_Inc=df_tasa["F_Hasta_Inc."].dt.strftime("%d-%m-%Y")  # Asegurar formato dd-mm-yyyy
            ).to_dict(orient="records")
        )
    except Exception as e:
        # Handle any errors during file processing
        return f"Error al procesar el archivo: {str(e)}", 400

# Route to set the calculation date
@app.route("/set_date", methods=["POST"])
def set_date():
    global calc_date_global
    # Get the calculation date from the form
    calc_date = request.form.get("calc_date")
    if not calc_date:
        return "No se proporcionó ninguna fecha.", 400
    try:
        # Convert the date string to a datetime object
        calc_date_global = datetime.strptime(calc_date, "%Y-%m-%d")
        # Render the template with the calculation date
        return render_template_string(html_template, calc_date=calc_date_global.strftime("%d-%m-%Y"))
    except ValueError:
        # Handle invalid date format
        return "Formato de fecha no válido.", 400

# Route to process the uploaded debt file
@app.route("/process", methods=["POST"])
def process_file():
    global uploaded_tasa, calc_date_global
    # Get the uploaded file
    file = request.files["excel_file"]

    if not file:
        return "No se cargó ningún archivo.", 400

    if uploaded_tasa is None:
        return "No se ha cargado el archivo Tasa.xlsx.", 400

    if calc_date_global is None:
        return "No se ha establecido la fecha de cálculo.", 400

    try:
        # Read the Excel file into a DataFrame
        df = pd.read_excel(file)
        # Strip any leading/trailing whitespace from column names
        df.columns = df.columns.str.strip()
        # Define the expected column names
        column_mapping = {"Mes y Año": "Mes y Año", "Fecha_Vto": "Fecha_Vto", "Importe_Deuda": "Importe_Deuda"}
        # Check if all required columns are present
        if not all(col in df.columns for col in column_mapping.keys()):
            return f"El archivo no contiene las columnas esperadas. Columnas detectadas: {list(df.columns)}", 400
        # Rename columns to standardize them
        df = df.rename(columns=column_mapping)

        # Convert the due date column to datetime format
        df["Fecha_Vto"] = pd.to_datetime(df["Fecha_Vto"], format="%d-%m-%Y", errors="coerce")
        # Check if any dates are invalid or missing
        if df["Fecha_Vto"].isnull().any():
            return "Algunas fechas de vencimiento no son válidas o están ausentes.", 400

        # Function to calculate the number of days elapsed
        def calcular_dias_transcurridos(row, tasa_row):
            f_desde = tasa_row["F_Desde"]
            f_hasta = tasa_row["F_Hasta_Inc."]
            vencimiento = row["Fecha_Vto"]

            if pd.isnull(vencimiento) or pd.isnull(f_desde) or pd.isnull(f_hasta):
                return None

            dias_transcurridos = (min(calc_date_global, f_hasta) - max(vencimiento, f_desde)).days + 1

            return max(0, dias_transcurridos)

        # Initialize list to store extra columns
        extra_columns = []
        # Define the column name for accumulated coefficient
        coef_acumulado_col = 'Coef_Acumulado'

        # Iterate over each row in the tasa DataFrame
        for _, tasa_row in uploaded_tasa.iterrows():
            tasa_name = f"Cant_Días ({tasa_row['Tasa']})"
            extra_columns.append(tasa_name)

            # Calculate the number of days elapsed for each row in the debt DataFrame
            df[tasa_name] = df.apply(lambda row: calcular_dias_transcurridos(row, tasa_row), axis=1)

        # Initialize the accumulated coefficient column
        df[coef_acumulado_col] = 0
        # Calculate the accumulated coefficient for each row
        for i in range(len(df)):
            for tasa_row in uploaded_tasa.itertuples():
                tasa_name = f"Cant_Días ({tasa_row.Tasa})"
                if not pd.isna(df.at[i, tasa_name]):
                    df.at[i, coef_acumulado_col] += (df.at[i, tasa_name] * tasa_row.Tasa) / 30

        # Add the accumulated coefficient column to the extra columns list if not already present
        if coef_acumulado_col not in extra_columns:
            extra_columns.append(coef_acumulado_col)

        # Calculate the interest amount and updated debt
        df["Importe_Intereses"] = (df["Importe_Deuda"] * df[coef_acumulado_col]).round(2)
        df["Deuda_Actualizada"] = (df["Importe_Deuda"] + df["Importe_Intereses"]).round(2)

        # Format the columns Importe_Deuda, Importe_Intereses, and Deuda_Actualizada
        df["Importe_Deuda"] = df["Importe_Deuda"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        df["Importe_Intereses"] = df["Importe_Intereses"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        df["Deuda_Actualizada"] = df["Deuda_Actualizada"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))

        # Reemplazar el punto por la coma en la columna coef_acumulado_col
        df[coef_acumulado_col] = df[coef_acumulado_col].apply(lambda x: "{:,.8f}".format(x).replace(".", ","))  # coef readondeado 8 decimales y coma como separador.

        # Extract the year from the "Mes y Año" column
        df["Año"] = pd.to_datetime(df["Mes y Año"], format="%m-%Y", errors="coerce").dt.year
        # Calculate subtotals by year
        subtotals = df.groupby("Año").agg(
            Subtotal_Importe_Deuda=("Importe_Deuda", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Importe_Intereses=("Importe_Intereses", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x)),
            Subtotal_Deuda_Actualizada=("Deuda_Actualizada", lambda x: sum(float(val.replace(".", "").replace(",", ".")) for val in x))
        ).reset_index()

        # Format the subtotals
        subtotals["Subtotal_Importe_Deuda"] = subtotals["Subtotal_Importe_Deuda"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        subtotals["Subtotal_Importe_Intereses"] = subtotals["Subtotal_Importe_Intereses"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        subtotals["Subtotal_Deuda_Actualizada"] = subtotals["Subtotal_Deuda_Actualizada"].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))

        # Calculate the total amounts
        totals = {
            "Total_Importe_Deuda": "{:,.2f}".format(df["Importe_Deuda"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", "."),
            "Total_Importe_Intereses": "{:,.2f}".format(df["Importe_Intereses"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", "."),
            "Total_Deuda_Actualizada": "{:,.2f}".format(df["Deuda_Actualizada"].apply(lambda x: float(x.replace(".", "").replace(",", "."))).sum()).replace(",", "X").replace(".", ",").replace("X", ".")
        }

       		
		# Format the "Mes y Año" and "Fecha_Vto" columns
        df["Mes y Año"] = pd.to_datetime(df["Mes y Año"], errors="coerce").dt.strftime("%m-%Y")
        df["Fecha_Vto"] = df["Fecha_Vto"].dt.strftime("%d-%m-%Y")

        # Convert the DataFrame to a list of dictionaries for rendering in the template
        data = df.to_dict(orient="records")
        subtotals = subtotals.to_dict(orient="records")

  		# Render the template with the processed data
        return render_template_string(html_template, data=data, extra_columns=extra_columns, subtotals=subtotals, totals=totals)
    except Exception as e:
        # Handle any errors during file processing
        return f"Error al procesar el archivo: {str(e)}", 400

# Run the Flask application
if __name__ == "__main__":
    #  app.run(debug=True)  Modificado por mí
       app.run()
	   
		