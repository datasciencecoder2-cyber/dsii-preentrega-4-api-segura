"""Tests sin red: simulamos la respuesta del servicio y casos de fallo."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from extraer_datos import (
    extraer_publicaciones,
    guardar_csv,
    transformar_publicaciones,
    main,
)


class RespuestaSimulada:
    def __init__(self, datos, estado=200):
        self.datos = datos
        self.status_code = estado

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.datos


class PruebasExtraccion(unittest.TestCase):
    def setUp(self):
        self.datos = [
            {"userId": 1, "id": 1, "title": "Un titulo de prueba", "body": "No se exporta"},
            {"userId": 2, "id": 2, "title": "Otro titulo", "body": "No se exporta"},
        ]

    @patch("extraer_datos.requests.get")
    def test_get_exitoso_y_parametros(self, get_simulado):
        get_simulado.return_value = RespuestaSimulada(self.datos)
        resultado = extraer_publicaciones("https://ejemplo.org/posts", 2, 10)
        self.assertEqual(len(resultado), 2)
        get_simulado.assert_called_once_with(
            "https://ejemplo.org/posts",
            params={"_limit": 2},
            timeout=10,
            headers={"Accept": "application/json"},
        )

    def test_transformacion_elimina_campos_innecesarios(self):
        filas = transformar_publicaciones(self.datos)
        self.assertEqual(filas[0], {
            "id_publicacion": 1, "id_usuario": 1,
            "titulo": "Un titulo de prueba", "palabras_titulo": 4,
        })
        self.assertNotIn("body", filas[0])

    def test_guardado_csv_y_relectura(self):
        with tempfile.TemporaryDirectory() as carpeta:
            salida = Path(carpeta) / "data_extracted.csv"
            guardar_csv(transformar_publicaciones(self.datos), salida)
            with salida.open(encoding="utf-8", newline="") as archivo:
                filas = list(csv.DictReader(archivo))
            self.assertEqual(len(filas), 2)
            self.assertEqual(filas[1]["id_publicacion"], "2")

    @patch("extraer_datos.requests.get")
    def test_http_404_y_500(self, get_simulado):
        for estado in (404, 500):
            with self.subTest(estado=estado):
                get_simulado.return_value = RespuestaSimulada([], estado)
                with self.assertRaises(requests.exceptions.HTTPError):
                    extraer_publicaciones("https://ejemplo.org/posts", 2, 10)

    @patch("extraer_datos.requests.get")
    def test_error_de_red(self, get_simulado):
        get_simulado.side_effect = requests.exceptions.Timeout("No responde")
        with self.assertRaises(requests.exceptions.RequestException):
            extraer_publicaciones("https://ejemplo.org/posts", 2, 10)

    def test_json_vacio_e_incorrecto(self):
        for datos in ([], None, {"id": 1}):
            with self.subTest(datos=datos):
                with patch("extraer_datos.requests.get", return_value=RespuestaSimulada(datos)):
                    with self.assertRaises(ValueError):
                        extraer_publicaciones("https://ejemplo.org/posts", 2, 10)

    def test_faltan_campos(self):
        with self.assertRaises(ValueError):
            transformar_publicaciones([{"id": 1, "title": "Falta usuario"}])

    @patch("extraer_datos.cargar_configuracion")
    @patch("extraer_datos.requests.get")
    def test_flujo_completo_desde_get_hasta_csv(self, get_simulado, config_simulada):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "data_extracted.csv"
            config_simulada.return_value = ("https://ejemplo.org/posts", 2, 10, destino)
            get_simulado.return_value = RespuestaSimulada(self.datos)
            self.assertEqual(main(), 0)
            with destino.open(encoding="utf-8", newline="") as archivo:
                self.assertEqual(len(list(csv.DictReader(archivo))), 2)

    @patch("extraer_datos.cargar_configuracion")
    @patch("extraer_datos.requests.get")
    def test_no_sobrescribir_salida_si_get_falla(self, get_simulado, config_simulada):
        with tempfile.TemporaryDirectory() as carpeta:
            destino = Path(carpeta) / "data_extracted.csv"
            destino.write_text("contenido anterior", encoding="utf-8")
            config_simulada.return_value = ("https://ejemplo.org/posts", 2, 10, destino)
            get_simulado.return_value = RespuestaSimulada([], 500)
            self.assertEqual(main(), 1)
            self.assertEqual(destino.read_text(encoding="utf-8"), "contenido anterior")


if __name__ == "__main__":
    unittest.main()
