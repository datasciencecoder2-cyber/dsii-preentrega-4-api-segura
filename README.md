# Data Science II · Pre-entrega 4

## Extracción y almacenamiento seguro de datos vía API

**Objetivo.** Consultar una API pública mediante HTTP GET, procesar su respuesta JSON y guardar datos estructurados en CSV. El proyecto documenta la configuración con variables de entorno, la prevención de publicación de credenciales y el tratamiento de errores.

### Fuente de datos

- **Servicio:** [JSONPlaceholder](https://jsonplaceholder.typicode.com/), API REST pública para prácticas.
- **Recurso:** [`GET /posts`](https://jsonplaceholder.typicode.com/posts), limitado a 10 publicaciones (`_limit=10`).
- **Autenticación:** no requiere clave. Se utiliza `.env` **para la configuración**; si se trabajara con una API con claves, estas irían allí y no en el código.

### Estructura del repositorio

```text
├── extraer_datos.py           # GET, validaciones, transformación y CSV
├── data_extracted.csv         # Salida estructurada de 10 publicaciones
├── requirements.txt          # Dependencias
├── .env.example              # Plantilla de variables, sin secretos
├── .gitignore                # Excluye .env, cachés y entornos
├── tests/
│   └── test_extraer_datos.py  # Pruebas offline de éxito y errores
└── README.md                 # Instrucciones y justificación
```

### Requisitos e instalación

Python 3.10 o superior. Abrir una terminal en la carpeta del repositorio:

```bash
python -m venv .venv
```

Activar el entorno según el sistema operativo:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Luego instalar:

```bash
python -m pip install -r requirements.txt
```

### Configuración segura

Crear una copia local de `.env.example` llamada `.env` (en Windows PowerShell: `Copy-Item .env.example .env`; en Linux/macOS: `cp .env.example .env`). La plantilla contiene:

```ini
API_URL=https://jsonplaceholder.typicode.com/posts
API_LIMIT=10
TIMEOUT_SEGUNDOS=15
ARCHIVO_SALIDA=data_extracted.csv
```

El script utiliza `python-dotenv` (`load_dotenv`) para leer `.env`. El archivo **`.env` no se debe subir a GitHub**, por eso está en `.gitignore`; se comparte únicamente `.env.example`. JSONPlaceholder no necesita credenciales, por lo que **no se inventa ninguna API Key**.

### Ejecución y validación

```bash
python extraer_datos.py
python -m unittest discover -s tests -v
```

El primer comando solicita datos reales a la API, muestra un mensaje de éxito y **regenera** `data_extracted.csv`. Requiere conexión a Internet. El segundo ejecuta pruebas sin red, simulando respuestas para confirmar la lógica de petición, transformación y persistencia, además de errores 404, 500, timeout, estructura incorrecta y columnas faltantes.

### Transformación y salida

Se eliminó el texto largo del cuerpo (`body`) por no ser necesario para este ejercicio. Se conservan los campos `id` y `userId` como `id_publicacion` e `id_usuario`, más el `titulo` limpio. Se añade `palabras_titulo` como métrica derivada. El CSV usa UTF-8 y tiene este esquema:

| Campo | Tipo esperado | Origen / propósito |
|---|---|---|
| `id_publicacion` | Entero | `id` de la publicación |
| `id_usuario` | Entero | `userId` de autor |
| `titulo` | Texto | `title` de publicación |
| `palabras_titulo` | Entero | Recuento de palabras de `titulo` |

La escritura se realiza primero en un archivo temporal y luego se reemplaza el CSV; si el GET falla, no se sobrescribe la salida anterior.

### Seguridad, integridad y errores

- **Confidencialidad:** variables de configuración en `.env`, excluido de Git. No se muestran credenciales.
- **Transporte:** URL HTTPS.
- **Robustez:** timeout y `raise_for_status()` para respuestas HTTP 404/500.
- **Errores controlados:** tratamiento de fallos de red, JSON inesperado, campos faltantes, archivos y configuración inválida.
- **Integridad:** el CSV solo se reemplaza después de descargar, verificar y transformar la respuesta.

### Comprobaciones para corregir la práctica

1. Verificar `extraer_datos.py` y `.env.example`.
2. Revisar `data_extracted.csv` (10 registros más encabezado).
3. Seguir las instrucciones y ejecutar el script con Internet.
4. Ejecutar los tests con `unittest` y comprobar `OK`.

**Nota:** los registros publicados por JSONPlaceholder son ficticios y se utilizan únicamente con fines de aprendizaje, no representan personas reales ni datos confidenciales.
