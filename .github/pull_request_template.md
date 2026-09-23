## Qué cambia

<!-- Una frase. Si toca `solver/kissat/`, di qué fichero y qué punto del CDCL. -->

## Por qué

<!-- Enlaza el ADR, el documento de investigación o el experimento que lo motiva. -->

- ADR / experimento:

## Evidencia

<!-- Sin esto no se fusiona nada que toque el solver. -->

- [ ] `./scripts/smoke_test.sh` en verde (corrección + pruebas DRAT + determinismo)
- [ ] A/B ejecutado: `results/<...>.csv` (A) vs `results/<...>.csv` (B)
- [ ] Números pegados abajo (`python3 scripts/par2.py A.csv B.csv --md`)
- [ ] La feature está detrás de una opción, apagada por defecto (ADR-0002 §3)

## Documentación (ADR-0006: en el mismo PR, no al final)

- [ ] `CHANGELOG.md` actualizado
- [ ] Manual de usuario / `labesat(1)` actualizados si el usuario ve el cambio
- [ ] ADR si hay decisión de diseño; `docs/decisiones/registro.md` si surgió una decisión abierta
- [ ] Entrada en `docs/metodologia/bitacora.md` si cierra una sesión de trabajo

## Autoría (ADR-0005)

- [ ] `scripts/check_authorship.sh` en verde: sin coautorías de herramientas en commits ni en este PR

<!-- pega aquí la tabla de par2.py --md -->

## Riesgos y qué vigilar

<!-- ¿Puede degradar alguna familia? ¿Toca generación de pruebas? ¿Cambia el determinismo? -->
