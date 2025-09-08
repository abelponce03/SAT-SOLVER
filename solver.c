#include <stdio.h>
#include <stdlib.h>
#include "solver.h"

// Crear un WatchList vacío
static void init_watchlist(WatchList *wl)
{
    wl->cap = 4;
    wl->size = 0;
    wl->data = malloc(sizeof(Clause *) * wl->cap);
}

static void add_watch(WatchList *wl, Clause *c)
{
    if (wl->size == wl->cap)
    {
        wl->cap *= 2;
        wl->data = realloc(wl->data, sizeof(Clause *) * wl->cap);
    }
    wl->data[wl->size++] = c;
}

Solver *read_cnf(const char *filename)
{
    FILE *f = fopen(filename, "r");
    if (!f)
    {
        perror("No se pudo abrir el archivo");
        return NULL;
    }

    char c;
    int nvars, nclauses;

    // Saltar comentarios 'c'
    while ((c = fgetc(f)) == 'c')
    {
        while ((c = fgetc(f)) != '\n' && c != EOF)
            ;
    }
    ungetc(c, f);

    // Leer encabezado
    if (fscanf(f, "p cnf %d %d", &nvars, &nclauses) != 2)
    {
        printf("Formato DIMACS inválido\n");
        fclose(f);
        return NULL;
    }

    // Inicializar el solver
    Solver *S = malloc(sizeof(Solver));
    S->nvars = nvars;
    S->nclauses = nclauses;
    S->clauses = malloc(sizeof(Clause) * nclauses);
    S->assign = malloc(sizeof(int) * (nvars + 1));
    S->level = malloc(sizeof(int) * (nvars + 1));
    S->antecedent = malloc(sizeof(int) * (nvars + 1));

    // Inicializar asignaciones y niveles
    for (int v = 1; v <= nvars; v++)
    {
        S->assign[v] = -1; // sin asignar
        S->level[v] = -1;
        S->antecedent[v] = -1; // sin antecedente
    }

    S->trail = malloc(sizeof(int) * (nvars + 1));
    S->trail_size = 0;
    S->qhead = 0;

    S->watches = malloc(sizeof(WatchList) * (2 * nvars));

    // Inicializar listas de vigilancia
    for (int i = 0; i < 2 * nvars; i++)
    {
        init_watchlist(&S->watches[i]);
    }

    // Leer cláusulas
    for (int i = 0; i < nclauses; i++)
    {
        int lit, count = 0;
        int *tmp = malloc(sizeof(int) * (nvars + 1));
        while (fscanf(f, "%d", &lit) == 1 && lit != 0)
        {
            tmp[count++] = lit;
        }

        S->clauses[i].lits = malloc(sizeof(int) * count);
        for (int j = 0; j < count; j++)
        {
            S->clauses[i].lits[j] = tmp[j];
        }
        S->clauses[i].size = count;

        if (count >= 2)
        {
            S->clauses[i].watch1 = 0;
            S->clauses[i].watch2 = 1;
        }
        else if (count == 1)
        {
            S->clauses[i].watch1 = 0;
            S->clauses[i].watch2 = -1;
        }
        else
        {
            S->clauses[i].watch1 = -1;
            S->clauses[i].watch2 = -1;
        }

        free(tmp);
    }

    // Para cada cláusula, registrar sus dos vigilados
    for (int i = 0; i < nclauses; i++)
    {
        Clause *c = &S->clauses[i];
        if (c->watch1 >= 0)
        {
            int lit1 = c->lits[c->watch1];
            add_watch(&S->watches[lit_index(lit1, nvars)], c);
        }
        if (c->watch2 >= 0)
        {
            int lit2 = c->lits[c->watch2];
            add_watch(&S->watches[lit_index(lit2, nvars)], c);
        }
    }

    fclose(f);
    return S;
}

void free_solver(Solver *S)
{
    for (int i = 0; i < S->nclauses; i++)
    {
        free(S->clauses[i].lits);
    }
    free(S->clauses);

    for (int i = 0; i < 2 * S->nvars; i++)
    {
        free(S->watches[i].data);
    }
    free(S->watches);
    free(S->assign);
    free(S->level);
    free(S->trail);
    free(S->antecedent);
    free(S);
}

static inline int var_of(int lit) { return (lit > 0) ? lit : -lit; }

static inline int value_of(Solver *S, int lit)
{
    int v = var_of(lit);
    int val = S->assign[v];
    if (val == -1)
        return -1; // UNDEF
    return (lit > 0) ? val : 1 - val;
}

