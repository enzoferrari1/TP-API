from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import matplotlib.pyplot as plt
import requests
import pandas as pd
import json
import time
import io

# Nombre del directorio donde se encuentra el proyecto


app = FastAPI()

# Declaramos una clase para manejar el payload enviado por el cliente
# De esta manera la documentación de swagger manejará mejor el formato de los payloads
# Para el PUT

class ClientRequest(BaseModel):
  fecha_actual: str = Field(default = str(datetime.now().date().strftime('%Y-%m-%d')))
  lapso_dias: int = Field(default = 30)
  paginas: int = Field(default = 1)

# Para el POST

class StockNode(BaseModel):
  fecha_agregado: str
  nombre_accion: str
  monto_invertido_gobierno: float


@app.put("/informe/crear")
async def crear_informe(client_request: ClientRequest):
  '''
  Crear informe de gastos del gobierno de EEUU según recipiente, ordenados de mayor a menor monto, dado un lapso de tiempo.
  
  Se vuelcan los recipientes sobre un archivo gastos.json
  
  PUT
  
  Body
  
  {
  
    'fecha_actual' : '2023-06-29',
    
    'lapso_dias' : 30,
    
    'paginas' : 1
    
  }
  
  fecha_actual: str (datetime, %Y-%m-%d) Fecha final desde la cual se toman las transacciones sobre los recipientes. Default: fecha actual.
  
  laspo_dias: int Cuántos días atras se toman desde la fecha actual. Default: 30.
  
  paginas: int cantidad de recipientes que se generan, cada página registra 100 recipientes. Default: 1.
  
  '''
  # Desempaquetamos el payload del cliente
  fecha_actual_str = client_request.fecha_actual
  lapso_dias = client_request.lapso_dias
  paginas = client_request.paginas

  # Obtenemos la fecha inicial
  fecha_actual = datetime.strptime(fecha_actual_str, '%Y-%m-%d').date()
  fecha_inicio = fecha_actual - timedelta(days=lapso_dias)
  fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')

  url = 'https://api.usaspending.gov/api/v2/search/spending_by_category/recipient'
  payload =  {
        "filters": {
            "time_period": [
                {
                    "start_date": fecha_inicio_str,
                    "end_date": fecha_actual_str
                }
            ],
        'recipient_type_names': ['category_business', 'corporate_entity_not_tax_exempt']
        },
        "category": "recipient",
        'limit':100
    }

  # Iterar respecto de las páginas:
  # Cada página agrega 100 registros
  page_limit = paginas

  data = pd.DataFrame()

  for n in range(1, page_limit+1):
    payload['page'] = n
    response = requests.post(url, json=payload)
    try:
      json_response = response.json()
    except ValueError:
      return 'Error en la página ' + str(n)
    page_data = pd.DataFrame(json_response['results'])
    data = pd.concat([data, page_data], ignore_index=True)
    time.sleep(0.1)

  # Guardar el json generado
  data.to_json('/home/enzo/Documents/API/gastos.json', orient='records')

  return {'Mensaje':'datos.json ha sido exitosamente creado'}

@app.get('/informe/graficar/{top}')
async def graficar_informe(top: int = 20):
  '''
  Gráfico de barras que muestra los importes de cada recipiente generado por el informe \n
  GET \n
  top: cantidad de recipientes a graficar.
  '''
  try:
    data = pd.read_json('/home/enzo/Documents/API/gastos.json')
  except FileNotFoundError:
    return {"Mensaje": "No ha sido creado el informe, por favor, cree uno primero"}
  data_top = data.groupby(['name']).sum().sort_values('amount', ascending=False).head(top)['amount']
  data_top.plot(kind='barh')
  plt.xlabel('Monto (Dólares)')
  plt.ylabel('Recipiente')
  plt.title('Monto cedido por el gobierno según recipiente')
  plt.tight_layout()

  # Guardar el plot en un buffer de memoria
  image_buffer = io.BytesIO()
  plt.savefig(image_buffer, format='png')
  image_buffer.seek(0)

  return StreamingResponse(image_buffer, media_type='image/png')

