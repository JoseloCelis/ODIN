# Changelog

## [0.4.7](https://github.com/JoseloCelis/ODIN/compare/v0.4.6...v0.4.7) (2026-11-28)


### Documentation

* **agentes:** corregir la regla de tokens y recortar la sección 10 al mínimo indispensable ([#61](https://github.com/JoseloCelis/ODIN/issues/61)) ([8b73deb](https://github.com/JoseloCelis/ODIN/commit/8b73debd29fe4b92ed4fbca17174133b48ead87e))

## [0.4.6](https://github.com/JoseloCelis/ODIN/compare/v0.4.5...v0.4.6) (2026-11-28)


### Documentation

* **agentes:** documentar el sistema de diseno, el tooling MCP y las decisiones durables ([#59](https://github.com/JoseloCelis/ODIN/issues/59)) ([ee97954](https://github.com/JoseloCelis/ODIN/commit/ee9795437c8cd9bba2a4c1c2da2f1bb19cb24337))

## [0.4.5](https://github.com/JoseloCelis/ODIN/compare/v0.4.4...v0.4.5) (2026-11-26)


### Bug Fixes

* **ci:** usar PAT en el auto-merge para que el push a main dispare Release-Please ([#56](https://github.com/JoseloCelis/ODIN/issues/56)) ([2067f7f](https://github.com/JoseloCelis/ODIN/commit/2067f7ffb95f033ee1e472b335bd272590738594))

## [0.4.4](https://github.com/JoseloCelis/ODIN/compare/v0.4.3...v0.4.4) (2026-11-26)


### Documentation

* **agentes:** Azure es espejo, main la unica rama de largo plazo ([#54](https://github.com/JoseloCelis/ODIN/issues/54)) ([4e34d0c](https://github.com/JoseloCelis/ODIN/commit/4e34d0ca94c46013f1f8fe7b98b233d2924a6aae))

## [0.4.3](https://github.com/JoseloCelis/ODIN/compare/v0.4.2...v0.4.3) (2026-11-26)


### Documentation

* versionar docs/ para Azure Wiki ([5cef2a4](https://github.com/JoseloCelis/ODIN/commit/5cef2a4f141a0a9d07c71f60df00a98badc98765))

## [0.4.2](https://github.com/JoseloCelis/ODIN/compare/v0.4.1...v0.4.2) (2026-11-25)


### Documentation

* **odd:** registrar la deuda de registro cerrada en 037db96 ([cba557d](https://github.com/JoseloCelis/ODIN/commit/cba557d3474ddbfdd6894c12e68be0d8e76fff64))

## [0.4.1](https://github.com/JoseloCelis/ODIN/compare/v0.4.0...v0.4.1) (2026-11-25)


### Bug Fixes

* **procesamiento:** no decidir la geometria por ruido de redondeo ([fbe96bb](https://github.com/JoseloCelis/ODIN/commit/fbe96bb21b1c32009c36e1838b104d6750aea82c))
* **procesamiento:** no decidir la geometria por ruido de redondeo ([01d2f65](https://github.com/JoseloCelis/ODIN/commit/01d2f6584bdd23f5b517951dbc343ed50579b46a))

## [0.4.0](https://github.com/JoseloCelis/ODIN/compare/v0.3.1...v0.4.0) (2026-11-25)


### Features

* **procesamiento:** acotar la medicion del trazo a las orillas de su par ([910424e](https://github.com/JoseloCelis/ODIN/commit/910424e04b1ef5185abcd90dbc3484d56390a27b))
* **procesamiento:** medir el trazo entre las orillas de su par de picos ([c231d57](https://github.com/JoseloCelis/ODIN/commit/c231d574e07c4bd11f49d5b5d9490a0d2d7519c1))
* **procesamiento:** refinar las orillas del trazo con cota subpíxel (±0.5 px) ([0651c4d](https://github.com/JoseloCelis/ODIN/commit/0651c4d8b2f0abd1d63a580d7e2b2c13a1a02d3c))
* **procesamiento:** seleccionar el trazo correcto por intensidad (franja oscura) ([87acfa9](https://github.com/JoseloCelis/ODIN/commit/87acfa952e2c5b41f71a840c3f82920c01eb5795))
* **procesamiento:** definir la orilla como región conexa del perfil, no como máximo local ([149b03a](https://github.com/JoseloCelis/ODIN/commit/149b03a68b0e6d2e8a3c1c6e10b5d8a7b1c2d3e4))

### Bug Fixes

* **procesamiento:** no decidir la geometria por ruido de redondeo ([fbe96bb](https://github.com/JoseloCelis/ODIN/commit/fbe96bb21b1c32009c36e1838b104d6750aea82c))
* **procesamiento:** no decidir la geometria por ruido de redondeo ([01d2f65](https://github.com/JoseloCelis/ODIN/commit/01d2f6584bdd23f5b517951dbc343ed50579b46a))

### Refactor

* **registro:** llevar el registro de la aplicación a logging ([037db96](https://github.com/JoseloCelis/ODIN/commit/037db9634a8e5b3c4d2e1f6a7b8c9d0e1f2a3b4c5))
* **procesamiento:** limpieza de ramas y sincronización de changelogs ([d420db4](https://github.com/JoseloCelis/ODIN/commit/d420db4))
