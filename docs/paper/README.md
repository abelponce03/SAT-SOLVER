# Material para artículos

Este directorio se escribe **en paralelo al desarrollo**, no al final. Cada
experimento cerrado deposita aquí su párrafo de método y su tabla, de modo que
cuando llegue el momento de redactar no haya que reconstruir nada de memoria.

## Artículos previstos

| id | título de trabajo | estado | fuente |
|---|---|---|---|
| **P1** | *Configuration complementarity is an untapped resource in modern CDCL solvers* | en recolección | `docs/research/01`, EXP-001, EXP-002 |
| **P2** | *When is aggressive preprocessing worth it? A cheap structural predictor* | idea | catálogo línea B3 |
| **P3** | Descripción de solver para la SAT Competition 2027 (2–4 págs.) | plantilla | todo el repo |

## Estructura

```
docs/paper/
├── README.md         este índice
├── P1-notas.md       argumento, evidencia acumulada y huecos pendientes de P1
├── figuras/          figuras generadas por scripts (cactus, scatter, VBS)
└── tablas/           tablas en Markdown/LaTeX generadas por los scripts de análisis
```

## Reglas

1. **Ninguna cifra se escribe a mano.** Toda tabla sale de un script del
   repositorio y lleva el comando que la regenera en un comentario. Si una cifra
   no se puede regenerar, no entra.
2. **Cada afirmación lleva su experimento.** El texto cita `EXP-NNN`; si no
   existe el experimento, la afirmación es una hipótesis y se marca como tal.
3. **Los resultados negativos también se redactan.** El descarte de la línea de
   bandits (catálogo §D1), con las siete variantes de 2026 por debajo de la
   base, es material publicable: es la clase de resultado que nadie escribe y
   que ahorra trabajo al siguiente.
4. La descripción de solver para la competición (P3) se genera a partir del
   diff contra upstream (`solver/kissat/UPSTREAM.md`), que es exactamente lo
   que piden los organizadores.
