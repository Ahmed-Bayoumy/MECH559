"""
constrained_optimization_template_python.py
Template: constrained nonlinear optimization with default SciPy settings
No options and no user gradients are provided.
Problem form:
    min_x f(x)
    s.t.  g_i(x) <= 0 (SciPy 'ineq'), h_j(x) = 0 (SciPy 'eq'), and bounds
"""

# SciPy optimizer interface.
from scipy.optimize import minimize


def objective(x):
    # Objective function f(x).
    return (x[0] - 1.0) ** 2 + (x[1] - 2.0) ** 2


def constraint_linear(x):
    # Linear inequality in SciPy form: x0 + 2*x1 - 2.5 <= 0.
    return x[0] + 2.0 * x[1] - 2.5


def constraint_nonlinear(x):
    # Nonlinear inequality in SciPy form: x0^2 + x1^2 - 4 <= 0.
    return x[0] ** 2 + x[1] ** 2 - 4


def constraint_equality(x):
    # Example equality in SciPy form: x0 - x1 = 0.
    return x[0] - x[1]


# Initial guess for decision variables x = [x0, x1].
x0 = [0.5, 0.5]

# Variable bounds: lower <= x_i <= upper.
bounds = [(0.0, 3.0), (0.0, 3.0)]

# Constraint definitions for scipy.optimize.minimize.
# 'ineq' means constraint_fun(x) <= 0.
# 'eq' means constraint_fun(x) = 0.
constraints = [
    {"type": "ineq", "fun": constraint_linear},
    {"type": "ineq", "fun": constraint_nonlinear},
    # Uncomment to activate equality constraint constraint_equality(x) = 0.
    # {"type": "eq", "fun": constraint_equality},
]

# Solve using SciPy defaults (no method/options/jac/hess specified).
result = minimize(objective, x0, bounds=bounds, constraints=constraints)

# Report solution vector, objective value, and solver status.
print("x_opt:", result.x)
print("f_opt:", result.fun)
print("success:", result.success)
print("message:", result.message)
