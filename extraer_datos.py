"""Pre-entrega 4: extracción reproducible de datos desde una API pública.

Requiere requests y python-dotenv. La API elegida no necesita credenciales.
"""

import csv
import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
CAMPOS_CSV = ("id_publicacion", "id_usuario", "titulo", "palabras_titulo")


def cargar_configuracion():
    """Lee la configuración de .env sin exponer posibles secretos."""
    load_dotenv(BASE_DIR / ".env")

    url = os.getenv("API_URL", "https://jsonplaceholder.typicode.com/posts").strip()
    limite = int(os.getenv("API_LIMIT", "10"))
    timeout = float(os.getenv("TIMEOUT_SEGUNDOS", "15"))
    ruta_salida = os.getenv("ARCHIVO_SALIDA", "data_extracted.csv").strip()

    if not url.startswith("https://"):
        raise ValueError("API_URL debe comenzar con https://")
    if limite < 1 or limite > 100:
        raise ValueError("API_LIMIT debe estar entre 1 y 100")
    if timeout <= 0:
        raise ValueError("TIMEOUT_SEGUNDOS debe ser mayor que cero")
    if not ruta_salida.lower().endswith(".csv"):
        raise ValueError("ARCHIVO_SALIDA debe terminar en .csv")

    ruta_archivo = Path(ruta_salida)
    if not ruta_archivo.is_absolute():
        ruta_archivo = BASE_DIR / ruta_archivo
    return url, limite, timeout, ruta_archivo


def extraer_publicaciones(url, limite, timeout):
    """Ejecuta un GET con timeout, valida el HTTP y decodifica el JSON."""
    respuesta = requests.get(
        url,
        params={"_limit": limite},
        timeout=timeout,
        headers={"Accept": "application/json"},
    )
    respuesta.raise_for_status()  # Errores HTTP: 404, 500, etc.
    datos = respuesta.json()
    if not isinstance(datos, list) or not datos:
        raise ValueError("La API no devolvió una lista de publicaciones con datos")
    return datos


def transformar_publicaciones(publicaciones):
    """Conserva campos útiles y deriva la longitud de cada título."""
    resultado = []
    for posicion, publicacion in enumerate(publicaciones, start=1):
        if not isinstance(publicacion, dict):
            raise ValueError(f"Publicación {posicion}: se esperaba un objeto JSON")
        try:
            id_publicacion = int(publicacion["id"])
            id_usuario = int(publicacion["userId"])
            titulo = str(publicacion["title"]).strip()
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Publicación {posicion}: datos faltantes o inválidos") from error
        if id_publicacion < 1 or id_usuario < 1 or not titulo or titulo.lower() == "none":
            raise ValueError(f"Publicación {posicion}: identificadores o título inválidos")
        resultado.append(
            {
                "id_publicacion": id_publicacion,
                "id_usuario": id_usuario,
                "titulo": titulo,
                "palabras_titulo": len(titulo.split()),
            }
        )
    return resultado


def guardar_csv(registros, destino):
    """Escribe UTF-8 y reemplaza el archivo solo al completar la escritura."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", delete=False,
            suffix=".tmp", dir=destino.parent,
        ) as archivo:
            temporal = Path(archivo.name)
            escritor = csv.DictWriter(archivo, fieldnames=CAMPOS_CSV)
            escritor.writeheader()
            escritor.writerows(registros)
        temporal.replace(destino)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def main():
    try:
        url, limite, timeout, salida = cargar_configuracion()
        datos = extraer_publicaciones(url, limite, timeout)
        registros = transformar_publicaciones(datos)
        guardar_csv(registros, salida)
    except requests.exceptions.HTTPError as error:
        print(f"Error HTTP al consultar la API: {error}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as error:
        print(f"Error de conexión o tiempo de espera: {error}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        print(f"Error de configuración o procesamiento: {error}", file=sys.stderr)
        return 1

    print(f"Extracción completada: {len(registros)} registros.")
    print(f"Archivo guardado en: {salida}")
    print(f"Columnas: {', '.join(CAMPOS_CSV)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
