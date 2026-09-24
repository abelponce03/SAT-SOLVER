/* [SOLVER] Ruptura de simetrías integrada en el binario (LabeSAT, D-016,
   fase 1; ADR-0007).  Descripción y topes en 'symmetry.h'.  */

#define _DEFAULT_SOURCE
#define _POSIX_C_SOURCE 200809L

#include "symmetry.h"

#include <string.h>

#ifndef LABESAT_SYMMETRY

bool kissat_symmetry_compiled (void) { return false; }

void kissat_symmetry_preprocess (const char *input, const char *proof,
                                 double budget, symmetry_outcome *res) {
  (void) input, (void) proof, (void) budget;
  memset (res, 0, sizeof *res);
  strcpy (res->reason, "compilado sin '--symmetry'");
}

void kissat_symmetry_cleanup (symmetry_outcome *res) { (void) res; }

#else

#include "file.h"
#include "resources.h"

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#ifdef __linux__
#include <sys/prctl.h>
#endif

/* satsuma, compilado desde solver/symmetry/satsuma_entry.cpp */
extern int labesat_satsuma_main (int argc, char **argv);

#define EXIT_TOO_BIG 97 /* el hijo avisa de que la CNF supera el tope */
#define EXIT_NO_INPUT 98 /* el hijo no pudo leer o descomprimir */

bool kissat_symmetry_compiled (void) { return true; }

static double env_double (const char *name, double def) {
  const char *s = getenv (name);
  if (!s || !*s)
    return def;
  char *end;
  double v = strtod (s, &end);
  return (*end || v <= 0) ? def : v;
}

/* Copia 'in' (ya abierto y comprimido) a 'plain' sin comprimir: satsuma solo
   lee DIMACS plano.  Devuelve el número de bytes, o -1 si falla o supera
   'max_bytes' (en 'too_big'). */
static long long decompress (file *opened, const char *plain,
                             double max_bytes, bool *too_big) {
  file in = *opened;
  *too_big = false;
  FILE *out = fopen (plain, "w");
  if (!out) {
    kissat_close_file (&in);
    return -1;
  }
  char buffer[1 << 16];
  long long total = 0;
  size_t n;
  while ((n = kissat_read (&in, buffer, sizeof buffer)) > 0) {
    total += (long long) n;
    if (total > max_bytes) {
      *too_big = true;
      break;
    }
    if (fwrite (buffer, 1, n, out) != n) {
      total = -1;
      break;
    }
  }
  kissat_close_file (&in);
  if (fclose (out))
    total = -1;
  return *too_big ? -1 : total;
}

/* Proceso hijo: descomprime si hace falta y ejecuta satsuma.  Nunca vuelve. */
static void child (const char *input, const char *proof, const char *dir,
                   const char *out, double max_bytes) {
#ifdef __linux__
  prctl (PR_SET_PDEATHSIG, SIGKILL); /* si el solver muere, satsuma también */
#endif
  int null = open ("/dev/null", O_RDWR);
  if (null >= 0) {
    dup2 (null, 0), dup2 (null, 1), dup2 (null, 2);
    if (null > 2)
      close (null);
  }
  char plain[4096 + 16];
  const char *cnf = input;
  file in;
  if (!kissat_open_to_read_file (&in, input))
    _exit (EXIT_NO_INPUT);
  if (in.compressed) { /* Kissat reconoce la compresión por su firma */
    snprintf (plain, sizeof plain, "%s/in.cnf", dir);
    bool too_big;
    if (decompress (&in, plain, max_bytes, &too_big) < 0)
      _exit (too_big ? EXIT_TOO_BIG : EXIT_NO_INPUT);
    cnf = plain;
  } else {
    kissat_close_file (&in);
    if ((double) kissat_file_size (input) > max_bytes)
      _exit (EXIT_TOO_BIG);
  }
  char *argv[16];
  int argc = 0;
  argv[argc++] = (char *) "satsuma";
  argv[argc++] = (char *) "fix";
  argv[argc++] = (char *) cnf;
  argv[argc++] = (char *) "--silent";
  argv[argc++] = (char *) "--full-skip-limit";
  argv[argc++] = (char *) "100000000";
  argv[argc++] = (char *) "--add-reduced-as-unit";
  argv[argc++] = (char *) "--bsr";
  argv[argc++] = (char *) "--out-file";
  argv[argc++] = (char *) out;
  if (proof) {
    argv[argc++] = (char *) "--proof-file";
    argv[argc++] = (char *) proof;
  }
  argv[argc] = 0;
  _exit (labesat_satsuma_main (argc, argv));
}

