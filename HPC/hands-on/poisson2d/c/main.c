/*
 * Copyright (c) 2021, Dirk Pleiter, KTH
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *  * Neither the name of NVIDIA CORPORATION nor the names of its
 *    contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#ifndef NX
#define NX 1024
#endif
#ifndef NY
#define NY 16
#endif
#define NMAX 200000
#define EPS 1e-5

int solver(double *, double *, int, int, double, int);

int main()
{
    double *v;
    double *f;

    // Allocate memory
    v = (double *) malloc(NX * NY * sizeof(double));
    f = (double *) malloc(NX * NY * sizeof(double));

    // Initialise input
    for (int iy = 0; iy < NY; iy++)
        for (int ix = 0; ix < NX; ix++)
        {
            v[NX*iy+ix] = 0.0;

            const double x = 2.0 * ix / (NX - 1.0) - 1.0;
            const double y = 2.0 * iy / (NY - 1.0) - 1.0;
            f[NX*iy+ix] = sin(x + y);
        }

    // Call solver
    solver(v, f, NX, NY, EPS, NMAX);

    //for (int iy = 0; iy < NY; iy++)
    //    for (int ix = 0; ix < NX; ix++)
    //        printf("%d,%d,%e\n", ix, iy, v[iy*NX+ix]);

    // Clean-up
    free(v);
    free(f);

    return 0;
}