void enqueue(Solver *S, int lit, int ante_clause)
{
    int v = var_of(lit);
    if (S->assign[v] != -1)
        return; // ya asignado
    S->assign[v] = (lit > 0) ? 1 : 0;
    S->antecedent[v] = ante_clause; // -1 si es decisión
    S->trail[S->trail_size++] = lit;
}

// Devuelve -1 si no hay conflicto
// Si hay conflicto, devuelve el índice de la cláusula conflictiva
int propagate(Solver *S)
{
    while (S->qhead < S->trail_size)
    {
        int lit = S->trail[S->qhead++]; // literal recién asignado

        // Mirar todas las cláusulas que vigilan -lit
        WatchList *wl = &S->watches[lit_index(-lit, S->nvars)];
        
        // Usamos un índice que puede decrementarse cuando removemos elementos
        int i = 0;
        while (i < wl->size)
        {
            Clause *c = wl->data[i];

            // Manejar cláusulas unitarias de forma especial
            if (c->size == 1) {
                // Si el único literal es falso, tenemos un conflicto
                if (value_of(S, c->lits[0]) == 0) {
                    return (int)(c - S->clauses); // conflicto
                }
                i++; // No es conflicto, continuar
                continue;
            }

            // Determinar cuál vigilado de la cláusula es -lit
            int *watch_pos;
            int other_pos;
            
            if (c->lits[c->watch1] == -lit) {
                watch_pos = &c->watch1;
                other_pos = c->watch2;
            } else if (c->lits[c->watch2] == -lit) {
                watch_pos = &c->watch2;
                other_pos = c->watch1;
            } else {
                // Este literal no es vigilado por esta cláusula
                i++;
                continue;
            }
            
            int other_lit = c->lits[other_pos];

            if (value_of(S, other_lit) == 1)
            {
                i++; // cláusula ya satisfecha, continuar
                continue;
            }

            // Intentar mover el vigilado a otro literal no FALSE
            int found = 0;
            for (int k = 0; k < c->size; k++)
            {
                if (k == c->watch1 || k == c->watch2)
                    continue;
                if (value_of(S, c->lits[k]) != 0)
                {
                    // Mover el vigilado
                    *watch_pos = k;
                    add_watch(&S->watches[lit_index(c->lits[k], S->nvars)], c);
                    
                    // Remover de la lista actual (intercambiar con el último y decrementar tamaño)
                    wl->data[i] = wl->data[wl->size - 1];
                    wl->size--;
                    
                    found = 1;
                    break;
                }
            }

            if (found)
            {
                // No incrementamos i porque pusimos un elemento nuevo en la posición i
                continue;
            }

            // No se pudo mover → cláusula unitaria o conflicto
            if (value_of(S, other_lit) == -1)
            {
                // implicación: guardamos qué cláusula la produjo
                enqueue(S, other_lit, (int)(c - S->clauses));
                i++; // continuar con el siguiente
            }
            else
            {
                // conflicto
                return (int)(c - S->clauses); // índice de la cláusula conflictiva
            }
        }
    }
    return -1; // no hubo conflicto
}

void print_implication_chain(Solver *S, int var)
{
    printf("Cadena de implicación para var %d:\n", var);

    while (var > 0 && S->antecedent[var] != -1)
    {
        int cid = S->antecedent[var];
        Clause *c = &S->clauses[cid];

        printf("  Var %d fue implicada por cláusula %d: (", var, cid + 1);
        for (int j = 0; j < c->size; j++)
        {
            printf("%d ", c->lits[j]);
        }
        printf(")\n");

        // retrocedemos: tomamos algún literal de esa cláusula que ya estaba asignado
        // para seguir la cadena
        int next_var = -1;
        for (int j = 0; j < c->size; j++)
        {
            int lit = c->lits[j];
            int v = var_of(lit);
            if (v != var && S->assign[v] != -1)
            {
                next_var = v;
                break;
            }
        }
        if (next_var == -1)
            break;
        var = next_var;
    }

    if (var > 0 && S->antecedent[var] == -1)
    {
        printf("  Var %d fue una DECISIÓN inicial.\n", var);
    }
}


// Incrementa la actividad de una variable
void bump_activity(Solver *S, int var)
{   
    // Aumentar la actividad
    S->activity[var] += S->var_inc;
    if (S->activity[var] > 1e100)
    {
        // Reescalar para evitar overflow
        for (int v = 1; v <= S->nvars; v++)
        {
            S->activity[v] *= 1e-100;
        }
        S->var_inc *= 1e-100;
    }
}

