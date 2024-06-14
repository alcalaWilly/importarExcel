from flask import Flask, render_template, request, jsonify,send_file,url_for,session,make_response
import os #acceder a los directorios
import tempfile
import json
import pandas as pd
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
from flask import redirect
from flask.helpers import flash
from database import get_num_ninos,reporte_hg, ninos_por_establecimiento,grafico_hg,consultar_padron,get_database_connection,eliminar_tabla_reporte
from sqlalchemy import create_engine, text
from io import StringIO
import io
import mysql.connector

#acceder al archivo index,html
template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir, 'muni','templates')
#inicializar flask
app = Flask(__name__,template_folder=template_dir,  static_folder='static')



@app.route('/')
def index():
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Elimina los datos de la sesión
    session.pop('user_id', None)
    session.pop('username', None)
    # Limpiar cookies
    response = make_response(redirect(url_for('index')))
    response.set_cookie('session', '', expires=0)
    return response 

@app.after_request
def add_header(response):
    # Desactivar la caché del navegador
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/login', methods=['POST'])
def login():
    usuario = request.form['usuario']
    password = request.form['password']
    
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE usuario = %s AND password = %s", (usuario, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user'] = user
            session['nombres'] = user['nombres']
            return redirect(url_for('dash'))
        else:
            error_message = "Usuario o contraseña incorrectos"
            return render_template('login.html', error_message=error_message)
    else:
        error_message = "Error de conexión a la base de datos"
        return render_template('login.html', error_message=error_message)

@app.route('/dash')
def dash():
    if 'user' in session:
        num_ninos = get_num_ninos()
        num_reporte = reporte_hg()
        data_json = ninos_por_establecimiento()
        data_anemia = grafico_hg()
        return render_template('dash.html', num_ninos=num_ninos, num_reporte=num_reporte, data_json=data_json, data_anemia=data_anemia)
    else:
        # Si la sesión del usuario no está activa, redirigir al inicio de sesión
        
        # Elimina los datos de la sesión
        response = make_response(redirect(url_for('logout')))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

# @app.route('/subir')
# def subir():
#     return render_template('subir.html')



@app.route('/padron', methods=['GET', 'POST'])
def padron():
    return render_template('padron.html')

@app.route('/padron_de_niños', methods=['GET', 'POST'])
def padron_niños():
    padron_data_json = consultar_padron()

    return padron_data_json

@app.route('/anemia')
def anemia():
    return render_template('anemia.html')

@app.route('/descarga', methods=['GET','POST'])
def descarga():
    data_anemia = grafico_hg()
    data_tabla=tabla_anemias()
    
    return render_template('descarga.html',data_anemia=data_anemia,data_tabla=data_tabla)