@app.post('/staging/agregar-stocks')
async def agregar_stocks(stock_payload: List[StockNode]):
  '''
  Agrega stocks al staging area. Se ingresan fecha de agregado, nombre de acción y monto invertido por el gobierno

  fecha_agregado: str (datetime, %Y-%m-%d)

  nombre_accion: str

  monto_invertido_gobierno: float
  '''
  columns = ['fecha_agregado',
           'nombre_accion',
           'cotizacion',
           'monto_invertido_gobierno',
           'capitalizacion_empresa',
           'relacion_inversion-capitalizacion',
           'price_to_earnings_ratio',
           'analyst_target_price',
           '50_day_moving_average']
  staging_area = pd.DataFrame(columns=columns)
  # Primero, solicitamos la cotización de las acciones ingresadas mediante la API de FinancialModeling Prep
  # Esta nos brinda un único json donde cada registro detalla el precio de la acción para cada acción ingresada
  stock_list = [data.nombre_accion for data in stock_payload]
  stock_list_string = ','.join(stock_list)
  price_url = 'https://financialmodelingprep.com/api/v3/quote-short/' + stock_list_string + '?apikey=8f88ca39ce56acf3d5a9778cd9ccb4f6'
  response_price = requests.get(price_url)
  try:
    json_price = json.loads(response_price.content)
    dict_price = {registro['symbol']: registro for registro in json_price}
  except ValueError:
    print('Error solicitando precio de acciones')
  except TypeError:
    return 'Error en el nombre de las acciones. Por favor revise que sean válidas'

  # Creamos ahora un diccionario para acceder fácilmente a los precios de las acciones


  # Ahora, por cada acción pedimos la información en AlphaVantage
  for register in stock_payload:
    # Inicializamos la nueva fila como un diccionario y agregamos los datos dados por el usuario
    nueva_fila = {}
    nueva_fila['fecha_agregado'] = register.fecha_agregado
    nueva_fila['nombre_accion'] = register.nombre_accion
    nueva_fila['monto_invertido_gobierno'] = register.monto_invertido_gobierno
    try:
      nueva_fila['cotizacion'] = dict_price[register.nombre_accion]['price']
    except KeyError:
      pass

    # Buscamos la información de la acción en Alpha Vantage
    info_url = 'https://www.alphavantage.co/query?function=OVERVIEW&symbol=' + register.nombre_accion + '&apikey=WEZ4MINFUGJQPQK2'
    response_info = requests.get(info_url)
    try:
      json_info = response_info.json()
    except ValueError:
      print('Error solicitando información de ' + register.nombre_accion)
    if not json_info:
      continue
    nueva_fila['capitalizacion_empresa'] = json_info['MarketCapitalization']
    try:
      nueva_fila['relacion_inversion-capitalizacion'] = float(nueva_fila['monto_invertido_gobierno']) / float(json_info['MarketCapitalization'])
    except KeyError:
      pass
    except ZeroDivisionError:
      pass
    nueva_fila['price_to_earnings_ratio'] = json_info['PERatio']
    nueva_fila['analyst_target_price'] = json_info['AnalystTargetPrice']
    nueva_fila['50_day_moving_average'] = json_info['50DayMovingAverage']
    staging_area = pd.concat([staging_area, pd.DataFrame([nueva_fila])], ignore_index = True)

    # Agregamos las acciones al viejo staging area
    try:
      old_staging_area = pd.read_json('/home/enzo/Documents/API/staging.json')
      staging_area = pd.concat([old_staging_area, staging_area], ignore_index = True)
    except FileNotFoundError:
      pass
    staging_area.to_json('/home/enzo/Documents/API/staging.json', orient='records')

  return {'Mensaje': 'Las acciones han sido agregadas al staging area'}

@app.get('/staging/consultar-stocks')
async def mostrar_stocks():
  '''
  Muestra los stocks agregados guardados en el archivo JSON.

  '''
  try:
    staging_area = pd.read_json('/home/enzo/Documents/API/staging.json')
  except FileNotFoundError:
    return {"Mensaje": "El staging area no ha sido creado aún"}
  return staging_area.to_json(orient='records')

@app.delete('/staging/borrar-stocks')
async def borrar_stocks(accion: str = "", fecha: str = ""):
  '''
  Borra stocks del staging area

  DELETE

  accion: str. Acciones a remover

  fecha: str, datetime %Y-%m-%d. Día a remover

  Si solo se da accion, borra todas esas acciones.

  Si solo se da fecha, se borran todas las acciones de esa fecha
  
  Si no se da ninguna, borra todo.
  '''
  try:
    staging_area = pd.read_json('/home/enzo/Documents/API/staging.json')
  except FileNotFoundError:
    return {"Mensaje": "No existe staging area. Cree una primero"}
  if accion == "" and fecha == "":
    pd.DataFrame().to_json('/home/enzo/Documents/API/staging.json',orient='records')
    return {"Mensaje": "Se han borrado todos los stocks"}
  if fecha == "":
    filtered_staging_area = staging_area[(staging_area['nombre_accion'] != accion)]
    filtered_staging_area.to_json('/home/enzo/Documents/API/staging.json', orient='records')
    return {"Mensaje": "Se han borrado todos los stocks de " + accion}
  if accion == "":
    filtered_staging_area = staging_area[(staging_area['fecha_agregado'] != fecha)]
    filtered_staging_area.to_json('/home/enzo/Documents/API/staging.json', orient='records')
    return {"Mensaje": "Se han borrado todos los stocks del día " + fecha}
  else:
    filtered_staging_area = staging_area[((staging_area['nombre_accion'] != accion) & (staging_area['fecha_agregado'] != fecha))]
    filtered_staging_area.to_json('/home/enzo/Documents/API/staging.json', orient='records')
    return {"Mensaje": "Se han borrado los stocks de " + accion + " del día " + fecha}

