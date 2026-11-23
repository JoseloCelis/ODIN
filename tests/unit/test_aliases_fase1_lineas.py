"""Contrato de los alias públicos de la fase 1 de líneas (etapas ⑩ y ⑪).

AGENTS.md §4: los algoritmos se consumen por el alias del dominio, no
importando el archivo del modelo desde fuera del paquete. Este test fija
esa superficie para que T3 no se rompa en silencio.
"""

from __future__ import annotations

import dataclasses

from src.odin import bootstrap


def test_procesamiento_expone_hough_de_lineas() -> None:
    """La etapa ⑩ se consume desde `odin.Procesamiento`, no desde el modelo."""
    from src.odin.Procesamiento import (
        CandidatasLineas,
        candidatas_lineas,
        hough_lineas,
        reducir_candidatas,
    )

    assert callable(hough_lineas)
    assert callable(candidatas_lineas)
    assert callable(reducir_candidatas)
    assert dataclasses.is_dataclass(CandidatasLineas)


def test_ajustes_expone_ajuste_de_recta() -> None:
    """La etapa ⑪ se consume desde `odin.Ajustes`, no desde el modelo."""
    from src.odin.Ajustes import (
        dist_p_recta,
        euc_space,
        linea1,
        linea_mc,
        linea_robusta,
        medir_trazo,
        separar_orillas,
        MedicionTrazo,
    )

    exponibles = (linea_robusta, linea1, dist_p_recta, euc_space, linea_mc, medir_trazo, separar_orillas, MedicionTrazo)
    assert all(callable(funcion) for funcion in exponibles if funcion is not MedicionTrazo)
    assert callable(MedicionTrazo)


def test_bootstrap_registra_las_etapas_nuevas() -> None:
    """Las dos etapas nuevas entran en el registro de carga ordenada del arranque."""
    rutas = [ruta for _alias, ruta in bootstrap.PREPROCESAMIENTO_SUITE_ORDER]

    assert "odin.Procesamiento.models.hough_lineas" in rutas
    assert "odin.Ajustes.models.linea_robusta" in rutas
