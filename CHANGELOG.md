# Changelog

## [0.1.4](https://github.com/JoseloCelis/ODIN/compare/v0.1.3...v0.1.4) (2026-11-22)


### Bug Fixes

* **docs:** traer la cadena de absorcion completa a main ([863886b](https://github.com/JoseloCelis/ODIN/commit/863886bfccb2363eef520bf8017256ee9b7696d1))

## [0.1.3](https://github.com/JoseloCelis/ODIN/compare/v0.1.2...v0.1.3) (2026-11-22)


### Documentation

* **odd:** corregir casillas falsas en el lugar y registrar cada correccion ([355215a](https://github.com/JoseloCelis/ODIN/commit/355215aae1273e2402be4802c7100df0b68ad82c))
* **odd:** corregir veredictos tras reverificar, los 9 specs son absorbibles ([5699702](https://github.com/JoseloCelis/ODIN/commit/5699702a3d7ca16af6fb87a857cd8261b66dcd8e))
* **odd:** criterios de absorcion de .kiro y versionado de odd/specs ([79a68bb](https://github.com/JoseloCelis/ODIN/commit/79a68bbbee26824cf58bf90d690fa18b129eea27))
* **odd:** declarar estado en los tres archivos, divergencias verificadas y test de inmutabilidad ([13ed80d](https://github.com/JoseloCelis/ODIN/commit/13ed80d29399e30007bb902ba814630e18f68392))
* **odd:** registrar el criterio de absorcion de .kiro y versionar odd/specs ([c9400ba](https://github.com/JoseloCelis/ODIN/commit/c9400ba6347004035dd9b76a4a82653e627268a6))

## [0.1.2](https://github.com/JoseloCelis/ODIN/compare/v0.1.1...v0.1.2) (2026-11-20)


### Documentation

* agregar README.md ([b9e9b0c](https://github.com/JoseloCelis/ODIN/commit/b9e9b0c3b91d62b262ee1600bd178e3e90732900))

## [0.1.1](https://github.com/JoseloCelis/ODIN/compare/v0.1.0...v0.1.1) (2026-11-19)


### Documentation

* exigir ledger de estado actualizado en cada PR ([8962e6d](https://github.com/JoseloCelis/ODIN/commit/8962e6ddc730f34758ae9a75a2d1126ba953e01e))
* exigir ledger de estado actualizado en cada PR ([8f36158](https://github.com/JoseloCelis/ODIN/commit/8f36158ff2c1cd403c380131c92693f051a7c450))

## 0.1.0 (2026-11-18)


### Features

* **arranque:** actualizar mediciones Task 14/16 con Xvfb y corregir launch.json ([2b4f5cb](https://github.com/JoseloCelis/ODIN/commit/2b4f5cb8560bc9acce375954bb6b6bfe8a92790a))
* **arranque:** agregar flag --version para verificar arranque sin GUI (Task 15.1/15.2) ([d7a8cdd](https://github.com/JoseloCelis/ODIN/commit/d7a8cddba97d59b50bc7e61846f796ccecc99d57))
* **arranque:** bootstrap estructurado con logging y carga ordenada de modulos ([d722917](https://github.com/JoseloCelis/ODIN/commit/d72291785f4aeee35e11fe38476b1dbb95af2e67))
* **arranque:** documentar orden estricto de widgets en MainWindow (Task 12.2) ([3878050](https://github.com/JoseloCelis/ODIN/commit/38780505133990b2163fc88073e72a31ac09aaed))
* **circulo-simple:** validacion de entrada y excepciones descriptivas ([04ab25f](https://github.com/JoseloCelis/ODIN/commit/04ab25f60dba61f9300d2aa64d04607cc25817a7))
* etapa 7, barrido de radios y seleccion de un solo centro ([5cec468](https://github.com/JoseloCelis/ODIN/commit/5cec468cc6a58b8d9794ac0712f8fcfca6f9b9f8))
* **find-circle:** tolerancia adaptativa y validacion de cobertura del anillo ([b350deb](https://github.com/JoseloCelis/ODIN/commit/b350deb48e0e7d7ea26eed9995fc9ecb2726f9c0))
* **hough-circles:** campo de diametro en la UI y barrido de dos escalas para recortes holgados ([f0ba3cf](https://github.com/JoseloCelis/ODIN/commit/f0ba3cfa3e9aa7066553f6684e85c3a592b90625))
* **integration:** integrar cadena final hacia main ([21d91d0](https://github.com/JoseloCelis/ODIN/commit/21d91d0b57e2724e3a11d0f3ff0243c2420da1e5))
* **Preprocesamiento:** exponer aliases públicos de etapas ②-⑨ en __init__.py ([3e8ee9b](https://github.com/JoseloCelis/ODIN/commit/3e8ee9b07c6ac4ff1b57e3e7db579e6295fe675b))
* **refactor:** etapa ① kernelSeparable a src/odin/Preprocesamiento/models/ ([53bd01b](https://github.com/JoseloCelis/ODIN/commit/53bd01b31bb0ff8bc182fc5f3c4a06ebdcade2ff))
* umbrales Otsu+Rosin, arranque dual de main.py y correcciones de entorno ([7e04c72](https://github.com/JoseloCelis/ODIN/commit/7e04c722b9ddbb34d860753cbfde0e9fd8a4f0a1))


### Bug Fixes

* **ajustes:** exportar alias público LSC según AGENTS.md; corregir referencia a config/config.yaml inexistente ([0f58b5e](https://github.com/JoseloCelis/ODIN/commit/0f58b5e47cec13abdfc8634d0da65526a2658081))
* **bootstrap:** cadenas de excepción (from e), borrar MAX_WARN_LEN, doc placeholder env_type, typing moderno; quitar print en import de utils ([1b1d326](https://github.com/JoseloCelis/ODIN/commit/1b1d32691eaf3a981e9ee9dd9bc8e90739847c19))
* **bootstrap:** nombrar componente y modo en los errores de arranque ([d4e15f8](https://github.com/JoseloCelis/ODIN/commit/d4e15f8c1cce06f5fa904b79d59207ff176d9707))
* cargar imagen con self.handle y corregir nr/nc en dibujo de kernels; tests etapa 9 con datos e imagen real ([844113d](https://github.com/JoseloCelis/ODIN/commit/844113d402527a11404cfc48bced6e13fd7299c8))
* **ci:** instalar gi/GTK4 por apt en runner para evitar ModuleNotFoundError ([5100686](https://github.com/JoseloCelis/ODIN/commit/51006862405a6a9c01f37f44ec4c847a642326c4))
* **ci:** owner en minúsculas para tag GHCR ([75a752b](https://github.com/JoseloCelis/ODIN/commit/75a752b20d250fa48636b7ffedcc44afa49718ca))
* **ci:** owner hardcodeado en minusculas para tag GHCR ([824320b](https://github.com/JoseloCelis/ODIN/commit/824320b0a17f1d17f22c3f7177c1fcbad179c5e8))
* **ci:** quitar cache-from para publicar imagen sin manifest unknown ([4fcde24](https://github.com/JoseloCelis/ODIN/commit/4fcde2483b40dbc4d4dc58e3e3a8876bdf998aa5))
* **circulo-simple:** guard de colinealidad sobre condicion normalizado ([58a6202](https://github.com/JoseloCelis/ODIN/commit/58a62022845e3274273e6428b7c03aee509e4b9f))
* **ci:** usar imagen Docker de Dockerfile.ci en ambos CI para garantizar gi/GTK4 ([6d7122f](https://github.com/JoseloCelis/ODIN/commit/6d7122f83d1f7a4e1b03e2a304d16b20a420c6b6))
* **ci:** usar imagen Docker publicada en GHCR para garantizar gi/GTK4 ([6449ff3](https://github.com/JoseloCelis/ODIN/commit/6449ff3da4330c1c23f4ba183488643fe7435d39))
* **ci:** usar imagen publicada ghcr.io/joselocelis/odin-ci:latest ([a19e742](https://github.com/JoseloCelis/ODIN/commit/a19e742a75920def1676a13086b9fa976a0a2c61))
* **ci:** volver a instalar gi/GTK4 por apt en runner ([d150df1](https://github.com/JoseloCelis/ODIN/commit/d150df100b5339ce20a9427a2a96335ea72a4c3d))
* **ci:** volver a instalar gi/GTK4 por apt en runner (contenedor sin gi) ([6323815](https://github.com/JoseloCelis/ODIN/commit/632381572a4191668826c95132275ecc975e1cc5))
* corregir imports y variables en src/odin/controllers/main_controller.py ([01a0442](https://github.com/JoseloCelis/ODIN/commit/01a0442ef91bbfd9db130c9c15b018de9f611475))
* corregir sys.path en src/main.py para apuntar a src/ no a src/src/ ([53de28a](https://github.com/JoseloCelis/ODIN/commit/53de28a9c70fc3497b4e1351f96c3f8635d81ac8))
* etapa 6, guarda de entrada vacia y elimina histeresis recursiva muerta ([1841523](https://github.com/JoseloCelis/ODIN/commit/1841523f675280fc6b852f5edebf5f67bf04c86c))
* exportar MagFase en Preprocesamiento y agregar guardas en tests de controlador ([64101f6](https://github.com/JoseloCelis/ODIN/commit/64101f6a09634f09a6d872e327775ed723adce41))
* **hough-circles:** rechazar radio no positivo en hough_circles_vectorizado ([11183bf](https://github.com/JoseloCelis/ODIN/commit/11183bf8ecf41fb45c75ab9c6bbf92c884196f8d))
* **kernel-separable:** D4 sigma flotante como MATLAB (round en lugar de int) ([720aa56](https://github.com/JoseloCelis/ODIN/commit/720aa5671d32194ad65cecb1ffc5c3895a90b042))
* limpieza de MagFase - sin import cv2 muerto y guarda de entradas vacias ([c4c43ba](https://github.com/JoseloCelis/ODIN/commit/c4c43ba5b0400a2d652c8126c2587d426746b349))
* **mag-fase:** mapear ángulo -180 a 180 para cumplir rango (-180, 180] ([a2ffd87](https://github.com/JoseloCelis/ODIN/commit/a2ffd87684f4ed8e71a85e32dcd650a58e5597c3))
* NMS cuadrante-correcto, tie-breaking uniforme y limpieza (etapa 3) ([10f2626](https://github.com/JoseloCelis/ODIN/commit/10f2626a745a333ff83381c8e7eae4a5f6f025f0))
* OdinAdwaita -&gt; ODINAdwaita en main_window.py ([99f5d3e](https://github.com/JoseloCelis/ODIN/commit/99f5d3e14651de5daf4615be16dee67dbb3af0c9))
* **otsu-rosin:** manejar rango minimo en histograma para casi-constantes ([12bd93d](https://github.com/JoseloCelis/ODIN/commit/12bd93dd8d90d4b04fcce9377b3e2b493fdd1424))
* pasar self.main_window (no self) a handle.recortar_imagen en on_process_clicked ([ea8f103](https://github.com/JoseloCelis/ODIN/commit/ea8f103efd8e0aa5d2eb510bac8f41097fbe4ea7))
* **Procesamiento:** _a_escalar en estimar_radio y alias NonMaxSup en non_max_sup ([8b8bda9](https://github.com/JoseloCelis/ODIN/commit/8b8bda98fb273b1348cd69a4930ddcad4ef6d037))
* recuperar NMS_Parabolic y NMS_Gaussian tras verificar su utilidad (etapa 3) ([d1a458c](https://github.com/JoseloCelis/ODIN/commit/d1a458c5db78a27411622cb7674b459cf6c87f9a))
* reduce la dilatacion de la histeresis de 7x7 a 5x5 ([d990ef7](https://github.com/JoseloCelis/ODIN/commit/d990ef79482312d2f9015b59090dffe03ecbc8ab))
* sincronizar image_loaded con main_window y actualizar perfiles de launch.json ([643a45e](https://github.com/JoseloCelis/ODIN/commit/643a45e90d481283de5fa849b40db527780a4c5a))
* soporte completo del kernel, guard de sigma y cortes acotados (etapa 1) ([6412c67](https://github.com/JoseloCelis/ODIN/commit/6412c6774e1decc8ace5934eca5d57c1ae8d1d17))
* **test:** corregir shadowing find_circle (alias de paquete Ajustes); test opt-in ODIN_TEST_LENTO verde ([f45b151](https://github.com/JoseloCelis/ODIN/commit/f45b151a82a00e49474bd19fae52a7168eb1a267))
* umbral correcto para histogramas de un solo bin (etapa 4) ([1b1eefb](https://github.com/JoseloCelis/ODIN/commit/1b1eefbc2a39c36efc3983c57b10a8eb8ff589dd))
* usar self.main_window.sigma en lugar de self.sigma en DerivGauss ([b8c4432](https://github.com/JoseloCelis/ODIN/commit/b8c4432e6db768e3b1f9a51e7a443aaf61fae1ba))
* **worker:** add missing Gdk import and wire resolver_radio into worker thread ([2fe46b5](https://github.com/JoseloCelis/ODIN/commit/2fe46b5fc52a7bd55ca7ce9e289bfbf852b77280))


### Documentation

* actualizar specs de kiro y memoria del proyecto a rutas src/ ([571c775](https://github.com/JoseloCelis/ODIN/commit/571c77576239a6d23d8cf6e8884ae81a2ec475ef))
* AGENTS.md refleja la suite de tests existente ([67cb2a5](https://github.com/JoseloCelis/ODIN/commit/67cb2a5021967533a2e767e94abd3424f62c810c))
* **agents:** actualizar AGENTS.md sin bloque JSON de launch.json ([844bdb3](https://github.com/JoseloCelis/ODIN/commit/844bdb3b42d204d9fa07eeaf2087e45ce280b4ec))
* **agents:** actualizar arquitectura a src/odin/ y agregar sección de skills ([572ec03](https://github.com/JoseloCelis/ODIN/commit/572ec03e85e3069a9a39d4530cc7220737d0aa14))
* **agents:** add Open Agent Skills ecosystem loading & registry section ([b6b3ecf](https://github.com/JoseloCelis/ODIN/commit/b6b3ecf533c70a4682f476e18fe26fdac2030329))
* **agents:** clarificar formato de commits para Release Please (type en inglés, scope/desc en español) ([999be6d](https://github.com/JoseloCelis/ODIN/commit/999be6d0356e32bf61cf3e17b284772dc9a49fba))
* **agents:** documentar resolución real de skills locales (.agents/skills + symlinks) ([c5c80c4](https://github.com/JoseloCelis/ODIN/commit/c5c80c45d9ae6a9f26d27e2037121883984fe728))
* **agents:** fusionar versión agente + proyecto; mantener inglés como única doc técnica en inglés ([e11f400](https://github.com/JoseloCelis/ODIN/commit/e11f40083e937ffd80adee370d74f65f83633930))
* **agents:** reescribir AGENTS.md con la arquitectura real y carga de skills ([896b6a4](https://github.com/JoseloCelis/ODIN/commit/896b6a41f26d5b5ba475132edceaf3b8cafb5250))
* **agents:** simplify source tree to dirs + __init__.py + key infra files ([7668cc7](https://github.com/JoseloCelis/ODIN/commit/7668cc7103f392097e010dfb92c4481cde871271))
* agregar AGENTS.md con estructura y convenciones del proyecto ([3c41148](https://github.com/JoseloCelis/ODIN/commit/3c41148e7937b6136aa1196c7b674bd376d2cf6b))
* cerrar Task 16 y marcar tasks 12-16 completadas ([7f823b7](https://github.com/JoseloCelis/ODIN/commit/7f823b74afa8ea163681f4a9838c1e7782bb86d1))
* etapa 7 implementada en MEMORY.md, con R9 y la deuda R6 ([69223f6](https://github.com/JoseloCelis/ODIN/commit/69223f63ff7809a76ca36ab2bef396a4a84499b3))
* **memoria:** cierre de R6 y R10 en la etapa 7 ([28db3ad](https://github.com/JoseloCelis/ODIN/commit/28db3ad2bb8410fbbe6acd028cca9461592f67fb))
* **memoria:** etapa 8 cerrada y aviso para la etapa 9 ([5489a13](https://github.com/JoseloCelis/ODIN/commit/5489a13bf4e4776921e9ff7a4fd86d341bb259af))
* **memory:** actualizar estado final Task 14/16 (Wayland completada, 16 parcial) ([9f98f7c](https://github.com/JoseloCelis/ODIN/commit/9f98f7c3fb201c530e0662a88bc34b17b090d40d))
* **memory:** actualizar fecha de modificacion tras actualizar AGENTS.md ([89ead77](https://github.com/JoseloCelis/ODIN/commit/89ead7728565191d97aa64c3d52f4a83b264209b))
* **memory:** actualizar fecha y limpiar líneas desactualizadas (aliases, dataset) ([6bdd7cd](https://github.com/JoseloCelis/ODIN/commit/6bdd7cd70771af4d1be58bc4b27edf8d69c53ad3))
* **memory:** actualizar ledger tras barrido S1-S4 y doc-staleness\n\nFecha de modificacion: 2026-10-31. Registro los dos bugs reales corregidos (Hough r&lt;=0 y Otsu rango minimo), el barrido completo S1-S4 verde, la doc-staleness pendiente (R3.2 y diseno de etapa 4) y el estado de specs en .kiro/. Formato ledger con fecha de modificacion al inicio, maximo 50 líneas. ([54de92e](https://github.com/JoseloCelis/ODIN/commit/54de92ee7d97c6d3b5b533b0fa05fc3f4dde593e))
* **memory:** actualizar ledger tras Task 12 y Task 15 completadas ([2347121](https://github.com/JoseloCelis/ODIN/commit/2347121fa591046ed0b63780d52a26977ee9a150))
* **memory:** cerrar doc-staleness R3.2 etapa ② MagFase ([06b4c03](https://github.com/JoseloCelis/ODIN/commit/06b4c030049a4e6586625a0e3c90d5898ca4f9b8))
* **memory:** cerrar Task 14/16 con estado verificado (bloqueado por pantalla) ([e428b74](https://github.com/JoseloCelis/ODIN/commit/e428b742dca2090b927fd8844aef5eda91c990bc))
* **memory:** compactar temas para mantener &lt;=50 lineas ([491183b](https://github.com/JoseloCelis/ODIN/commit/491183bb485dfab8a939837f8db4ba09c101b46a))
* **memory:** dejar automatización release y security solo en GitHub ([4f0b027](https://github.com/JoseloCelis/ODIN/commit/4f0b02732c3bfa06e5be8b7557648e118bf53d8d))
* **memory:** hypothesis instalado en host (apt); suite verde bajo xvfb ([69fed5d](https://github.com/JoseloCelis/ODIN/commit/69fed5d0e14a28f4608345f55ace7151d3be22a0))
* **memory:** máquina verificada (WSL2/D3D12); suite verde bajo xvfb ([fb94026](https://github.com/JoseloCelis/ODIN/commit/fb940268cec8c6166c64cba0856ce96a7a605b24))
* **memory:** precisar pendientes de arquitectura (Strategy y MVC) ([0bd1e8a](https://github.com/JoseloCelis/ODIN/commit/0bd1e8ae4498d123c4f6179fdea94ea28d1eb320))
* **memory:** registrar encapsulado de API pública por dominio ([093757b](https://github.com/JoseloCelis/ODIN/commit/093757bed799499db52e229c4becee9c3fb265c2))
* **memory:** registrar fix RAIZ y conteos post-fix ([500e9ac](https://github.com/JoseloCelis/ODIN/commit/500e9acd78351b6d231f2cefc40a9f27fdc5ac3a))
* **memory:** registrar fixes del bootstrap (skill python) ([ef203fd](https://github.com/JoseloCelis/ODIN/commit/ef203fde339e574937b321f639f7bf9cac2650d1))
* **memory:** registrar mediciones Task 14/16 sin pantalla ([39f1371](https://github.com/JoseloCelis/ODIN/commit/39f13715633e1f41e37d1a222a509d5d2f2f8cad))
* **memory:** registrar PRs de Azure en ci/release-workflows ([4d09261](https://github.com/JoseloCelis/ODIN/commit/4d09261db342eb662d1a07d0028ea0f931ee6385))
* **memory:** registrar PRs en slices y compactar estado del proyecto ([4f72788](https://github.com/JoseloCelis/ODIN/commit/4f72788d6201c6379ee82cba29245a24b1766285))
* **memory:** registrar type hints completos en src/odin ([3dfabcd](https://github.com/JoseloCelis/ODIN/commit/3dfabcdad04477b649934f96a77b2d607d8a767c))
* **memory:** suite completa 188 passed bajo xvfb+ODIN_TEST_LENTO ([4ee6eb6](https://github.com/JoseloCelis/ODIN/commit/4ee6eb66dd85c156e126235cb89a0bab886b5133))
* **odd:** registro del barrido de falsacion por etapa ([a8f90bf](https://github.com/JoseloCelis/ODIN/commit/a8f90bfd919dccb4b2ea835246a6005bbcf93d02))
* registra la enmienda 5x5, el spec de la etapa 7 y el dataset ignorado ([52cbee5](https://github.com/JoseloCelis/ODIN/commit/52cbee5d4619e838c23ca59184dd8763510e0c75))
* sincronizar rutas en tasks de kiro y actualizar MEMORY.md a 2026-11-06 ([ba3ed93](https://github.com/JoseloCelis/ODIN/commit/ba3ed9329bd5d01910c2c8dbd0d233e31fc2e77b))
* spec de caracterizacion R1-R5 para mag-fase, etapa 2 ([a4a9308](https://github.com/JoseloCelis/ODIN/commit/a4a9308783c6f657fca05baef48157bb424794de))
* spec R1-R5 para non-max-sup, etapa 3 ([ba49f3f](https://github.com/JoseloCelis/ODIN/commit/ba49f3f97bbde875ac41f4c98d0ab67b218f654a))
* spec R1-R6 para otsu-rosin, etapa 4 ([b04f43b](https://github.com/JoseloCelis/ODIN/commit/b04f43b817861ef7dfe79ccc8a71952479c644b3))
* spec R1-R8 para edge-track-hyst, etapa 6 ([dfdde21](https://github.com/JoseloCelis/ODIN/commit/dfdde21895ac49a1fbfc6f10f5a3cb3fdb64bdd2))
* spec R1-R8 para hough-circles, etapa 7 ([235bac3](https://github.com/JoseloCelis/ODIN/commit/235bac3c6caa7f71bbc9e58507d5f3e42b06dc9d))
* spec S1-S6 (requirements/design/tasks) para kernel-separable, etapa 1 ([6d26e78](https://github.com/JoseloCelis/ODIN/commit/6d26e78f19518854c483dc065aff131ac1e0d4d8))
* **spec:** actualizar diseño de etapa ④ Otsu tras fix de rango mínimo ([1b5bc08](https://github.com/JoseloCelis/ODIN/commit/1b5bc08aa7afb5e1ae3eb2d33a2f9f5aba9f544d))
* **spec:** cerrar etapa ⑨ circulo-simple con requisitos alineados al código ([857f422](https://github.com/JoseloCelis/ODIN/commit/857f4227f2cc9b60f42deb3d9d3c6a5ae707d126))
* unificar AGENTS.md canónico con visión de Kiro y memoria de proyecto ([cf110cf](https://github.com/JoseloCelis/ODIN/commit/cf110cf3cf08b2f361ed1954d8320ef84353cf8c))
