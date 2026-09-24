/* xor_detect.c — cuenta restricciones XOR codificadas en CNF (research/06).
   Una XOR de k variables (3..MAXK) aparece como los 2^(k-1) patrones de signo
   de la misma paridad.  Informa: nº de XOR, variables cubiertas y la mayor
   componente conexa (en nº de XOR).  Uso: xz -dc f.cnf.xz | ./xor_detect */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define MAXK 6
typedef struct { int k; int v[MAXK]; unsigned mask; } rec;
static rec *R; static size_t n, cap;
static int cmpv(const void*a,const void*b){int x=abs(*(int*)a),y=abs(*(int*)b);return x-y;}
static int cmprec(const void*a,const void*b){const rec*x=a,*y=b;if(x->k!=y->k)return x->k-y->k;for(int i=0;i<x->k;i++)if(x->v[i]!=y->v[i])return x->v[i]<y->v[i]?-1:1;return (x->mask>y->mask)-(x->mask<y->mask);}
static int *par; static int findp(int x){while(par[x]!=x){par[x]=par[par[x]];x=par[x];}return x;}
int main(){
  int nv=0,lit[64],len=0; char line[1<<16];
  long long ncl=0;
  while(fgets(line,sizeof line,stdin)){
    if(line[0]=='c')continue;
    if(line[0]=='p'){sscanf(line,"p cnf %d",&nv);continue;}
    char*p=line; char*e;
    for(;;){long x=strtol(p,&e,10); if(e==p)break; p=e;
      if(x==0){ncl++; if(len>=3&&len<=MAXK){int tmp[MAXK];memcpy(tmp,lit,len*sizeof(int));qsort(tmp,len,sizeof(int),cmpv);
          int ok=1;for(int i=1;i<len;i++)if(abs(tmp[i])==abs(tmp[i-1]))ok=0;
          if(ok){ if(n==cap){cap=cap?2*cap:1<<16;R=realloc(R,cap*sizeof(rec));}
            rec*r=&R[n++]; r->k=len; r->mask=0; for(int i=0;i<len;i++){r->v[i]=abs(tmp[i]); if(tmp[i]<0)r->mask|=1u<<i;} }}
        len=0;} else if(len<64) lit[len++]=(int)x; }
  }
  qsort(R,n,sizeof(rec),cmprec);
  par=malloc((nv+2)*sizeof(int)); for(int i=0;i<=nv+1;i++)par[i]=i;
  char*cov=calloc(nv+2,1); long long nx=0, nxk[MAXK+1]={0};
  int *xcomp=NULL; size_t xn=0,xc=0;  /* primer var de cada xor */
  for(size_t i=0;i<n;){ size_t j=i; while(j<n&&R[j].k==R[i].k&&!memcmp(R[j].v,R[i].v,R[i].k*sizeof(int)))j++;
    int k=R[i].k; int cnt[2]={0,0}; unsigned last=~0u;
    for(size_t t=i;t<j;t++){ if(R[t].mask==last)continue; last=R[t].mask; cnt[__builtin_popcount(R[t].mask)&1]++; }
    int need=1<<(k-1);
    if(cnt[0]==need||cnt[1]==need){ nx++; nxk[k]++;
      for(int q=0;q<k;q++){cov[R[i].v[q]]=1; if(R[i].v[q]<=nv){int a=findp(R[i].v[0]),b=findp(R[i].v[q]); if(a!=b)par[a]=b;}}
      if(xn==xc){xc=xc?2*xc:1024;xcomp=realloc(xcomp,xc*sizeof(int));} xcomp[xn++]=R[i].v[0]; }
    i=j; }
  long long covered=0; for(int i=1;i<=nv;i++)covered+=cov[i];
  /* mayor componente en nº de XOR */
  int *cntc=calloc(nv+2,sizeof(int)); int best=0;
  for(size_t i=0;i<xn;i++){int r=findp(xcomp[i]); if(++cntc[r]>best)best=cntc[r];}
  printf("vars=%d clauses=%lld xors=%lld k3=%lld k4=%lld k5=%lld k6=%lld covered=%lld maxcomp=%d\n",nv,ncl,nx,nxk[3],nxk[4],nxk[5],nxk[6],covered,best);
  return 0;
}
