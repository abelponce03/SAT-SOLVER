#include <stdio.h>
#include "solver.h"

int main()
{
    Solver *S = read_cnf("conflicto.cnf");
    if (!S)
        return 1;

    // Inicial: encolamos el literal 1 (x1 = TRUE)
    enqueue(S, 1, -1); // decisión libre: antecedente = -1

    // Llamamos a propagate
    int confl = propagate(S);

    printf("\nDespués de propagate:\n");
    if (confl == -1)
    {
        printf("No hubo conflicto.\n");
    }
    else
    {
        printf("Conflicto detectado en cláusula %d: (", confl + 1);
        Clause *c = &S->clauses[confl];
        for (int j = 0; j < c->size; j++)
        {
            printf("%d ", c->lits[j]);
        }
        printf(")\n");
    }

    // Mostrar asignaciones y antecedentes
    for (int i = 1; i <= S->nvars; i++)
    {
        int val = S->assign[i];
        if (val == -1)
        {
            printf("Var %d = UNDEF\n", i);
        }
        else
        {
            printf("Var %d = %s (antecedente = %d)\n",
                   i, val ? "TRUE" : "FALSE", S->antecedent[i]);
        }
    }

    // Recorrer cadena de implicación de x2 (causante del conflicto)
    print_implication_chain(S, 2);

    free_solver(S);
    return 0;
}
