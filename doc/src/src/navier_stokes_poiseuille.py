"""
FEniCS tutorial demo program: Incompressible Navier-Stokes equations
for Poisseuille flow in the unit square using the Incremental Pressure
Correction Scheme (IPCS).

  u' + u . grad(u)) - div(sigma) = f
                          div(u) = 0
"""

from __future__ import print_function
from fenics import *
import numpy as np

T = 10.0           # final time
num_steps = 500    # number of time steps
dt = T / num_steps # time step size
nu = 0.5           # kinematic viscosity

# Create mesh and define function spaces
mesh = UnitSquareMesh(16, 16)
V = VectorFunctionSpace(mesh, 'P', 1)
Q = FunctionSpace(mesh, 'P', 1)

# Define boundary conditions
bcu_noslip  = DirichletBC(V, Constant((0, 0)), 'near(x[1], 0)||near(x[1], 1)')
bcp_inflow  = DirichletBC(Q, Constant(1), 'near(x[0], 0)')
bcp_outflow = DirichletBC(Q, Constant(0), 'near(x[0], 1)')
bcu = [bcu_noslip]
bcp = [bcp_inflow, bcp_outflow]

# Define trial and test functions
u = TrialFunction(V)
v = TestFunction(V)
p = TrialFunction(Q)
q = TestFunction(Q)

# Define functions for solutions at previous and current time steps
u0 = Function(V)
u1 = Function(V)
p0 = Function(Q)
p1 = Function(Q)

# Define expressions used in variational forms
U   = 0.5*(u0 + u)
n   = FacetNormal(mesh)
f   = Constant((0, 0))
k   = Constant(dt)
nu  = Constant(nu)

# Define symmetric gradient
def epsilon(u):
    return sym(grad(u))

# Define stress tensor
def sigma(u, p):
    return 2*nu*sym(grad(u)) - p*Identity(len(u))

# Define variational problem for step 1
F1 = dot((u - u0) / k, v)*dx + dot(grad(u0)*u0, v)*dx \
   + inner(sigma(U, p0), epsilon(v))*dx \
   + dot(p0*n, v)*ds - dot(nu*grad(U).T*n, v)*ds \
   - dot(f, v)*dx
a1 = lhs(F1)
L1 = rhs(F1)

# Define variational problem for step 2
a2 = dot(grad(p), grad(q))*dx
L2 = dot(grad(p0), grad(q))*dx - (1/k)*div(u1)*q*dx

# Define variational problem for step 3
a3 = dot(u, v)*dx
L3 = dot(u1, v)*dx - k*dot(grad(p1 - p0), v)*dx

# Assemble matrices
A1 = assemble(a1)
A2 = assemble(a2)
A3 = assemble(a3)

# Apply boundary conditions to matrices
[bc.apply(A1) for bc in bcu]
[bc.apply(A2) for bc in bcp]

# Time-stepping
t = 0
for n in xrange(num_steps):

    # Update current time
    t += dt

    # Step 1: Tentative velocity step
    b1 = assemble(L1)
    [bc.apply(b1) for bc in bcu]
    solve(A1, u1.vector(), b1)

    # Step 2: Pressure correction step
    b2 = assemble(L2)
    [bc.apply(b2) for bc in bcp]
    solve(A2, p1.vector(), b2)

    # Step 3: Velocity correction step
    b3 = assemble(L3)
    solve(A3, u1.vector(), b3)

    # Plot solution
    plot(u1)

    # Compute error at vertices
    u_e = Expression(('x[1]*(1.0 - x[1])', '0'), degree=2)
    u_e = interpolate(u_e, V)
    error = np.abs(u_e.vector().array() - u1.vector().array()).max()
    print('t = %.2f: error = %.3g' % (t, error))

    # Update previous solution
    u0.assign(u1)
    p0.assign(p1)

# Hold plot
interactive()
