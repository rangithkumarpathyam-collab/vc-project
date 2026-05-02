import sys
import json
import traceback
from sympy import symbols, Function, Eq, dsolve, classify_ode, sympify, latex, diff, integrate, exp, simplify

def generate_linear_steps(eq, y, x):
    # Form: y' + P(x)y = Q(x)
    # We will just extract the integrating factor conceptually
    steps = []
    steps.append({"title": "Identify equation type", "detail": "This is a First-Order Linear Differential Equation.", "latex": ""})
    steps.append({"title": "Standard Form", "detail": "Ensure the equation is in the form y' + P(x)y = Q(x)", "latex": ""})
    steps.append({"title": "Integrating Factor", "detail": "Compute the integrating factor \u03bc(x) = e^{\u222bP(x)dx}", "latex": "\\mu(x) = e^{\\int P(x) dx}"})
    steps.append({"title": "Multiply and Integrate", "detail": "Multiply both sides by \u03bc(x) and integrate to solve for y(x).", "latex": "y(x) = \\frac{1}{\\mu(x)} \\left( \\int \\mu(x) Q(x) dx + C \\right)"})
    return steps

def generate_separable_steps(eq, y, x):
    steps = []
    steps.append({"title": "Identify equation type", "detail": "This is a Separable Differential Equation.", "latex": ""})
    steps.append({"title": "Separate Variables", "detail": "Rearrange the equation so all y terms are on one side with dy, and all x terms on the other with dx.", "latex": "f(y) dy = g(x) dx"})
    steps.append({"title": "Integrate Both Sides", "detail": "Integrate both sides of the equation.", "latex": "\\int f(y) dy = \\int g(x) dx"})
    steps.append({"title": "Solve for y", "detail": "Solve the integrated equation explicitly for y(x) if possible, and add the constant of integration C.", "latex": ""})
    return steps

def generate_bernoulli_steps(eq, y, x):
    steps = []
    steps.append({"title": "Identify equation type", "detail": "This is a Bernoulli Differential Equation.", "latex": "y' + P(x)y = Q(x)y^n"})
    steps.append({"title": "Divide by y^n", "detail": "Divide the entire equation by y^n to prepare for substitution.", "latex": "y^{-n}y' + P(x)y^{1-n} = Q(x)"})
    steps.append({"title": "Substitution", "detail": "Let v = y^{1-n}. Then v' = (1-n)y^{-n}y'.", "latex": "v = y^{1-n}"})
    steps.append({"title": "Solve Linear Equation", "detail": "Substitute v into the equation to get a linear ODE in terms of v, and solve using the integrating factor method.", "latex": ""})
    steps.append({"title": "Back-substitute", "detail": "Replace v with y^{1-n} and solve for y.", "latex": ""})
    return steps

def generate_exact_steps(eq, y, x):
    steps = []
    steps.append({"title": "Identify equation type", "detail": "This is an Exact Differential Equation.", "latex": "M(x, y) dx + N(x, y) dy = 0"})
    steps.append({"title": "Check Exactness", "detail": "Verify that \u2202M/\u2202y = \u2202N/\u2202x.", "latex": "\\frac{\\partial M}{\\partial y} = \\frac{\\partial N}{\\partial x}"})
    steps.append({"title": "Integrate M w.r.t x", "detail": "Integrate M(x,y) with respect to x to find the potential function \u03a8(x,y) up to a function of y.", "latex": "\\Psi(x, y) = \\int M(x, y) dx + h(y)"})
    steps.append({"title": "Find h(y)", "detail": "Differentiate \u03a8 with respect to y, set it equal to N(x,y), and solve for h'(y), then integrate to find h(y).", "latex": ""})
    steps.append({"title": "Final Solution", "detail": "The implicit solution is \u03a8(x,y) = C.", "latex": ""})
    return steps

def solve_equation(equation_str):
    try:
        x = symbols('x')
        y_func = Function('y')
        y = y_func(x)
        
        eq_str = equation_str.replace("y'", "diff(y(x), x)")
        eq_str = eq_str.replace("dy/dx", "diff(y(x), x)")
        eq_str = eq_str.replace("y", "y(x)")
        eq_str = eq_str.replace("y(x)(x)", "y(x)")
        eq_str = eq_str.replace("diff(y(x)(x), x)", "diff(y(x), x)")
        
        if '=' in eq_str:
            lhs_str, rhs_str = eq_str.split('=', 1)
            lhs = sympify(lhs_str, locals={'y': y_func, 'x': x})
            rhs = sympify(rhs_str, locals={'y': y_func, 'x': x})
            eq = Eq(lhs, rhs)
        else:
            eq = sympify(eq_str, locals={'y': y_func, 'x': x})
            
        hints = classify_ode(eq, y)
        best_hint = hints[0] if hints else "unknown"
        
        solution = dsolve(eq, y)
        sol_latex = latex(solution)
        
        # Determine specific steps based on hint
        if "1st_linear" in best_hint:
            steps = generate_linear_steps(eq, y, x)
        elif "separable" in best_hint:
            steps = generate_separable_steps(eq, y, x)
        elif "Bernoulli" in best_hint or "bernoulli" in best_hint.lower():
            steps = generate_bernoulli_steps(eq, y, x)
        elif "1st_exact" in best_hint:
            steps = generate_exact_steps(eq, y, x)
        else:
            steps = [
                {"title": "Identify equation type", "detail": f"Classified as: {best_hint.replace('_', ' ')}", "latex": ""},
                {"title": "Apply Algorithm", "detail": "Use specialized integration techniques for this type.", "latex": ""},
            ]
            
        steps.append({"title": "Final Answer", "detail": "After integration and simplification:", "latex": sol_latex})
        
        # Generate Plot Points (heuristically substituting C1=1, C2=1 etc)
        plot_data = []
        try:
            import numpy as np
            from sympy import lambdify
            # Substitute C1, C2 with 1
            sol_expr = solution.rhs
            for sym in sol_expr.free_symbols:
                if str(sym).startswith('C'):
                    sol_expr = sol_expr.subs(sym, 1)
            
            # Lambdify
            f = lambdify(x, sol_expr, 'numpy')
            x_vals = np.linspace(-5, 5, 100)
            y_vals = f(x_vals)
            
            for i in range(len(x_vals)):
                # Skip complex or inf/nan values
                if np.isreal(y_vals[i]) and not np.isnan(y_vals[i]) and not np.isinf(y_vals[i]):
                    # clamp values to avoid huge numbers breaking the chart
                    y_val = float(y_vals[i])
                    if abs(y_val) < 1000:
                        plot_data.append({"x": float(f"{x_vals[i]:.2f}"), "y": float(f"{y_val:.2f}")})
        except Exception as graph_e:
            pass # Ignore graphing errors if equation is implicit or too complex
            
        result = {
            "success": True,
            "equation": latex(eq),
            "type": best_hint.replace('_', ' ').title(),
            "solution_latex": sol_latex,
            "steps": steps,
            "plotData": plot_data
        }
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        eq_str = sys.argv[1]
    else:
        eq_str = sys.stdin.read().strip()
        
    if not eq_str:
        print(json.dumps({"success": False, "error": "No equation provided"}))
        sys.exit(1)
        
    res = solve_equation(eq_str)
    print(json.dumps(res))