@app.route('/tabla_dataAnemia', methods=['GET','POST'])
def tabla_anemias():
    database = get_database_connection()
    cursor = database.cursor()

    query = """
    SELECT
    subquery.HG_last,
    subquery.fecha_last,
    n.nombres,
    CONCAT(n.apellidoPaterno, ' ', n.apellidoMaterno) AS apellidos,
    n.tipoDocumento,
    n.fechaNacimiento,
    subquery.edad,
    s.descripcionSexo,
    e.descripcionEsta,
    subquery.programas
FROM (
    SELECT 
        r.idMenor,
        MAX(CASE 
            WHEN r.HG4 IS NOT NULL AND r.HG4 <= 11.0 THEN r.HG4 
            WHEN r.HG3 IS NOT NULL AND r.HG3 <= 11.0 THEN r.HG3 
            WHEN r.HG2 IS NOT NULL AND r.HG2 <= 11.0 THEN r.HG2 
            WHEN r.HG1 <= 11.0 THEN r.HG1 
            ELSE NULL 
        END) AS HG_last, 
        MAX(CASE 
            WHEN r.HG4 IS NOT NULL AND r.HG4 <= 11.0 THEN r.fecha4 
            WHEN r.HG3 IS NOT NULL AND r.HG3 <= 11.0 THEN r.fecha3 
            WHEN r.HG2 IS NOT NULL AND r.HG2 <= 11.0 THEN r.fecha2 
            WHEN r.HG1 <= 11.0 THEN r.fecha1 
            ELSE NULL 
        END) AS fecha_last,
        MAX(CASE 
            WHEN TIMESTAMPDIFF(DAY, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())) < 30 THEN
                CONCAT(TIMESTAMPDIFF(DAY, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())), ' días')
            WHEN TIMESTAMPDIFF(MONTH, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())) < 12 THEN
                CONCAT(TIMESTAMPDIFF(MONTH, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())), ' meses')
            ELSE
                CONCAT(
                    TIMESTAMPDIFF(YEAR, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())), ' años, ',
                    TIMESTAMPDIFF(MONTH, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())) % 12, ' meses, ',
                    FLOOR(TIMESTAMPDIFF(DAY, STR_TO_DATE(n.fechaNacimiento, '%Y-%m-%d'), DATE(NOW())) % 30.436875), ' días'
                )
        END) AS edad,
        MAX(CASE 
            WHEN n.programa LIKE '%0%' THEN 'NINGUNO'
            WHEN n.programa LIKE '%1%' THEN 'PIN'
            WHEN n.programa LIKE '%2%' THEN 'PVL'
            WHEN n.programa LIKE '%4%' THEN 'JUNTOS'
            WHEN n.programa LIKE '%5%' THEN 'QALIWARMA'
            WHEN n.programa LIKE '%7%' THEN 'CUNA+SCD'
            WHEN n.programa LIKE '%8%' THEN 'CUNA+SAF'
            WHEN n.programa = '' THEN 'NINGUNO'
            ELSE 'OTRO'
        END) AS programas
    FROM 
        reportehemoglobina r
    JOIN 
        niños n ON r.idMenor = n.tipoDocumento
    WHERE
        (r.HG4 IS NOT NULL AND r.HG4 <= 11.0) OR
        (r.HG3 IS NOT NULL AND r.HG3 <= 11.0) OR
        (r.HG2 IS NOT NULL AND r.HG2 <= 11.0) OR
        (r.HG1 <= 11.0)
    GROUP BY 
        r.idMenor
) AS subquery
JOIN 
    niños n ON subquery.idMenor = n.tipoDocumento
JOIN 
    sexo s ON n.sexo = s.idSexo
JOIN 
    establecimiento e ON n.idEstablecimiento = e.idEstablecimiento
WHERE 
    subquery.HG_last IS NOT NULL;


    """
    
    cursor.execute(query)

    rows_tabla_anemia = cursor.fetchall()

    cursor.close()

    # Convertir resultados a JSON
    reporteHemo_json = []
    for row in rows_tabla_anemia:
        dic = {}
        dic['nombres']= row[2]
        dic['apellidos']= row[3]
        dic['tipoDocumento']= row[4]
        dic['fechaNacimiento']= row[5]
        dic['edad']= row[6]
        dic['descripcionSexo']= row[7]
        dic['programaSocial']= row[9]
        dic['descripcionEsta']= row[8]
        dic['fecha_last']= row[1]
        dic['HG_last']= row[0]
        reporteHemo_json.append(dic)
        
    return jsonify({"datos":[reporteHemo_json]})

app.secret_key = '123'


@app.route('/generar_excel', methods=['POST','GET']) 
def generar_excel():
    if request.method == 'POST':
        try:
            json_data = request.get_json()
            data = json_data['jsonData']

            # Convertir los datos JSON en una estructura Python
            data_python = json.loads(data)

            # Crear un DataFrame de pandas
            df = pd.DataFrame(data_python)

            # Crear un archivo temporal para guardar el Excel
            temp_dir = tempfile.gettempdir()
            excel_filename = 'ReporteMensual.xlsx'
            excel_file_path = os.path.join(temp_dir, excel_filename)

            # Guardar el DataFrame como un archivo Excel
            df.to_excel(excel_file_path, index=False)

            # Verificar si el archivo se ha creado correctamente
            if not os.path.exists(excel_file_path):
                return jsonify({"error": "El archivo Excel no se pudo generar."}), 500

            print('La ruta es: ', excel_file_path)

            # Redirige a la ruta de descarga con el nombre del archivo temporal
            return jsonify({"filename": excel_filename})

        except Exception as e:
            # Maneja las excepciones
            app.logger.error("Error al generar el archivo Excel: %s", str(e))
            return jsonify({"error": "Error al generar el archivo Excel"}), 500
    else:
        return jsonify({"error": "Método no permitido"}), 405

@app.route('/descargar_excel/<filename>')
def descargar_excel(filename):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    file_path = file_path.replace('\\', '/')
    print('File path for download: ', file_path)

    # Enviar el archivo al cliente para su descarga
    return send_file(file_path, as_attachment=True, download_name=filename)

@app.route('/subirTodoPage')
def subirTodoPage():
    return render_template('subir_2.html')

