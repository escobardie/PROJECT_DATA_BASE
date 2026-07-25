"""
Funciones relacionadas con datos geográficos.
"""

import json
from pathlib import Path


_DATA = None


def _load_data():
    """
    Carga el archivo argentina.json.
    """
    global _DATA

    if _DATA is None:
        file_path = (
            Path(__file__).resolve().parent
            / "data"
            / "argentina.json"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            _DATA = json.load(file)

    return _DATA


def get_provincias():
    """
    Retorna la lista de provincias.
    """
    data = _load_data()

    return [
        provincia["nombre"]
        for provincia in data["provincias"]
    ]


def get_ciudades(provincia_nombre: str):
    """
    Retorna las ciudades de una provincia.
    """
    data = _load_data()

    for provincia in data["provincias"]:
        if provincia["nombre"] == provincia_nombre:
            return provincia["ciudades"]

    return []

def get_provincias_choices():
    """
    Retorna provincias listas para Django Forms.
    """
    provincias = get_provincias()

    return [
        (provincia, provincia)
        for provincia in provincias
    ]

def get_ciudades_choices(provincia_nombre):
    """
    Retorna ciudades listas para Django Forms.
    """

    ciudades = get_ciudades(provincia_nombre)

    return [
        (ciudad, ciudad)
        for ciudad in ciudades
    ]