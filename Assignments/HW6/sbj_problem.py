"""MECH 559 - HW6: supersonic business jet (SBJ) disciplinary analyses for DMDO 2612.1.

The four discipline models (SSBJ_*.py) are the Python versions of the Sobieski et al. (1998) codes that
ship with the DMDO benchmarks. This module wraps them with the signatures DMDO expects:

* an analysis takes ONE list of inputs and returns a list of outputs;
* an ``opt`` function takes (inputs, outputs, *args) and returns ``[f, [g_1, ..., g_m]]`` with g_j <= 0.

The input and output order of each function is the order of the ``inputs``/``outputs`` rows of the
matching ``DA`` block in ``SBJ_b.yaml`` (repeated in the docstrings below). Flight conditions are fixed:
altitude h = 55,000 ft and Mach number M = 1.4.

Typical use (see ``run_sbj``)::

    from sbj_problem import run_sbj
    session, result = run_sbj("SBJ_b.yaml", work_dir)
    print(result.stop_reason, result.iterations, result.max_inconsistency)
    # coordination history: os.path.join(result.post_dir, "Coordination_history.out")
"""
import contextlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from SSBJ_Aircraft import SSBJ_Aircraft  # noqa: E402
from SSBJ_Aerodynamics import SSBJAerodynamics  # noqa: E402
from SSBJ_Propulsion import SSBJPropulsion  # noqa: E402
from SSBJ_Structures import WingDesignAnalyzer  # noqa: E402

RANGE_MIN = 2000.0  # required range [nm]: g = 1 - range / 2000 <= 0

# Number of calls of each disciplinary analysis (reset with reset_calls()); the opt functions are not counted.
CALLS = {"aircraft": 0, "propulsion": 0, "aerodynamics": 0, "structures": 0}


def reset_calls():
    for k in CALLS:
        CALLS[k] = 0


def _skip_model_search_for_large_subproblems(max_dim=5):
    """OMADS 2612 fits a quadratic model before every MADS search step; on the structures subproblem
    (26 variables, 72 constraints) each fit takes minutes. Skip it when a subproblem has >= max_dim variables
    (only matters if you switch SP 3 or SP 4 to the ``mads`` solver)."""
    try:
        from OMADS._heuristics._exploration import EfficientExploration
    except ImportError:
        return
    original = EfficientExploration.generate_quad_model_points
    if getattr(original, "_hw6_patched", False):
        return

    def small_only(self, *args, **kwargs):
        if self.dim >= max_dim:
            self.candidate_points_set = []
            return None
        return original(self, *args, **kwargs)

    small_only._hw6_patched = True
    EfficientExploration.generate_quad_model_points = small_only


_skip_model_search_for_large_subproblems()

# ----------------------------------------------------------------------------------------------------------
# Disciplinary analyses
# ----------------------------------------------------------------------------------------------------------


def SBJ_aircraft_analysis(x):
    """Aircraft (SP 1). x = [SFC, We, L/D, Ws, Wf] -> [Wt, range]  (Breguet range, Wt = We + Wf + Ws)."""
    CALLS["aircraft"] += 1
    return SSBJ_Aircraft(We=x[1], Ws=x[3], Wf=x[4], SFCp=x[0], LDr=x[2]).SBJ_aircraft_analysis()


def SBJ_propulsion_analysis(x):
    """Propulsion (SP 2). x = [D, T] -> [SFC, We, ESF, Temp_E, Throttle_uA]."""
    CALLS["propulsion"] += 1
    return SSBJPropulsion(D=x[0], T=x[1]).SBJ_propulsion_analysis()


def SBJ_aerodynamics_analysis(x):
    """Aerodynamics (SP 3).

    x = [Wt, ESF, theta, tc, ARw, LAMBDAw, Sref, Sht, ARht, LAMBDAht, Lw, Lht] -> [L, D, L/D, Pg, CLo1, CLo2]
    """
    CALLS["aerodynamics"] += 1
    return SSBJAerodynamics(Wt=x[0], ESFp=x[1], theta=x[2], tc=x[3], ARw=x[4], LAMBDAw=x[5], Sref=x[6],
                            Sht=x[7], ARht=x[8], LAMBDAht=x[9], Lw=x[10], Lht=x[11]).SBJ_aerodynamics_analysis()