void kissat_symmetry_preprocess (const char *input, const char *proof,
                                 double budget, symmetry_outcome *res) {
  memset (res, 0, sizeof *res);
  const double timeout = env_double ("LABESAT_SYMM_TIMEOUT", 60);
  const double max_bytes = env_double ("LABESAT_SYMM_MAXBYTES", 536870912);
  double limit = timeout;
  if (budget > 0 && budget < limit)
    limit = budget;
  if (!input) {
    strcpy (res->reason, "entrada por '<stdin>'");
    return;
  }
  if (proof && !strcmp (proof, "-")) {
    strcpy (res->reason, "prueba por '<stdout>'");
    return;
  }
  if (limit < 1) {
    strcpy (res->reason, "sin tiempo");
    return;
  }
  const char *tmp = getenv ("TMPDIR");
  snprintf (res->dir, sizeof res->dir, "%s/labesat.XXXXXX",
            tmp && *tmp ? tmp : "/tmp");
  if (!mkdtemp (res->dir)) {
    res->dir[0] = 0;
    strcpy (res->reason, "sin directorio temporal");
    return;
  }
  if ((size_t) snprintf (res->path, sizeof res->path, "%s/sb.cnf",
                         res->dir) >= sizeof res->path) {
    rmdir (res->dir);
    res->dir[0] = 0;
    strcpy (res->reason, "ruta temporal demasiado larga");
    return;
  }

  fflush (stdout); /* que el hijo no herede salida sin volcar */
  fflush (stderr);
  const double started = kissat_wall_clock_time ();
  pid_t pid = fork ();
  if (pid < 0) {
    strcpy (res->reason, "fork falló");
    return;
  }
  if (!pid)
    child (input, proof, res->dir, res->path, max_bytes);

  int status = 0;
  bool killed = false;
  for (;;) {
    pid_t w = waitpid (pid, &status, WNOHANG);
    if (w == pid)
      break;
    if (w < 0 && errno != EINTR) {
      status = -1;
      break;
    }
    if (kissat_wall_clock_time () - started > limit) {
      kill (pid, SIGKILL);
      while (waitpid (pid, &status, 0) < 0 && errno == EINTR)
        ;
      killed = true;
      break;
    }
    struct timespec ts = {0, 5 * 1000 * 1000};
    nanosleep (&ts, 0);
  }
  res->seconds = kissat_wall_clock_time () - started;

  struct stat st;
  const bool ok = !killed && status >= 0 && WIFEXITED (status) &&
                  !WEXITSTATUS (status) && !stat (res->path, &st) &&
                  st.st_size > 0;
  if (ok) {
    res->applied = true;
    snprintf (res->reason, sizeof res->reason,
              "satsuma aplicado en %.2f s", res->seconds);
  } else if (killed)
    snprintf (res->reason, sizeof res->reason,
              "satsuma superó el tope de %.0f s", limit);
  else if (WIFEXITED (status) && WEXITSTATUS (status) == EXIT_TOO_BIG)
    snprintf (res->reason, sizeof res->reason,
              "CNF de más de %.0f bytes", max_bytes);
  else if (WIFEXITED (status) && WEXITSTATUS (status) == EXIT_NO_INPUT)
    strcpy (res->reason, "no se pudo leer o descomprimir la entrada");
  else if (WIFEXITED (status))
    snprintf (res->reason, sizeof res->reason,
              "satsuma terminó con código %d en %.2f s",
              WEXITSTATUS (status), res->seconds);
  else
    snprintf (res->reason, sizeof res->reason,
              "satsuma terminó por una señal en %.2f s", res->seconds);
}

void kissat_symmetry_cleanup (symmetry_outcome *res) {
  if (!res->dir[0])
    return;
  const char *keep = getenv ("LABESAT_SYMM_KEEP"); /* diagnóstico */
  if (keep && !strcmp (keep, "1")) {
    fprintf (stderr, "c [symmetry] temporales conservados en %s\n", res->dir);
    res->dir[0] = 0;
    return;
  }
  char path[4096 + 16];
  snprintf (path, sizeof path, "%s/sb.cnf", res->dir);
  unlink (path);
  snprintf (path, sizeof path, "%s/in.cnf", res->dir);
  unlink (path);
  rmdir (res->dir);
  res->dir[0] = 0;
}

#endif
