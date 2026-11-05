"""Hilo de fondo para la matemática pesada de ODIN.

Ejecuta el pipeline de procesamiento de imágenes sin congelar la UI.
"""

import threading

import numpy as np
from gi.repository import GLib


class WorkerThread(threading.Thread):
    """Ejecuta el pipeline de detección de bordes en segundo plano."""

    def __init__(self, controller):
        super().__init__(daemon=True)
        self.controller = controller
        self.error = None

    def run(self):
        try:
            print("Hilo secundario: Iniciando convoluciones...")
            controlador = self.controller
            resultadosProcesamiento = {}
            resultadosProcesamiento["inicial"] = (
                controlador.handle.matriz_a_pixbuf(controlador.current_image)
            )
            Gx, Gy = controlador.kernelSeparable.DerivGauss(
                controlador.current_image, controlador.sigma, 1, 1, 360
            )
            MG, Tetha = controlador.MagnitudGradiente.MagFase(Gx, Gy)
            GNMaxS = controlador.NonMaxSup.LinearInterpolation(
                MG, Gx, Gy, Tetha
            )
            uOtsu, _uRosin = controlador.Otsu.umbralRosinYOtsu(
                GNMaxS, histo=True
            )
            HighE, LowE = controlador.NonMaxSup.DobleThreshold(GNMaxS, uOtsu)
            DetectedEdges = controlador.DoubleTh.EdgeTrack_Hyst(HighE, LowE)
            print(
                f"Bordes: {np.sum(HighE > 0)} fuertes, "
                f"{np.sum(LowE > 0)} débiles, "
                f"{np.sum(DetectedEdges > 0)} tras histéresis"
            )

            resultadosProcesamiento["gx"] = (
                controlador.handle.matriz_a_pixbuf(Gx)
            )
            resultadosProcesamiento["gy"] = (
                controlador.handle.matriz_a_pixbuf(Gy)
            )
            resultadosProcesamiento["mag"] = (
                controlador.handle.matriz_a_pixbuf(MG)
            )
            resultadosProcesamiento["maximos"] = (
                controlador.handle.matriz_a_pixbuf(GNMaxS)
            )
            resultadosProcesamiento["bordesdebiles"] = (
                controlador.handle.matriz_a_pixbuf(LowE)
            )
            resultadosProcesamiento["bordesfuertes"] = (
                controlador.handle.matriz_a_pixbuf(HighE)
            )
            resultadosProcesamiento["bordes"] = (
                controlador.handle.matriz_a_pixbuf(DetectedEdges)
            )

            vista = controlador.main_window.vistas_procesadas
            vista["original"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["inicial"])
            )
            vista["gradiente x"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gx"])
            )
            vista["gradiente y"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["gy"])
            )
            vista["magnitud"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["mag"])
            )
            vista["maximos"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["maximos"])
            )
            vista["bordes debiles"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesdebiles"])
            )
            vista["bordes fuertes"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordesfuertes"])
            )
            vista["bordes"].set_paintable(
                Gdk.Texture.new_for_pixbuf(resultadosProcesamiento["bordes"])
            )

            # Etapa 7: el radio no es una constante (spec hough-circles, R2).
            alto, ancho = DetectedEdges.shape[:2]
            r0 = min(alto, ancho) / 2
            radio, pico, ambiguedad, origen = resolver_radio(
                controlador.estado_diametro.diametro_para_procesar(),
                DetectedEdges,
                r0,
                controlador.aproxHough,
            )
            if radio <= 0:
                raise ValueError(
                    "No se pudo estimar el radio del circulo en el recorte."
                )

            if origen == "automatico":
                GLib.idle_add(
                    controlador._mostrar_diametro_detectado,
                    2 * radio,
                    ambiguedad >= controlador.aproxHough.UMBRAL_AMBIGUEDAD,
                )

            xRecortada, yRecortada, n, accumulador = (
                controlador.aproxHough.hough_circles_vectorizado(
                    DetectedEdges, radio, 0.8
                )
            )
            centro = controlador.aproxHough.mejor_centro(
                xRecortada, yRecortada, accumulador
            )
            if centro is None:
                raise ValueError(
                    "La transformada de Hough no encontro centros."
                )

            aviso = (
                " (revisar: hay otro candidato parecido)"
                if ambiguedad >= controlador.aproxHough.UMBRAL_AMBIGUEDAD
                else ""
            )
            print(
                f"Radio {radio:.1f} px (diametro {2 * radio:.1f}) [{origen}], "
                f"pico {pico}, ambiguedad {ambiguedad:.2f}{aviso}"
            )

            puntosFiltrados = controlador.circleFilter.find_circle(
                DetectedEdges, radio, (centro[0], centro[1])
            )

            # Etapa 8: la selección tiene que RODEAR el círculo.
            anillo_ok, motivo = controlador.circleFilter.validar_anillo(
                puntosFiltrados, (centro[0], centro[1])
            )
            if not anillo_ok:
                raise ValueError(f"No se puede medir el circulo: {motivo}.")

            x, y, r, pv = controlador.LSC.Circulo_simple(puntosFiltrados)
            x = controlador.main_window.xRecorte + x
            y = controlador.main_window.yRecorte + y
            GLib.idle_add(
                controlador.main_window.finalizar_proceso_exitoso
            )

        except Exception as e:
            GLib.idle_add(
                controlador.main_window.mostrar_alerta,
                "No se pudo procesar la imagen",
                str(e),
                True,
            )
            GLib.idle_add(
                controlador.main_window.btn_procesar.set_sensitive, True
            )