def SBJ_structure_analysis(x):
    """Structures (SP 4).

    x = [L, tc, ARw, LAMBDAw, Sref, Sht, ARht, lambda, t1..t9, ts1..ts9] -> [Ws, Wf, theta]
    """
    CALLS["structures"] += 1
    return WingDesignAnalyzer(Lift=x[0], tc=x[1], ARw=x[2], LAMBDAw=x[3], Sref=x[4], Sht=x[5], ARht=x[6],
                              lambdatr=x[7], t=list(x[8:17]), ts=list(x[17:26])).SBJ_structure_analysis()


# ----------------------------------------------------------------------------------------------------------
# Subproblem objectives and constraints (DMDO adds the consistency penalties itself)
# ----------------------------------------------------------------------------------------------------------


def SBJ_aircraft_opt(x, y, *args):
    """SP 1: f = Wt; g = [1 - range / 2000]. y = [Wt, range]."""
    return SSBJ_Aircraft(We=x[1], Ws=x[3], Wf=x[4], SFCp=x[0], LDr=x[2]).SBJ_aircraft_opt(Wt=y[0], range=y[1])


def SBJ_propulsion_opt(x, y, *args):
    """SP 2: f = 0; g = [Temp_E / 1.02 - 1, T * 16168 / Throttle_uA - 1]. y = [SFC, We, ESF, Temp_E, Throttle_uA]."""
    return SSBJPropulsion(D=x[0], T=x[1]).SBJ_propulsion_opt(Temp_E=y[3], Throttle_uA=y[4])


def SBJ_aerodynamics_opt(x, y, *args):
    """SP 3: f = 0; g = [Pg / 1.1 - 1, two lift-balance constraints on CLo]. y = [L, D, L/D, Pg, CLo1, CLo2]."""
    return SSBJAerodynamics(Wt=x[0], ESFp=x[1], theta=x[2], tc=x[3], ARw=x[4], LAMBDAw=x[5], Sref=x[6],
                            Sht=x[7], ARht=x[8], LAMBDAht=x[9], Lw=x[10],
                            Lht=x[11]).SBJ_aerodynamics_opt(Pg=y[3], CLo=[y[4], y[5]])


def SBJ_structure_opt(x, y, *args):
    """SP 4: f = 0; g = the 72 structural constraints g_1 (stresses, buckling, geometry)."""
    return WingDesignAnalyzer(Lift=x[0], tc=x[1], ARw=x[2], LAMBDAw=x[3], Sref=x[4], Sht=x[5], ARht=x[6],
                              lambdatr=x[7], t=list(x[8:17]), ts=list(x[17:26])).SBJ_structure_opt()


BLACKBOXES = {f.__name__: f for f in (SBJ_aircraft_analysis, SBJ_propulsion_analysis, SBJ_aerodynamics_analysis,
                                      SBJ_structure_analysis, SBJ_aircraft_opt, SBJ_propulsion_opt,
                                      SBJ_aerodynamics_opt, SBJ_structure_opt)}


# ----------------------------------------------------------------------------------------------------------
# Running DMDO and checking the result
# ----------------------------------------------------------------------------------------------------------