@app.route('/subirTodo', methods=['POST','GET']) 
def subirTodo():
    if request.method == 'POST':
        try:
            file = request.files['file']

            # Lee el archivo XLSX
            datos = pd.read_excel(file, header=None)

            # Crea un archivo temporal para guardar el CSV
            temp_dir = tempfile.gettempdir()
            csv_filename = 'convertido_padron.csv'
            csv_file_path = os.path.join(temp_dir, csv_filename)
            
            # Convierte y guarda como CSV
            datos.to_csv(csv_file_path, sep=';', encoding='utf-8', index=False)
            
            # Aplicar las modificaciones con la función Menor
            df_modificado = Menor_Padron(csv_file_path)
            df_madre = madre(csv_file_path)
            df_padre = padre(csv_file_path)

            # Reemplazar valores NaN con valores adecuados (por ejemplo, una cadena vacía)
            df_modificado.fillna('No tiene', inplace=True)
            df_madre.fillna('No tiene', inplace=True)
            df_padre.fillna('No tiene', inplace=True)
            if df_modificado.shape[0] > 0:
            # Convertir el DataFrame modificado a una lista de tuplas
                registros = [tuple(row) for row in df_modificado.values]
                registros_madre = [tuple(row) for row in df_madre.values]
                registros_padre = [tuple(row) for row in df_padre.values]

                # Establecer conexión a la base de datos
                database = get_database_connection()
                cursor = database.cursor()

                # Eliminar registros existentes antes de insertar nuevos datos
                eliminar_registros_existente(cursor)

                # Insertar los nuevos registros en las tablas
                insert_query_niños = "INSERT INTO niños VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.executemany(insert_query_niños, registros)

                insert_query_madre = "INSERT INTO madre VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.executemany(insert_query_madre, registros_madre)

                insert_query_padre = "INSERT INTO padre VALUES (%s, %s, %s, %s, %s)"
                cursor.executemany(insert_query_padre, registros_padre)

                # Commit de los cambios
                database.commit()

                # Cerrar la conexión a la base de datos
                cursor.close()
                database.close()

                return jsonify({'success': True, 'message': 'Los datos se han enviado correctamente a la base de datos.'})
            else:
                return jsonify({'success': False, 'message': 'Excel incorrecto'})
        except KeyError as e:
            # En caso de error específico de KeyError, devolver un mensaje genérico
            return jsonify({'success': False, 'message': 'Se produjo un error al procesar la solicitud.'})

        except mysql.connector.Error as err:
            # En caso de error de MySQL, devolver el mensaje de error
            return jsonify({'success': False, 'message': f"Error de MySQL: {err}"})

        except Exception as e:
            # En caso de cualquier otro error, devolver el mensaje de error
            return jsonify({'success': False, 'message': str(e)})

    return 'Página para subir archivos'


def eliminar_registros_existente(cursor):
    try:
        # Eliminar registros de la tabla reportehemoglobina
        cursor.execute("DELETE FROM reportehemoglobina")

        # Eliminar registros de la tabla padre
        cursor.execute("DELETE FROM padre")

        # Eliminar registros de la tabla madre
        cursor.execute("DELETE FROM madre")

        # Eliminar registros de la tabla niños
        cursor.execute("DELETE FROM niños")

        print("Registros existentes eliminados correctamente.")

    except mysql.connector.Error as err:
        print(f"Error al eliminar registros existentes: {err}")