// Decrementa la actividad de todas las variables
void decay_activities(Solver *S)
{
    S->var_inc /= S->var_decay;
}

// Decide la siguiente variable a asignar
int decide(Solver *S)
{
    // Encontrar variable no asignada con mayor actividad
    int best_var = -1;
    double best_activity = -1.0;

    // Buscar la variable no asignada con mayor actividad
    for (int v = 1; v <= S->nvars; v++)
    {
        if (S->assign[v] == -1 && S->activity[v] > best_activity)
        {
            best_activity = S->activity[v];
            best_var = v;
        }
    }

    if (best_var == -1) return 0; // Todas las variables asignadas
    
    // Incrementar el nivel de decisión
    S->decision_level++;
    S->trail_lim[S->decision_level] = S->trail_size;

    // Decidir polaridad (TRUE por defecto)
    enqueue(S, best_var, -1); // -1 indica que es una decisión
    
    return 1; 
}


// Retrocede al nivel de decisión dado
void backtrack(Solver *S, int level)
{
    if (S->decision_level <= level) return; // No hay nada que hacer

    // Retroceder al nivel de decisión dado
    int trail_pos = S->trail_lim[level + 1];

    // Actualizar el nivel de decisión
    for (int i = S->trail_size - 1; i >= trail_pos; i--)
    {
        int lit = S->trail[i];
        int var = var_of(lit);
        S->assign[var] = -1; // desasignar
        S->level[var] = -1; // resetear nivel
        S->antecedent[var] = -1; // resetear antecedente
    }
    
    // Actualizar el tamaño del trail y qhead
    S->trail_size = trail_pos;
    S->qhead = trail_pos;
    S->decision_level = level;
}

int analyze_conflict(Solver *S, int conflict_clause, int *learnt, int *learnt_size)
{
    Clause *c = &S->clauses[conflict_clause];
    int counter = 0;
    int p = -1; // literal UIP
    *learnt_size = 0;

    // Marcar literales del conflicto 
    int *seen = calloc(S->nvars + 1, sizeof(int));

    do
    {
        // Agregar literales de la cláusula conflictiva
        for (int i = 0; i < c->size; i++)
        {
            int lit = c->lits[i];
            int var = var_of(lit);

            if (!seen[var] && S->level[var] > 0)
            {
                seen[var] = 1;
                bump_activity(S, var);

                // Contar cuántas variables están en el nivel de decisión actual
                if (S->level[var] == S->decision_level) counter++;
                
                // Agregar a la cláusula aprendida
                else learnt[(*learnt_size)++] = lit;
            }
        }

        // Buscar el siguiente literal en el trail
        while (!seen[var_of(S->trail[--S->trail_size])]);
        
        p = S->trail[S->trail_size + 1];  // último literal procesado
        c = &S->clauses[S->antecedent[var_of(p)]]; // cláusula que implicó p
        seen[var_of(p)] = 0; // desmarcar
        counter--;

    } while (counter > 0);

    // p es el UIP, agregarlo negado
    learnt[(*learnt_size)++] = -p;

    // Encontrar el nivel de retroceso
    int backtrack_level = 0;
    for (int i = 0; i < *learnt_size - 1; i++)
    {
        int var = var_of(learnt[i]);
        if (S->level[var] > backtrack_level)
            backtrack_level = S->level[var];
    }

    free(seen);
    return backtrack_level;
}

int solve(Solver *S)
{
    while (1)
    {
        //Propagar
        int confl = propagate(S);

        if (confl != -1)
        {
            //Conflicto encontrado
            S->conflicts++;

            if (S->decision_level == 0)
            {
                return 0; // UNSAT
            }

            // Analizar conflicto y aprender cláusula
            int learnt[S->nvars];
            int learnt_size;
            int backtrack_level = analyze_conflict(S, confl, learnt, &learnt_size);

            // Retroceder
            backtrack(S, backtrack_level);

            // Agregar clausula aprendida
            add_learned_clause(S, learnt, learnt_size);

            //Decaer actividades
            decay_activities(S);

            // Reiniciar si es necesario
            if (S->conflicts >= S->restart_limit)
            {
                restart(S);
                S->restart_limit *= 1.5; // Aumentar el límite para la próxima vez
            }
        }
        else
        {
            // sin conlficto, decidir siguiente variable
            if (!decide(S)) return 1; // SAT
        }
    }
}

void restart(Solver *S)
{
    backtrack(S, 0);
    S->conflicts = 0;
}