def run_sbj(yaml_file, working_dir, quiet=True, **session_options):
    """Build and run the DMDO model of ``yaml_file`` (a path, or a dict with the content of a YAML file).

    Returns ``(session, result)``. ``result`` is a ``DMDO.RunResult`` (``stop_reason``, ``iterations``,
    ``objective``, ``max_inconsistency``, ``post_dir``); the coordination history is written to
    ``os.path.join(result.post_dir, "Coordination_history.out")``. Use a new ``working_dir`` for every run.
    """
    from DMDO import Session
    os.makedirs(working_dir, exist_ok=True)
    out = io.StringIO() if quiet else sys.stdout
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        if isinstance(yaml_file, dict):
            session = Session.from_dict(yaml_file, working_dir=working_dir, mdo_name="SBJ",
                                        blackboxes=BLACKBOXES, **session_options)
        else:
            session = Session.from_yaml(yaml_file, working_dir=working_dir, mdo_name="SBJ",
                                        blackboxes=BLACKBOXES, **session_options)
        result = session.run()
    return session, result


def copies(session):
    """List of (name, subproblem, value) of every copy of every variable (t and ts have nine copies each)."""
    return [(v.name, int(v.sp_index), float(v.value)) for v in session.mdo.Coordinator.master_vars]


def design(session):
    """The independent design of a run: shared variables from SP 4, local variables from their owner."""
    c = copies(session)

    def first(name, sp=None):
        return [val for n, s, val in c if n == name and (sp is None or s == sp)]

    z = {n: first(n, 4)[0] for n in ("tc", "ARw", "LAMBDAw", "Sref", "Sht", "ARht")}
    return dict(z, T=first("T")[0], LAMBDAht=first("LAMBDAht")[0], Lw=first("Lw")[0], Lht=first("Lht")[0],
                lam=first("lambda")[0], t=first("t"), ts=first("ts"))


def mda_check(d, tol=1e-12, max_iter=500):
    """Full (Gauss-Seidel) MDA of the independent design ``d`` (as returned by ``design``).

    Returns the coupling variables computed by the disciplines, the range, and the largest constraint value
    of the all-in-one problem (``gmax <= 0`` means feasible). Analysis calls made here are not counted.
    """
    n0 = dict(CALLS)
    Wt, theta, ESF = 25000.0, 10.0, 1.0
    for _ in range(max_iter):
        aero = SSBJAerodynamics(Wt=Wt, ESFp=ESF, theta=theta, tc=d["tc"], ARw=d["ARw"], LAMBDAw=d["LAMBDAw"],
                                Sref=d["Sref"], Sht=d["Sht"], ARht=d["ARht"], LAMBDAht=d["LAMBDAht"], Lw=d["Lw"],
                                Lht=d["Lht"])
        L, D, LD, Pg, CL0, CL1 = aero.SBJ_aerodynamics_analysis()
        struc = WingDesignAnalyzer(Lift=L, tc=d["tc"], ARw=d["ARw"], LAMBDAw=d["LAMBDAw"], Sref=d["Sref"],
                                   Sht=d["Sht"], ARht=d["ARht"], lambdatr=d["lam"], t=list(d["t"]),
                                   ts=list(d["ts"]))
        Ws, Wf, th = struc.SBJ_structure_analysis()
        prop = SSBJPropulsion(D=D, T=d["T"])
        SFC, We, ESFn, TempE, ThrUA = prop.SBJ_propulsion_analysis()
        Wtn = We + Wf + Ws
        err = abs(Wtn - Wt) / Wt + abs(th - theta) / max(1.0, abs(theta)) + abs(ESFn - ESF)
        Wt, theta, ESF = 0.5 * (Wt + Wtn), 0.5 * (theta + th), 0.5 * (ESF + ESFn)
        if err < tol:
            break
    Wt, rng = SSBJ_Aircraft(We=We, Ws=Ws, Wf=Wf, SFCp=SFC, LDr=LD).SBJ_aircraft_analysis()
    g = (list(struc.calculate_constraints()) + list(aero.calculate_constraints(Pg, [CL0, CL1]))
         + list(prop.calculate_constraints(TempE, ThrUA)) + [1.0 - rng / RANGE_MIN])
    CALLS.update(n0)
    return dict(Wt=Wt, Ws=Ws, Wf=Wf, We=We, theta=th, L=L, D=D, LD=LD, ESF=ESFn, SFC=SFC, range=rng,
                gmax=max(g))
