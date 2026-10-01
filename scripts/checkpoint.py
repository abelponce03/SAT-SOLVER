"""
checkpoint.py — CSV de experimentos que sobreviven a un apagado (ADR-0008).

Dos piezas, compartidas por todos los arneses:

- `filas_completas(path, campos)`: lee un CSV que pudo quedar cortado a mitad
  de una escritura (apagón, reinicio, falta de memoria) y devuelve solo las
  filas íntegras. Una fila es íntegra si su línea termina en salto de línea y
  tiene exactamente las columnas de la cabecera. `csv.DictReader` por sí solo
  no basta: una última línea cortada da una fila con campos `None` y su clave
  (instancia, semilla) parecería hecha.

- `EscritorDuradero(path, campos, previas)`: reescribe de forma ATÓMICA las
  filas previas (fichero temporal + `os.replace`) y después añade cada fila
  nueva con `flush` + `fsync`. Tras un corte de luz, en disco queda como mucho
  una línea a medias, que la siguiente lectura descarta.

Con esto, cada arnés reanuda por su clave natural (instancia, o instancia y
semilla) sin repetir lo medido ni dar por medido lo que no se terminó.
"""
import csv
import io
import os


def filas_completas(path, campos=None):
    """Filas íntegras de `path` (lista de dicts). Vacía si no existe."""
    if not os.path.exists(path):
        return []
    with open(path, newline="", errors="replace") as f:
        texto = f.read()
    lineas = texto.splitlines(keepends=True)
    if lineas and not lineas[-1].endswith(("\n", "\r")):
        lineas = lineas[:-1]                    # última línea cortada
    if not lineas:
        return []
    lector = csv.DictReader(io.StringIO("".join(lineas)))
    campos = campos or lector.fieldnames or []
    filas = []
    for fila in lector:
        if None in fila or any(fila.get(c) is None for c in campos):
            continue                            # columnas de más o de menos
        filas.append({c: fila[c] for c in campos})
    return filas


def _fsync_dir(path):
    try:
        fd = os.open(os.path.dirname(os.path.abspath(path)) or ".", os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


class EscritorDuradero:
    """Escritor CSV con reescritura atómica inicial y fsync por fila."""

    def __init__(self, path, campos, previas=()):
        self.path, self.campos = path, list(campos)
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=self.campos)
            w.writeheader()
            w.writerows(previas)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        _fsync_dir(path)
        self.f = open(path, "a", newline="")
        self.w = csv.DictWriter(self.f, fieldnames=self.campos)

    def escribir(self, fila):
        self.w.writerow(fila)
        self.persistir()

    def persistir(self):
        self.f.flush()
        os.fsync(self.f.fileno())

    def close(self):
        self.persistir()
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
