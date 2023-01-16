! Copyright (c) 2021, Dirk Pleiter, KTH
!
! This source code is in parts based on code from Jiri Kraus (NVIDIA) and
! Andreas Herten (Forschungszentrum Juelich)
!
! Redistribution and use in source and binary forms, with or without
! modification, are permitted provided that the following conditions
! are met:
!  * Redistributions of source code must retain the above copyright
!    notice, this list of conditions and the following disclaimer.
!  * Redistributions in binary form must reproduce the above copyright
!    notice, this list of conditions and the following disclaimer in the
!    documentation and/or other materials provided with the distribution.
!  * Neither the name of NVIDIA CORPORATION nor the names of its
!    contributors may be used to endorse or promote products derived
!    from this software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
! EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
! IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
! PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
! CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
! EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
! PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
! PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
! OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
! (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
! OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

subroutine solver(v, f, nx, ny, eps, nmax)

    implicit none

    integer, intent(in)                             :: nx
    integer, intent(in)                             :: ny
    real(kind=8), intent(inout), dimension(nx,ny)   :: v
    real(kind=8), intent(in), dimension(nx,ny)      :: f
    real(kind=8), intent(in)                        :: eps
    integer, intent(in)                             :: nmax

    integer                                         :: n
    real(kind=8)                                    :: e
    real(kind=8)                                    :: w
    real(kind=8)                                    :: d
    real(kind=8), dimension(:,:), allocatable       :: vp

    integer                                         :: ix
    integer                                         :: iy
    integer                                         :: ifail

    n = 0
    e = 2.0 * eps

    allocate(vp(nx,ny), stat = ifail)

    do while ((e > eps) .and. (n < nmax))
        e = 0.0

        do ix = 2, nx-1
            do iy = 2, ny-1
                vp(ix,iy) = -0.25 * (f(ix,iy) - (v(ix+1,iy  ) + v(ix-1,iy  ) + &
                                                 v(ix  ,iy+1) + v(ix,  iy-1)))

                d = abs(vp(ix,iy) - v(ix,iy))
                e = max(d, e)
            end do
        end do
        
        ! Update v and compute error as well as error weight factor

        w = 0.0

        do ix = 2, nx-1
            do iy = 2, ny-1
                v(ix,iy) = vp(ix,iy)
                w = w + abs(v(ix,iy))
            end do
        end do

        do ix = 2, nx-1
            v(ix, 1) = v(ix,ny-1)
            v(ix,ny) = v(ix,   2)
            w = w + abs(v(ix,1)) + abs(v(ix,ny))
        end do

        do iy = 2, ny-1
            v( 1,iy) = v(nx-1,iy)
            v(nx,iy) = v(   2,iy)
            w = w + abs(v(1,iy)) + abs(v(nx,iy))
        end do

        w = w / (nx * ny)
        e = e / w

        !if (mod(n,10) .eq. 0) then
        !    write(*,*) n, e
        !end if
        
        n = n + 1
    end do

    deallocate(vp)

    if (e < eps) then
        write(*,*) 'Converged after', n, 'iterations (nx=', nx, ', ny=', ny, ', e=', e, ')'
    else
        write(*,*) 'ERROR: Failed to converge'
    end if

end subroutine
