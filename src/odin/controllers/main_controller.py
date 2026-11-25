"""Controlador principal de ODIN.

Orquestador de eventos y coordinación entre la vista y los módulos de
procesamiento. Contiene la lógica de negocio sin depender directamente de
widgets GTK.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
import numpy as np
from gi.repository import Gio, GLib, Gtk

from ..Procesamiento import EvidenciaGeometria, Geometria, clasificar_geometria
from ..Procesamiento import emparejar_orillas, asignar_puntos_a_orillas
from ..Procesamiento import seleccionar_trazo_por_intensidad
from ..Ajustes import medir_trazo
from .plan_geometria import (
    GEOMETRIA_POR_OPCION,
    ORIGEN_AUTOMATICO,
    PlanGeometria,
    plan_de_etapas,
    puntos_de_borde,
)

if TYPE_CHECKING:
    from odin.bootstrap import BootstrapResult
    from odin.views.main_window import OdinMainWindow


class EstadoDiametro:
    """Estado del campo de diámetro: lo detectado por el barrido vs lo que
    declaró el usuario.

    Mantener los dos valores separados evita el error sutil de R6.3: si el
    valor que precarga el barrido se tomara como un valor escrito a mano, la
    siguiente ejecución se volvería manual sin que nadie lo pidiera.
    """

    def __init__(self) -> None:
        self.detectado = None
        self.usuario = None
        self.ambiguo = False

    def registrar_detectado(self, diametro: float, ambiguo: bool = False) -> None:
        """Guarda lo que estimó el barrido. No cuenta como decisión del usuario."""
        self.detectado = float(diametro)
        self.ambiguo = bool(ambiguo)

    def declarar_usuario(self, diametro: float | None) -> float | None:
        """Marca un valor escrito a mano. `None` o <= 0 vuelve a automático."""
        if diametro is None or float(diametro) <= 0:
            self.usuario = None
        else:
            self.usuario = float(diametro)
        return self.usuario

    def volver_a_auto(self) -> None:
        self.usuario = None

    @property
    def es_manual(self) -> bool:
        return self.usuario is not None

    def diametro_para_procesar(self) -> float | None:
        return self.usuario

    def valor_visible(self) -> float:
        if self.es_manual:
            return self.usuario
        return self.detectado if self.detectado is not None else 0.0

    def texto_estado(self) -> str:
        if self.es_manual:
            return f"Manual: {self.usuario:.1f} px (se omite la estimación)"
        if self.detectado is None:
            return "Se estima al procesar"
        aviso = " · revisar: hay otro candidato parecido" if self.ambiguo else ""
        return f"Detectado: {self.detectado:.1f} px{aviso}"


def resolver_radio(diametro_usuario: float | None, bordes: np.ndarray, r0: float, aprox_hough: Any) -> tuple[float, int, float, str]:
    """Devuelve `(radio, pico, ambiguedad, origen)`.

    Un diámetro declarado por el usuario se usa tal cual y **omite** el
    barrido (spec hough-circles, R6.2). Sin diámetro, se estima en dos
    escalas (R3, R10).

    `aprox_hough` es el módulo `hough_circles` (cargado por el `ModuleLoader`
    del bootstrap bajo la clave `aproxHough`): se inyecta desde
    `bootstrap_result.modules.preprocesamiento` (spec odin-startup-structure)
    en lugar de que el controlador importe el módulo de algoritmo directamente.
    """
    if diametro_usuario is not None and float(diametro_usuario) > 0:
        return float(diametro_usuario) / 2.0, 0, 0.0, "usuario"

    radio, pico, ambiguedad = aprox_hough.estimar_radio_dominante(bordes, r0)
    return radio, pico, ambiguedad, "automatico"


class OdinController:
    """Orquestador de eventos de la ventana principal.

    Conecta las acciones de la UI con los módulos de procesamiento.
    No contiene lógica matemática ni renderizado de widgets.
    """

    def __init__(self, bootstrap_result: BootstrapResult, logger: Any, main_window: OdinMainWindow) -> None:
        self.bootstrap_result = bootstrap_result
        self.logger = logger
        self.main_window = main_window

        # Obtener módulos cargados vía bootstrap
        preproc = bootstrap_result.modules.preprocesamiento
        handle_mod = bootstrap_result.modules.handle

        # Asignar módulos como atributos para uso posterior
        self.kernelSeparable = preproc["kernelSeparable"]
        self.MagnitudGradiente = preproc["MagnitudGradiente"]
        self.NonMaxSup = preproc["NonMaxSup"]
        self.Otsu = preproc["Otsu"]
        self.DoubleTh = preproc["DoubleTh"]
        self.aproxHough = preproc["aproxHough"]
        self.circleFilter = preproc["circleFilter"]
        self.LSC = preproc["LSC"]
        self.HoughLineas = preproc["HoughLineas"]
        self.LineaRobusta = preproc["LineaRobusta"]
        self.handle = handle_mod

        # Variables de control
        self.ruta_imagen = None
        self.image_loaded = None
        self.estado_diametro = EstadoDiametro()
        self._actualizando_diametro = False
        # Selector de geometría (T5): `None` es automático.
        self.geometria_seleccionada: Geometria | None = None

        # Timing para WINDOW_INIT
        self._t0_window = None
        self.sigma = None

    def registrar_acciones(self) -> None:
        """Registra las acciones lógicas de la ventana."""
        self.logger.set_application_name("ODIN")

        action_cargar = Gio.SimpleAction.new("cargar_imagen", None)
        action_cargar.connect("activate", self.on_open_dialog)
        self.main_window.add_action(action_cargar)

        action_about = Gio.SimpleAction.new("about", None)
        action_about.connect("activate", self.show_about)
        self.add_action(action_about)

    def on_open_dialog(self, button: Gtk.Button | None, *args: Any) -> None:
        """Abre el diálogo de selección de archivo."""
        fileDialog = Gtk.FileDialog.new()
        fileDialog.set_title("Selecciona la imagen")

        home_dir = str(self.bootstrap_result.env.base_path)

        if not os.path.exists(home_dir):
            home_dir = str(Path.home())

        if os.path.exists(home_dir):
            folder = Gio.File.new_for_path(home_dir)
            fileDialog.set_initial_folder(folder)

        filtros = Gio.ListStore.new(Gtk.FileFilter)
        filtro_img = Gtk.FileFilter()
        filtro_img.set_name("Imágenes (bmp, tiff, jpeg)")
        filtro_img.add_mime_type("image/bmp")
        filtro_img.add_mime_type("image/tiff")
        filtro_img.add_mime_type("image/jpeg")
        filtros.append(filtro_img)
        fileDialog.set_filters(filtros)

        fileDialog.open(self.main_window, None, self.on_file_opened_callback)

    def on_file_opened_callback(self, dialog: Gtk.FileDialog, response: Gio.AsyncResult) -> None:
        try:
            file = dialog.open_finish(response)
            if file:
                self.ruta_imagen = file.get_path()
                print(f"Ruta del archivo: {file.get_path()}")
                is_error, message, self.image_loaded = self.handle.load_GrayImage(
                    self, self.ruta_imagen
                )
                self.main_window.image_loaded = self.image_loaded
                pixbuff = self.handle.matriz_a_pixbuf(self.image_loaded)
                self.main_window.mostrar_alerta("Mensaje Imagen", message, is_error)
                if hasattr(self.main_window.image_container, "cargar_imagen"):
                    self.main_window.image_container.cargar_imagen(pixbuff)
                else:
                    self.main_window.image_container.set_filename(
                        self.ruta_imagen
                    )
        except GLib.Error as error:
            print(f"Error al abrir el archivo: {error.message}")

    def on_process_clicked(self, button: Gtk.Button) -> None:
        if self.ruta_imagen:
            self.main_window.mostrar_alerta(
                "Procesando", "Iniciando el cálculo de bordes...", es_error=False
            )

            self.current_image = self.handle.recortar_imagen(self.main_window)
            if self.current_image is None:
                self.main_window.mostrar_alerta(
                    "Error", "No se pudo obtener la imagen para procesar.", es_error=True
                )
                return

            hilo_matematico = threading.Thread(
                target=self._tarea_pesada_computacional
            )
            hilo_matematico.start()

    def _tarea_pesada_computacional(self) -> None:
        """Ejecuta la matemática pesada en un hilo de fondo."""
        try:
            print("Hilo secundario: Iniciando convoluciones...")
            resultadosProcesamiento = {}
            resultadosProcesamiento["inicial"] = self.handle.matriz_a_pixbuf(
                self.current_image
            )
            Gx, Gy = self.kernelSeparable.DerivGauss(
                self.current_image, self.main_window.sigma
            )
            MG, Tetha = self.MagnitudGradiente.MagFase(Gx, Gy)
            GNMaxS = self.NonMaxSup.LinearInterpolation(MG, Gx, Gy, Tetha)
            uOtsu, _uRosin = self.Otsu.umbralRosinYOtsu(GNMaxS, histo=True)
            HighE, LowE = self.NonMaxSup.DobleThreshold(GNMaxS, uOtsu)
            DetectedEdges = self.DoubleTh.EdgeTrack_Hyst(HighE, LowE)
            print(
                f"Bordes: {np.sum(HighE > 0)} fuertes, "
                f"{np.sum(LowE > 0)} débiles, "
                f"{np.sum(DetectedEdges > 0)} tras histéresis"
            )

            resultadosProcesamiento["gx"] = self.handle.matriz_a_pixbuf(Gx)
            resultadosProcesamiento["gy"] = self.handle.matriz_a_pixbuf(Gy)
            resultadosProcesamiento["mag"] = self.handle.matriz_a_pixbuf(MG)
            resultadosProcesamiento["maximos"] = self.handle.matriz_a_pixbuf(
                GNMaxS
            )
            resultadosProcesamiento["bordesdebiles"] = self.handle.matriz_a_pixbuf(
                LowE
            )
            resultadosProcesamiento["bordesfuertes"] = self.handle.matriz_a_pixbuf(
                HighE
            )
            resultadosProcesamiento["bordes"] = self.handle.matriz_a_pixbuf(
                DetectedEdges
            )

            # El hilo de fondo no toca GTK: entrega los pixbufs y la vista
            # renderiza en el hilo principal (AGENTS.md §6.3 y §4).
            GLib.idle_add(
                self.main_window.mostrar_resultados, resultadosProcesamiento
            )

            puntos_borde = puntos_de_borde(DetectedEdges)
            plan, _evidencia = self._decidir_plan(puntos_borde)
            print(f"Geometría: {plan.detalle}")

            # Criterio 3: sin decisión el pipeline se detiene mostrando ambos
            # candidatos con la confianza y la evidencia numérica.
            if plan.geometria is None:
                GLib.idle_add(
                    self._mostrar_geometria_indeterminada, plan.detalle
                )
                GLib.idle_add(self.main_window.btn_procesar.set_sensitive, True)
                return

            if plan.origen == ORIGEN_AUTOMATICO:
                GLib.idle_add(self._mostrar_geometria_propuesta, plan.detalle)

            # Criterio 4: las dos geometrías son ramas del mismo selector.
            if plan.geometria is Geometria.CIRCULO:
                completado = self._rama_circulo(DetectedEdges, plan)
            else:
                completado = self._rama_recta(DetectedEdges, Gx, Gy, MG, puntos_borde, plan)

            if completado:
                GLib.idle_add(self.main_window.finalizar_proceso_exitoso)

        except (ValueError, GLib.Error) as e:
            GLib.idle_add(
                self.main_window.mostrar_alerta,
                "No se pudo procesar la imagen",
                str(e),
                True,
            )
            GLib.idle_add(self.main_window.btn_procesar.set_sensitive, True)

    def establecer_geometria(self, indice: int) -> None:
        """Fija la geometría a medir desde el selector de la vista.

        `indice` es la posición en `OPCIONES_GEOMETRIA`; `None` (automático)
        deja la decisión al clasificador.
        """
        self.geometria_seleccionada = GEOMETRIA_POR_OPCION[indice]

    def _decidir_plan(
        self, puntos_borde: np.ndarray
    ) -> tuple[PlanGeometria, EvidenciaGeometria | None]:
        """Decide la geometría: la fija el operador o la propone el clasificador.

        En automático se consulta `clasificar_geometria` sobre los puntos de
        borde ya detectados (etapas ①–⑥) y la propuesta se usa solo si el
        clasificador decidió (criterio 2).
        """
        if self.geometria_seleccionada is not None:
            return plan_de_etapas(self.geometria_seleccionada), None
        evidencia = clasificar_geometria(puntos_borde)
        return plan_de_etapas(None, evidencia), evidencia

    def _mostrar_geometria_propuesta(self, detalle: str) -> bool:
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.main_window.row_geometria.set_subtitle(detalle)
        return False

    def _mostrar_geometria_indeterminada(self, detalle: str) -> bool:
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.main_window.row_geometria.set_subtitle(detalle)
        return False

    def _mostrar_recta_resultado(self, r: float, puntos: int) -> bool:
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.main_window.row_geometria.set_subtitle(
            f"recta ajustada con {puntos} puntos; dispersión {r:.3f}px"
        )
        return False

    def _mostrar_trazo_resultado(self, ancho: float, centro: np.ndarray) -> bool:
        """Corre en el hilo principal, vía GLib.idle_add."""
        rho_centro = centro[0] * centro[3] - centro[1] * centro[2]
        theta_centro = np.arctan2(-centro[2], centro[3])
        self.main_window.row_geometria.set_subtitle(
            f"trazo: ancho {ancho:.2f}px; centro rho {rho_centro:.1f}px theta {theta_centro:.3f}rad"
        )
        return False

    def _reportar_fallo(self, plan: PlanGeometria, motivo: str) -> None:
        """Detiene el pipeline mostrando el motivo y la evidencia (criterio 3)."""
        GLib.idle_add(
            self.main_window.mostrar_alerta,
            "No se pudo procesar la imagen",
            f"{motivo}. {plan.detalle}",
            True,
        )
        GLib.idle_add(self.main_window.btn_procesar.set_sensitive, True)

    def _rama_circulo(
        self, DetectedEdges: np.ndarray, plan: PlanGeometria
    ) -> bool:
        """Etapas ⑦→⑧→⑨: centro aproximado, anillo y ajuste de círculo."""
        alto, ancho = DetectedEdges.shape[:2]
        r0 = min(alto, ancho) / 2
        radio, pico, ambiguedad, origen = resolver_radio(
            self.estado_diametro.diametro_para_procesar(),
            DetectedEdges,
            r0,
            self.aproxHough,
        )
        if radio <= 0:
            self._reportar_fallo(
                plan, "No se pudo estimar el radio del círculo en el recorte."
            )
            return False

        if origen == "automatico":
            GLib.idle_add(
                self._mostrar_diametro_detectado,
                2 * radio,
                ambiguedad >= self.aproxHough.UMBRAL_AMBIGUEDAD,
            )

        xRecortada, yRecortada, _n, accumulador = (
            self.aproxHough.hough_circles_vectorizado(DetectedEdges, radio, 0.8)
        )
        centro = self.aproxHough.mejor_centro(
            xRecortada, yRecortada, accumulador
        )
        if centro is None:
            self._reportar_fallo(
                plan, "La transformada de Hough no encontró centros."
            )
            return False

        aviso = (
            " (revisar: hay otro candidato parecido)"
            if ambiguedad >= self.aproxHough.UMBRAL_AMBIGUEDAD
            else ""
        )
        print(
            f"Radio {radio:.1f} px (diametro {2 * radio:.1f}) [{origen}], "
            f"pico {pico}, ambiguedad {ambiguedad:.2f}{aviso}"
        )

        puntosFiltrados = self.circleFilter.find_circle(
            DetectedEdges, radio, (centro[0], centro[1])
        )

        # Etapa 8: la selección tiene que RODEAR el círculo.
        anillo_ok, motivo = self.circleFilter.validar_anillo(
            puntosFiltrados, (centro[0], centro[1])
        )
        if not anillo_ok:
            self._reportar_fallo(plan, f"No se puede medir el círculo: {motivo}")
            return False

        x, y, _r, _pv = self.LSC.Circulo_simple(puntosFiltrados)
        x = self.main_window.xRecorte + x
        y = self.main_window.yRecorte + y
        return True

    def _rama_recta(
        self,
        DetectedEdges: np.ndarray,
        Gx: np.ndarray,
        Gy: np.ndarray,
        MG: np.ndarray,  # Magnitud del gradiente
        puntos_borde: np.ndarray,
        plan: PlanGeometria,
    ) -> bool:
        """Etapas ⑩→⑪: Hough de rectas y ajuste robusto."""
        candidata = self.HoughLineas.hough_lineas(puntos_borde, DetectedEdges)
        if candidata is None:
            self._reportar_fallo(
                plan, "La transformada de Hough no encontró rectas candidatas."
            )
            return False

        rho, theta, conteo, masa, desviacion = candidata

        # Medir trazo grueso (T3): las orillas del trazo son dos picos casi
        # paralelos de Hough; se mide solo entre los puntos de ese par.
        gx = Gx[puntos_borde[:, 1].astype(int), puntos_borde[:, 0].astype(int)]
        gy = Gy[puntos_borde[:, 1].astype(int), puntos_borde[:, 0].astype(int)]
        from odin.Ajustes import refinar_bordes_subpixel
        puntos_refinados = refinar_bordes_subpixel(puntos_borde, gx, gy, MG)

        puntos_para_medir = puntos_refinados
        gx_para_medir = gx
        gy_para_medir = gy
        theta_para_medir = theta

        from ..Procesamiento import picos_de_rho

        # Orillas del trazo: máximos locales del perfil de rho en la dirección
        # de la candidata principal, a resolución de bin del acumulador.
        rhos_picos, conteos_picos, semianchuras = picos_de_rho(puntos_borde, theta)
        thetas_picos = np.full(rhos_picos.shape, theta)
        # El par de mayor evidencia es el trazo principal: es el mismo criterio
        # relativo que usa Hough para elegir candidata, y evita anclar en un
        # borde exterior que no es orilla de trazo.
        pares = emparejar_orillas(rhos_picos, thetas_picos, conteos_picos)
        # S9: la evidencia de Hough mide alineación, no intensidad, así que no
        # distingue una franja oscura de una clara —en 600mm todos los pares
        # consecutivos son franjas—. El trazo se elige por el contraste de su
        # interior contra el fondo, y la polaridad sale de la propia imagen: con
        # trazo claro sobre fondo oscuro gana la franja clara. Si ninguna franja
        # se aparta del fondo, el criterio se abstiene y manda la evidencia.
        par: tuple[int, int] | None = None
        if pares:
            par = seleccionar_trazo_por_intensidad(
                self.current_image,
                puntos_refinados,
                rhos_picos,
                thetas_picos,
                pares,
                conteos_picos,
                semianchuras,
            )
            if par is None:
                par = pares[0]

        if par is not None:
            mascara_a, mascara_b = asignar_puntos_a_orillas(
                puntos_refinados, rhos_picos, thetas_picos, par, semianchuras
            )
            # Ambas orillas del mismo trazo alimentan la medición; `medir_trazo`
            # las vuelve a separar por signo del gradiente.
            mascara_par = mascara_a | mascara_b
            if np.count_nonzero(mascara_par) >= 2:
                puntos_para_medir = puntos_refinados[mascara_par]
                gx_para_medir = gx[mascara_par]
                gy_para_medir = gy[mascara_par]
                theta_para_medir = theta

        medicion = medir_trazo(puntos_para_medir, gx_para_medir, gy_para_medir, theta_para_medir)
        
        if medicion is not None:
            # Mostrar ancho y centro del trazo
            print(
                f"Trazo: ancho {medicion.ancho:.2f}px; "
                f"centro rho {medicion.centro[0] * medicion.centro[3] - medicion.centro[1] * medicion.centro[2]:.1f}px "
                f"theta {np.arctan2(-medicion.centro[2], medicion.centro[3]):.3f}rad"
            )
            GLib.idle_add(
                self._mostrar_trazo_resultado, medicion.ancho, medicion.centro
            )
            return True
        
        # Fallback: ajuste de una sola recta
        param_inicial = self.LineaRobusta.euc_space(rho, theta)
        try:
            param_final, r, sobrevivientes = self.LineaRobusta.linea_robusta(
                puntos_borde, param_inicial
            )
        except ValueError as error:
            self._reportar_fallo(plan, f"No se pudo ajustar la recta: {error}")
            return False

        print(
            f"Recta rho {rho:.1f}px, theta {theta:.3f} rad "
            f"[{conteo} picos, masa {masa}, desviación {desviacion:.2f}px]; "
            f"dirección ({param_final[2]:.3f}, {param_final[3]:.3f}), "
            f"{sobrevivientes.shape[0]} puntos, dispersión {r:.3f}px"
        )
        GLib.idle_add(
            self._mostrar_recta_resultado, r, int(sobrevivientes.shape[0])
        )
        return True

    def _mostrar_diametro_detectado(self, diametro: float, ambiguo: bool) -> bool:
        """Corre en el hilo principal, vía GLib.idle_add."""
        self.estado_diametro.registrar_detectado(diametro, ambiguo)
        if not self.estado_diametro.es_manual:
            self._escribir_campo_diametro(
                self.estado_diametro.valor_visible()
            )
        self.main_window.row_diametro.set_subtitle(
            self.estado_diametro.texto_estado()
        )
        return False

    def _escribir_campo_diametro(self, valor: float) -> None:
        """Escribe el campo sin que cuente como cambio del usuario (R6.3)."""
        self._actualizando_diametro = True
        self.main_window.row_diametro.get_adjustment().set_value(valor)
        self._actualizando_diametro = False
