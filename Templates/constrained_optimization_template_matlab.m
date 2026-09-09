% constrained_optimization_template_matlab.m
% Template: constrained nonlinear optimization with default fmincon settings
% Requires Optimization Toolbox
% Problem form:
%   min_x f(x)
%   s.t.  A*x <= b, Aeq*x = beq, lb <= x <= ub, c(x) <= 0, ceq(x) = 0

% Reset workspace variables and clear command window.
clear; clc;

% Initial guess for decision variables x = [x1; x2].
x0 = [0.5; 0.5];

% Linear inequality constraint: x1 + 2*x2 <= 2.5.
A = [1, 2];
b = 2.5;

% Linear equality constraints Aeq*x = beq (left empty here).
Aeq = [];
beq = [];

% Bound constraints for each variable.
lb = [0; 0];
ub = [3; 3];

% Objective and nonlinear constraints are defined as local functions below.
fun = @objective_function;
nonlcon = @nonlinear_constraints;

% Solve with default fmincon settings (no options, no user gradients).
[x_opt, f_opt, exitflag, output] = fmincon(fun, x0, A, b, Aeq, beq, lb, ub, nonlcon);

% Report optimized design, objective value, and solver status.
fprintf('x_opt = [%.6f, %.6f]\n', x_opt(1), x_opt(2));
fprintf('f_opt = %.6f\n', f_opt);
fprintf('exitflag = %d\n', exitflag);
disp(output);


function f = objective_function(x)
% Objective function f(x).
f = (x(1) - 1)^2 + (x(2) - 2)^2;
end


function [c, ceq] = nonlinear_constraints(x)
% Nonlinear inequality: c(x) <= 0.
c = x(1)^2 + x(2)^2 - 4;

% Nonlinear equality: ceq(x) = 0 (none in this template).
ceq = [];
end
