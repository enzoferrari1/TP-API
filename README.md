[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/enzoferrari1/TP-API/blob/master/README.en.md)


# Trabajo Práctico - Redes de Datos
Trabajo final de la materia Redes de datos

### Hecho con
- Phyton
  - FastAPI
  - uvicorn

## Descripción
Este trabajo se concentra en la creación de una API. Contempla la obtención de la fuente y el método de adquisición de los datos, el desarrollo del cliente y cómo se facilita el acceso para el usuario. Esto último está también ligado a asegurar la conexión entre el cliente y el usuario en una red local.

La cátedra pretende que usemos al menos dos de los métodos PUSH, POST, GET y DELETE.

## Motivación
El trabajo propuesto por el alumno consiste en una API enfocada en la consulta de gasto público estadounidense y gestor de acciones para que el usuario pueda tomar desiciones basado en la información generada. 

Brinda al usuario con las siguientes funcionalidades:
- Consultar cuáles fueron los recipientes a los cuales se les fue otorgados la mayor cantidad de dinero en un lapso de tiempo dado y permitir visualizarlos adecuadamente.
- Con la información brindada en el punto anterior, agregar acciones en un 'staging area' acompañadas de indicadores estadísticos.
- Consultar y borrar acciones de dicho staging area.

## APIs consultadas
- https://api.usaspending.gov/api/v2/search/spending_by_category/recipientusaspending.gov

Información respecto al gasto público estadounidense. Ofrece una API para consultar los datos. Es de interés saber, dado un lapso de tiempo, cuáles fueron los recipientes que más fondos recibieron del gobierno.

- https://www.alphavantage.co/query?function=OVERVIEW&symbol=GOOG&apikey=WEZ4MINFUGJQPQK2

De aquí se obtienen los detalles de cada acción ajenos a la cotización, que no pudo ser obtenida de aquí debido a que no estaba a tiempo real. Para esto debemos usar otra API.

- https://financialmodelingprep.com/api/v3/quote-short/GOOG,TSLA?apikey=8f88ca39ce56acf3d5a9778cd9ccb4f6

Este endpoint nos muestra, dado un array de nombres de acciones, la cotización de estas al momento de ser consultadas. 

## Endpoints
Breve descripción de cada endpoint creado, para más información, visitar documentación generada por swagger.
- **PUT** - /informe/crear :

Crear informe de gastos del gobierno de EEUU según recipiente, ordenados de mayor a menor monto, dado un lapso de tiempo.

Se vuelcan los recipientes sobre un archivo gastos.json

- **GET** - /informe/graficar/{top} :

Gráfico de barras que muestra los importes de cada recipiente generado por el informe.

top: cantidad de recipientes a graficar.

![image](https://github.com/enzoferrari1/TP-API/assets/109885056/45aced24-b566-4226-8cf6-147ca4ce74e6)


- **POST** - /staging/agregar-stocks :

Agrega stocks al staging area. Se ingresan fecha de agregado, nombre de acción y monto invertido por el gobierno.

La API autocompleta indicadores estadísticos adicionales.

Ejemplo de body:
```
[
  {
    "fecha_agregado": "2023-08-17",
    "nombre_accion": "BAH",
    "monto_invertido_gobierno": 10000000
  },
  {
    "fecha_agregado": "2023-08-17",
    "nombre_accion": "GD",
    "monto_invertido_gobierno": 5000000
  }
]
```

- **GET** - /staging/consultar-stocks :

Muestra los stocks agregados guardados en el archivo JSON.

Ejemplo

|index|fecha\_agregado|nombre\_accion|cotizacion|monto\_invertido\_gobierno|capitalizacion\_empresa|relacion\_inversion-capitalizacion|price\_to\_earnings\_ratio|analyst\_target\_price|50\_day\_moving\_average|
|---|---|---|---|---|---|---|---|---|---|
|0|2023-08-17|BAH|117\.33|10000000|16003020000|0\.0006248821|30\.44|129\.55|113\.51|
|1|2023-08-17|BAH|117\.33|10000000|16003020000|0\.0006248821|30\.44|129\.55|113\.51|
|2|2023-08-17|GD|223\.865|5000000|61049684000|8\.19005e-05|18\.34|264\.37|217\.84|

- **DELETE** - /staging/borrar-stocks :

Borra stocks específicos del staging area, según nombre o fecha.

### Entorno del cliente
El programa fue ejecutado en un entorno Lubuntu 22.04.
Al comienzo del archivo *main.py* se indican las librerias a utilizar. Para ejecutar el programa se necesita el paquete uvicorn, usando el comando
```
uvicorn main:app --reload --host [ip]
```

### Entorno del usuario
El desarrollo de un programa para dar un acceso fácil al cliente puede ser una parte faltante de este trabajo.
Sin embargo, la documentación generada por swagger es suficiente para dar al usuario acceso a cada endpoint.

Para esto, el cliente debe acceder desde su motor de búsqueda preferido al enlace

http://127.0.0.1:8000/docs

Reemplazar la ip de loopback y el puerto en caso de ser necesario. Allí se encontrará la documentación de cada endpoint.
