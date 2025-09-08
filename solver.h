#ifndef SOLVER_H
#define SOLVER_H

// Estructura de cláusula
typedef struct
{
    int *lits;  // literales
    int size;   // número de literales
    int watch1; // índice del primer literal vigilado
    int watch2; // índice del segundo literal vigilado
    int learned; // 1 si es clausula aprendida, 0 si es original
    double activity; // actividad para eliminacion de clausulas 
} Clause;

// Lista dinámica de cláusulas vigiladas por un literal
typedef struct
{
    Clause **data;
    int size;
    int cap;
} WatchList;

//Lista dinamica de clausulas vigiladas por un literal
typedef struct
{
    Clause *data;
    int size;
    int cap;
}ClauseDB;

// Estructura de solver
typedef struct
{
    int nvars;
    int nclauses;
    int *assign; // -1 = UNDEF, 0 = FALSE, 1 = TRUE
    int *level;  // nivel de decisión por variable (para CDCL después)
    int *trail;  // pila de literales asignados
    int trail_size;
    int qhead;       // puntero para propagación
    int *antecedent; // antecedente de cada variable (cláusula que la implicó)

    //Variables para niveles de decision
    int *trail_lim; //Limites de trail por nivel de decision
    int decision_level; 

    //VSIDS heuristica
    double *activity; // actividad de las variables
    double var_inc; // incremento de actividad
    double var_decay; // factor de decrecimiento

    // Restart
    int conflicts;  // numero de conflictos
    int restart_limit; // limite para reiniciar la busqueda

    Clause *clauses;
    ClauseDB learned_clauses; // clausulas aprendidas
    WatchList *watches; // arreglo: uno por literal (2*nvars)
} Solver;

// Utilidades para índices 
static inline int lit_index(int lit, int nvars)
{
    // Mapear [-nvars, ..., -1, 1, ..., nvars] a [0, 1, ..., 2*nvars-1]
    if (lit > 0) {
        return nvars + lit - 1;  // [1..nvars] -> [nvars..2*nvars-1]
    } else {
        return -lit - 1;         // [-nvars..-1] -> [nvars-1..0]
    }
}

// Prototipos de funciones
Solver *read_cnf(const char *filename);
void free_solver(Solver *S);
int propagate(Solver *S);
void enqueue(Solver *S, int lit, int ante_clause);
void print_implication_chain(Solver *S, int var);

int decide(Solver *S);
void backtrack(Solver *S, int level);
int analyze_conflict(Solver *S, int conflict_clause, int *learnt, int *learnt_size);
void add_learned_clause(Solver *S, int *lits, int size);
void bump_activity(Solver *S, int var);
void decay_activities(Solver *S);
int solve(Solver *S);
void restart(Solver *S);

#endif