@app.route('/subirReporte_hemo', methods=['POST','GET']) 
def subirReporte_hemo():
    if request.method == 'POST':
        try:
            file = request.files['file']
            csv_data = manejoHg(file)
            if csv_data:
                # Conexión a la base de datos
                bd = "bd_importarexcel"
                url = "mysql+mysqlconnector://root@localhost/"

                timeout_seconds = 120
                engine = create_engine(url, connect_args={'connect_timeout': timeout_seconds})

                engine = create_engine(url + bd)

                # Leer la columna 'tipoDocumento' de la tabla 'niños' en un DataFrame
                df_tipo_documento = pd.read_sql_query('SELECT tipoDocumento FROM niños', con=engine)

                # Leer el archivo CSV que contiene los datos con la columna 'idMenor'
                data_hg = pd.read_csv(io.StringIO(csv_data), sep=';')

                # Filtrar los datos en data_hg para incluir solo aquellos cuyo valor de 'idMenor' esté presente en la columna 'tipoDocumento' de la tabla 'niños'
                data_para_insertar = data_hg[data_hg['idMenor'].isin(df_tipo_documento['tipoDocumento'])]

                # Eliminar los datos existentes en la tabla 'reportehemoglobina'
                with engine.connect() as con:
                    #con.execute(text('DELETE FROM reportehemoglobina'))
                    eliminar_tabla_reporte()

                # Insertar los nuevos datos en la tabla 'reportehemoglobina'
                data_para_insertar.to_sql(name='reportehemoglobina', con=engine, if_exists='append', index=False)

                return jsonify({'success': True, 'message': 'El archivo se ha procesado y guardado en la base de datos correctamente.'})
            else:
                return jsonify({'success': False, 'message': 'No se encontraron datos válidos en el archivo.'})

        except FileNotFoundError:
            return jsonify({'success': False, 'message': 'No se encontró el archivo.'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Se produjo un error al procesar el archivo: {str(e)}'})

    return 'Página para subir archivos'

def manejoHg(file):
    # Establecimientos
    establecimientos = ['VILLA CAPIRI', 'RIO CHARI ALTO', 'P.S. PITOCUNA', 'P.S. PTE IPOKI', 
                        'P.S. ALTO PITOCUNA', 'P.S. CUSHIVIANI', 'P.S. UNION CUVIRIAKI', 'P.S. SHABASHIPANGO', 
                        'P.S. S.J. DE CHENI','P.S. UNION CAPIRI', 'P.S. MIGUEL GRAU', 'RESUMEN ']

    dict_dataframes = pd.read_excel(file, sheet_name=[hoja for hoja in establecimientos])

    if 'RESUMEN ' in dict_dataframes:
        resumen_dataframe = dict_dataframes['RESUMEN ']
        falta = ['HUAHUARI', 'RIO NEGRO', 'ALTO VILLA VICTORIA']
        resumen_dataframe.columns.values[1] = 'esta'
        resumen_dataframe.columns.values[4] = 'nada1'
        resumen_dataframe.columns.values[5] = 'Unnamed: 4'
        resumen_dataframe.columns.values[2] = 'nada'
        resumen_dataframe.columns.values[3] = 'Unnamed: 2'
        resumen_dataframe = resumen_dataframe[resumen_dataframe['esta'].isin(falta)]
        dict_dataframes['RESUMEN '] = resumen_dataframe

    columnas_deseadas = ['Unnamed: 2', 'Unnamed: 4', 'Unnamed: 7', 'Unnamed: 8', 'Unnamed: 9',
                         'Unnamed: 10', 'Unnamed: 12', 'Unnamed: 13', 'Unnamed: 16', 'Unnamed: 17']
    hojas_sin_columnas_deseadas = []

    contador = 1
    merged_dfs = []
    for nombre_hoja, df in dict_dataframes.items():
        if nombre_hoja in establecimientos and all(col in df.columns for col in columnas_deseadas):
            df_sin_dni = df[~df[columnas_deseadas[0]].astype(str).str.startswith('DNI')]
            df_sin_dni = df_sin_dni[columnas_deseadas].reset_index(drop=True)
            filas_con_datos = df_sin_dni.notnull().any(axis=1)
            df_sin_dni = df_sin_dni[filas_con_datos]
            df_sin_dni.insert(0, 'num', range(contador, contador + len(df_sin_dni)))

            df_sin_dni.columns = ['idReporteHG', 'idMenor', 'grupoEdad', 'HG1', 'fecha1', 'HG2', 'fecha2', 'HG3', 'fecha3', 'fecha4', 'HG4']

            for index, row in df_sin_dni.iterrows():
                if pd.isnull(row['idMenor']) or row['idMenor'] == '':
                    df_sin_dni.at[index, 'idMenor'] = f"Falta Actualizar ({index})"
            
            contador += len(df_sin_dni)
            merged_dfs.append(df_sin_dni)
        else:
            hojas_sin_columnas_deseadas.append(nombre_hoja)

    if hojas_sin_columnas_deseadas:
        print("Las siguientes hojas no contienen todas las columnas deseadas:")
        for hoja in hojas_sin_columnas_deseadas:
            print(hoja)

    if merged_dfs:
        merged_df = pd.concat(merged_dfs)
        csv_buffer = StringIO()
        merged_df.to_csv(csv_buffer, sep=';', encoding='utf-8', index=False)
        csv_data = csv_buffer.getvalue()
        return csv_data

    return None

@app.route('/bd_hemoglobina/<filename>')
def Menor_Padron(csv_file_path):
  
        # Establecimientos
        establecimientos = ['HUAHUARI', 'RIO NEGRO', 'VILLA CAPIRI', 'RIO CHARI ALTO', 'PITOCUNA', 'PUENTE IPOKI', 
                            'ALTO PITOCUNA', 'CUSHIVIANI', 'UNION CUBIRIAKI', 'SHABASHIPANGO', 'SAN JUA CHENI', 
                            'UNION CAPIRI', 'MIGUEL GRAU', 'ALTO VILLA VICTORIA']

        # Leer el archivo CSV
        df = pd.read_csv(csv_file_path, sep=';')

        # Verificar si las columnas necesarias están presentes
        required_columns = ['0', '5', '10', '8', '9', '12', '11', '32', '37']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            missing_columns_str = ', '.join(missing_columns)
            raise ValueError(f"Columnas CSV incorrectas, Vuelve a cargar")

        # Renombrar las columnas
        nuevos_nombres = {
            '0': 'num', 
            '5': 'tipoDocumento', 
            '10': 'nombres',
            '8': 'apellidoPaterno',
            '9': 'apellidoMaterno',
            '12': 'fechaNacimiento',
            '11': 'sexo',
            '32': 'idEstablecimiento',
            '37': 'programa'
        }
        df = df.rename(columns=nuevos_nombres)

        # Verificar si la columna 'idEstablecimiento' está presente después del renombrado
        if 'idEstablecimiento' not in df.columns:
            raise ValueError("La columna 'idEstablecimiento' no se encontró después del renombrado.")

        # Crear un diccionario que mapee los establecimientos a sus índices en el array
        mapeo_establecimientos = {establecimiento: indice + 1 for indice, establecimiento in enumerate(establecimientos)}
        
        # Filtrar el DataFrame para mostrar solo las filas donde el valor en la columna 'idEstablecimiento' coincida con los establecimientos del array 'establecimientos'
        df_filtrado = df[df['idEstablecimiento'].isin(establecimientos)].copy()

        # Reemplazar los valores en la columna 'idEstablecimiento' con los índices correspondientes del array 'establecimientos'
        df_filtrado.loc[:, 'idEstablecimiento'] = df_filtrado['idEstablecimiento'].map(mapeo_establecimientos).fillna(df_filtrado['idEstablecimiento'])

        # Seleccionar las columnas adicionales que deseas agregar
        columnas_adicionales = ['num', 'tipoDocumento', 'nombres', 'apellidoPaterno', 'apellidoMaterno', 'fechaNacimiento', 'sexo','programa']

        # Agregar las columnas adicionales al DataFrame filtrado
        df_filtrado = df_filtrado[columnas_adicionales + ['idEstablecimiento']]

        # Llenar la columna 'tipoDocumento' con el índice de fila si hay valores nulos en alguna fila
        # for index, row in df_filtrado.iterrows():
        #     if row.isnull().values.any():
        #         texto = f"Actualizar ({index})"
        #         df_filtrado.loc[index, 'tipoDocumento'] = texto 
        for index, row in df_filtrado.iterrows():
            id_menor = row['tipoDocumento']
            if pd.isnull(id_menor) or id_menor == '':
                df_filtrado.at[index, 'tipoDocumento'] = f"Falta Actualizar ({index})"

        return df_filtrado

def madre(csv_file_path):
    try:
        # Establecimientos
        establecimientos = ['HUAHUARI', 'RIO NEGRO', 'VILLA CAPIRI', 'RIO CHARI ALTO', 'PITOCUNA', 'PUENTE IPOKI', 
                            'ALTO PITOCUNA', 'CUSHIVIANI', 'UNION CUBIRIAKI', 'SHABASHIPANGO', 'SAN JUA CHENI', 
                            'UNION CAPIRI', 'MIGUEL GRAU', 'ALTO VILLA VICTORIA']

        # Leer el archivo CSV
        df = pd.read_csv(csv_file_path, sep=';')

        # Verificar si las columnas necesarias están presentes
        required_columns = ['42','32', '45', '43', '44', '46', '5']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            missing_columns_str = ', '.join(missing_columns)
            raise ValueError(f"Columnas CSV incorrectas, Vuelve a cargar")

        # Renombrar las columnas
        nuevos_nombres = {
            '42': 'dniMadre', 
            '32': 'idEstablecimiento',
            '45': 'nombresMadre',
            '43': 'apellidoPaterno_Madre',
            '44': 'apellidoMaterno_Madre',
            '46': 'celularMadre',
            '5': 'idMenor',
        }
        df = df.rename(columns=nuevos_nombres)

        # Verificar si la columna 'idEstablecimiento' está presente después del renombrado
        if 'idEstablecimiento' not in df.columns:
            raise ValueError("La columna 'idEstablecimiento' no se encontró después del renombrado.")

        # Crear un diccionario que mapee los establecimientos a sus índices en el array
        mapeo_establecimientos = {establecimiento: indice + 1 for indice, establecimiento in enumerate(establecimientos)}
        
        # Filtrar el DataFrame para mostrar solo las filas donde el valor en la columna 'idEstablecimiento' coincida con los establecimientos del array 'establecimientos'
        df_filtrado = df[df['idEstablecimiento'].isin(establecimientos)].copy()

        # Reemplazar los valores en la columna 'idEstablecimiento' con los índices correspondientes del array 'establecimientos'
        df_filtrado.loc[:, 'idEstablecimiento'] = df_filtrado['idEstablecimiento'].map(mapeo_establecimientos).fillna(df_filtrado['idEstablecimiento'])

        # Seleccionar las columnas adicionales que deseas agregar
        columnas_adicionales = ['dniMadre', 'nombresMadre', 'apellidoPaterno_Madre', 'apellidoMaterno_Madre', 'celularMadre', 'idMenor']

        # Agregar las columnas adicionales al DataFrame filtrado
        df_filtrado = df_filtrado[columnas_adicionales]

        # Llenar la columna 'tipoDocumento' con el índice de fila si hay valores nulos en alguna fila
        for index, row in df_filtrado.iterrows():
            id_menor = row['idMenor']
            if pd.isnull(id_menor) or id_menor == '':
                df_filtrado.at[index, 'idMenor'] = f"Falta Actualizar ({index})"

        return df_filtrado
    except FileNotFoundError:
            # Archivo no encontrado
        raise FileNotFoundError("No se encontró el archivo CSV. Por favor, asegúrate de que el archivo CSV esté en la ubicación especificada.")
    except pd.errors.ParserError:
            # Error al analizar el archivo CSV
        raise ValueError("Error al leer el archivo CSV. Por favor, asegúrate de que el archivo CSV esté formateado correctamente.")
    except KeyError as e:
            # Columnas necesarias ausentes en el CSV
        raise ValueError(str(e)) # Transformar KeyError en ValueError con mensaje específico

def padre(csv_file_path):
    try:
        # Establecimientos
        establecimientos = ['HUAHUARI', 'RIO NEGRO', 'VILLA CAPIRI', 'RIO CHARI ALTO', 'PITOCUNA', 'PUENTE IPOKI', 
                            'ALTO PITOCUNA', 'CUSHIVIANI', 'UNION CUBIRIAKI', 'SHABASHIPANGO', 'SAN JUA CHENI', 
                            'UNION CAPIRI', 'MIGUEL GRAU', 'ALTO VILLA VICTORIA']

        # Leer el archivo CSV
        df = pd.read_csv(csv_file_path, sep=';')

        # Verificar si las columnas necesarias están presentes
        required_columns = ['52','32', '55', '53', '54','5']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            missing_columns_str = ', '.join(missing_columns)
            raise ValueError(f"Columnas CSV incorrectas, Vuelve a cargar")

        # Renombrar las columnas
        nuevos_nombres = {
            '52': 'dniPadre', 
            '32': 'idEstablecimiento',
            '55': 'nombresPadre',
            '53': 'apellidoPaterno_Padre',
            '54': 'apellidoMaterno_Padre',
            '5': 'idMenor',
        }
        df = df.rename(columns=nuevos_nombres)

        # Verificar si la columna 'idEstablecimiento' está presente después del renombrado
        if 'idEstablecimiento' not in df.columns:
            raise ValueError("La columna 'idEstablecimiento' no se encontró después del renombrado.")

        # Crear un diccionario que mapee los establecimientos a sus índices en el array
        mapeo_establecimientos = {establecimiento: indice + 1 for indice, establecimiento in enumerate(establecimientos)}
        
        # Filtrar el DataFrame para mostrar solo las filas donde el valor en la columna 'idEstablecimiento' coincida con los establecimientos del array 'establecimientos'
        df_filtrado = df[df['idEstablecimiento'].isin(establecimientos)].copy()

        # Reemplazar los valores en la columna 'idEstablecimiento' con los índices correspondientes del array 'establecimientos'
        df_filtrado.loc[:, 'idEstablecimiento'] = df_filtrado['idEstablecimiento'].map(mapeo_establecimientos).fillna(df_filtrado['idEstablecimiento'])

        # Seleccionar las columnas adicionales que deseas agregar
        columnas_adicionales = ['dniPadre', 'nombresPadre', 'apellidoPaterno_Padre', 'apellidoMaterno_Padre','idMenor']

        # Agregar las columnas adicionales al DataFrame filtrado
        df_filtrado = df_filtrado[columnas_adicionales]

        # Llenar la columna 'tipoDocumento' con el índice de fila si hay valores nulos en alguna fila
        for index, row in df_filtrado.iterrows():
            id_menor = row['idMenor']
            if pd.isnull(id_menor) or id_menor == '':
                df_filtrado.at[index, 'idMenor'] = f"Falta Actualizar ({index})"

        return df_filtrado
    except FileNotFoundError:
            # Archivo no encontrado
        raise FileNotFoundError("No se encontró el archivo CSV. Por favor, asegúrate de que el archivo CSV esté en la ubicación especificada.")
    except pd.errors.ParserError:
            # Error al analizar el archivo CSV
        raise ValueError("Error al leer el archivo CSV. Por favor, asegúrate de que el archivo CSV esté formateado correctamente.")
    except KeyError as e:
            # Columnas necesarias ausentes en el CSV
        raise ValueError(str(e)) # Transformar KeyError en ValueError con mensaje específico

@app.route('/mostrarPadres', methods=['POST','GET'])
def Menor_Hemoglobina():
    niño_id = request.form['niño_id']
    database = get_database_connection()
    cursor = database.cursor()

    # Consulta a la tabla madre
    query_madre = """
    SELECT dniMadre, nombresMadre, apellidoPaterno_Madre, apellidomaterno_Madre, celularMadre 
    FROM madre 
    WHERE idMenor = %s
    """
    cursor.execute(query_madre, (niño_id,))
    rows_madre = cursor.fetchall()

    # Consulta a la tabla padre
    query_padre = """
    SELECT dniPadre, nombresPadre, apellidoPaterno_Padre, apellidomaterno_Padre 
    FROM padre 
    WHERE idMenor = %s
    """
    cursor.execute(query_padre, (niño_id,))
    rows_padre = cursor.fetchall()

    cursor.close()

    # Convertir resultados a JSON
    reporteHemo_json = {
        "madre": [],
        "padre": []
    }
    
    for row in rows_madre:
        dic_madre = {
            'dniMadre': row[0],
            'nombresMadre': row[1],
            'apellidoPaterno_Madre': row[2],
            'apellidomaterno_Madre': row[3],
            'celularMadre': row[4]
        }
        reporteHemo_json["madre"].append(dic_madre)
    
    for row in rows_padre:
        dic_padre = {
            'dniPadre': row[0],
            'nombresPadre': row[1],
            'apellidoPaterno_Padre': row[2],
            'apellidomaterno_Padre': row[3]
        }
        reporteHemo_json["padre"].append(dic_padre)
        
    return jsonify({"datos": reporteHemo_json})

# def Menor_Hemoglobina_proceso(csv_file_path):
#     # Establecimientos
#     establecimientos = ['VILLA CAPIRI', 'RIO CHARI ALTO', 'P.S. PITOCUNA', 'P.S. PTE IPOKI', 
#                     'P.S. ALTO PITOCUNA', 'P.S. CUSHIVIANI', 'P.S. UNION CUVIRIAKI', 'P.S. SHABASHIPANGO', 
#                     'P.S. S.J. DE CHENI','P.S. UNION CAPIRI', 'P.S. MIGUEL GRAU', 'RESUMEN ']

#     hojas_excel = pd.ExcelFile(csv_file_path).sheet_names
    

#     dict_dataframes = pd.read_csv(csv_file_path, sheet_name=[hoja for hoja in establecimientos])

#     if 'RESUMEN ' in dict_dataframes:
#         resumen_dataframe = dict_dataframes['RESUMEN ']
#         falta = ['HUAHUARI', 'RIO NEGRO', 'ALTO VILLA VICTORIA']
#         resumen_dataframe.columns.values[1] = 'esta'
#         resumen_dataframe.columns.values[4] = 'nada1'
#         resumen_dataframe.columns.values[5] = 'Unnamed: 4'
#         resumen_dataframe.columns.values[2] = 'nada'
#         resumen_dataframe.columns.values[3] = 'Unnamed: 2'
#         filtrado = resumen_dataframe.loc[resumen_dataframe['esta'].isin(falta), 'esta']

#         # Guardar el DataFrame actualizado si es necesario
#         resumen_dataframe = resumen_dataframe[resumen_dataframe['esta'].isin(falta)]
#         dict_dataframes['RESUMEN '] = resumen_dataframe

#         # Selecciona las columnas que deseas conservar en cada hoja
#     columnas_deseadas = ['Unnamed: 2', 'Unnamed: 4', 'Unnamed: 7','Unnamed: 8', 'Unnamed: 9','Unnamed: 10', 'Unnamed: 12','Unnamed: 13', 'Unnamed: 16','Unnamed: 17']

#     # Almacena las hojas que no contienen las columnas deseadas
#     hojas_sin_columnas_deseadas = []

#     # Almacena las filas que comienzan con "DNI"
#     contador = 1
#     # Une todas las hojas en un solo DataFrame y conserva solo las columnas deseadas
#     merged_dfs = []
#     for nombre_hoja, df in dict_dataframes.items():
#             if nombre_hoja in establecimientos and all(col in df.columns for col in columnas_deseadas):
#                 # Filtrar las filas que comienzan con "DNI"
#                 df_sin_dni = df[~df[columnas_deseadas[0]].astype(str).str.startswith('DNI')]
#                 df_sin_dni = df_sin_dni[columnas_deseadas].reset_index(drop=True)
                
#                 # Agregar la columna 'num' que enumera las filas que contienen datos
#                 filas_con_datos = df_sin_dni.notnull().any(axis=1)
#                 df_sin_dni = df_sin_dni[filas_con_datos]
#                 df_sin_dni.insert(0, 'num', range(contador, contador + len(df_sin_dni)))
                
#                 # Renombrar las columnas
#                 df_sin_dni.columns = ['idReporteHG', 'idMenor', 'grupoEdad', 'HG1','fecha1', 'HG2','fecha2', 'HG3','fecha3','fecha4', 'HG4']
                
#                 contador += len(df_sin_dni)  # Actualizar el contador
#                 merged_dfs.append(df_sin_dni)
#             else:
#                 hojas_sin_columnas_deseadas.append(nombre_hoja)

#     # Verifica si hay hojas sin las columnas deseadas
#     if hojas_sin_columnas_deseadas:
#         print("Las siguientes hojas no contienen todas las columnas deseadas:")
#         for hoja in hojas_sin_columnas_deseadas:
#             print(hoja)

#     # Concatena los DataFrames si hay al menos uno para concatenar
#     if merged_dfs:
#         merged_df = pd.concat(merged_dfs)

#         # Crea un archivo temporal para guardar el CSV
#         temp_dir = tempfile.gettempdir()
#         csv_filename = 'Reporte_hemoglobina.csv'
#         csv_file_path = os.path.join(temp_dir, csv_filename)
#     else:
#         print("No se encontraron hojas con todas las columnas deseadas.")

    

#     return merged_df

#lamzar la 
if __name__ == '__main__':
    app.run(debug=True, port=3939)




        # df = pd.read_csv(io.StringIO(csv_data), sep=';', header=0)

                # if not isinstance(df, pd.DataFrame):
                #     raise ValueError("La conversión a DataFrame falló")
                # else:
                #     print("Fue exitoso!!!!!!!!!!!!!!!!")

                
                # registros_hg = [tuple(row) for row in df.values]

                # database = get_database_connection()
                # cursor = database.cursor()

                # # Obtener los idMenor existentes en la tabla niños
                # cursor.execute("SELECT tipoDocumento FROM niños")
                # id_menor_existentes = set(row[0] for row in cursor.fetchall())

                # # Filtrar registros_hg para incluir solo aquellos cuyo idMenor exista en la tabla niños
                # registros_hg_validos = [registro for registro in registros_hg if registro[1] in id_menor_existentes]

                # if registros_hg_validos:
                #     cursor.execute("SELECT COUNT(*) FROM reportehemoglobina")
                #     result = cursor.fetchone()
                #     num_rows = result[0]
                    
                #     if num_rows == 0:
                #         insert_query_hg = """
                #             INSERT INTO reportehemoglobina 
                #             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                #         """
                #         cursor.executemany(insert_query_hg, registros_hg_validos)
                    
                #     database.commit()

                # cursor.close()
                # database.close()