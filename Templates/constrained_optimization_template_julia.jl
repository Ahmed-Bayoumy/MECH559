# constrained_optimization_template_julia.jl
# Template: constrained nonlinear optimization with default Ipopt settings via JuMP
# No solver options and no user gradients are provided.
# Problem form:
#   min_x f(x)
#   s.t.  linear/nonlinear constraints and variable bounds

# Modeling package and default nonlinear optimizer.
using JuMP
using Ipopt

# Create optimization model with the default Ipopt optimizer settings.
model = Model(Ipopt.Optimizer)

# Decision variables with bound constraints and initial values.
@variable(model, 0.0 <= x1 <= 3.0, start = 0.5)
@variable(model, 0.0 <= x2 <= 3.0, start = 0.5)

# Linear inequality constraint.
@constraint(model, x1 + 2.0 * x2 <= 2.5)

# Nonlinear inequality constraint.
@NLconstraint(model, x1^2 + x2^2 <= 4.0)

# Optional equality constraint example (uncomment if needed):
# @constraint(model, x1 - x2 == 0.0)

# Nonlinear objective function.
@NLobjective(model, Min, (x1 - 1.0)^2 + (x2 - 2.0)^2)

# Solve with default Ipopt settings.
optimize!(model)

# Report solver termination status and solution values.
println("termination_status: ", termination_status(model))
println("x_opt = [", value(x1), ", ", value(x2), "]")
println("f_opt = ", objective_value(model))
