import streamlit as st
import math
import ast
import html
import operator as op

st.set_page_config(
    page_title="Scientific Calculator",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #f7f7f8; }
    .block-container { max-width: 620px; padding-top: 3rem; padding-bottom: 2rem; }
    .st-key-screen {
        background: #ffffff; border-radius: 22px; padding: 14px 22px 12px; margin: 0 0 18px;
        box-shadow: 0 6px 22px rgba(30,40,80,.08); gap: 0;
    }
    .st-key-screen div[data-testid="stTextInput"] > div,
    .st-key-screen div[data-testid="stTextInput"] > div > div { background: transparent; border: none; box-shadow: none; }
    .st-key-screen input {
        background: transparent !important; border: none !important; box-shadow: none !important;
        text-align: right; color: #8a90a0 !important; font-size: 1.15rem; padding: 4px 0;
    }
    .display-result { color: #1f2430; font-size: 2.6rem; font-weight: 600; text-align: right;
        overflow-wrap: anywhere; line-height: 1.2; }
    /* all keys: round pills like the reference */
    div[data-testid="stButton"] > button {
        width: 100%; min-height: 56px; border-radius: 10px; border: none; box-shadow: none;
        font-size: 1.05rem; font-weight: 500; color: #1f2430; transition: .12s ease;
        box-shadow: 0 3px 8px rgba(30,40,80,.10);
    }
    div[data-testid="stButton"] { filter: drop-shadow(0 3px 4px rgba(30,40,80,.18)); }
    div[data-testid="stButton"] > button:active { transform: scale(.95); }
    /* layout gaps */
    [class*="st-key-pad"], [class*="st-key-sci"] { gap: 12px; }
    [class*="st-key-padrow"], [class*="st-key-scirow"] { gap: 12px; }
    /* scientific keys: tinted, taller to span the 5 keypad rows */
    [class*="st-key-sci_"] button { background: #e8ebf4; min-height: 73px; font-size: 1rem; }
    [class*="st-key-sci_"] button:hover { background: #dde2f0; color: #1f2430; }
    /* digit keys */
    [class*="st-key-num_"] button { background: #ffffff; font-size: 1.35rem; }
    [class*="st-key-num_"] button:hover { background: #f1f3fa; color: #1f2430; }
    [class*="st-key-fn_"] button { background: #ffffff; }
    [class*="st-key-fn_"] button:hover { background: #f1f3fa; color: #1f2430; }
    [class*="st-key-clr_"] button { background: #ffffff; color: #e0524d; font-size: 1.3rem; }
    [class*="st-key-op_"] button { background: #dedede; font-size: 1.5rem; }
    [class*="st-key-op_"] button:hover { background: #d0d0d0; color: #1f2430; }
    [class*="st-key-eq_"] button { background: #5b8def; color: #fff; font-size: 1.6rem; }
    [class*="st-key-eq_"] button:hover { background: #4a7de0; color: #fff; }
</style>
""", unsafe_allow_html=True)

# ---------- State ----------
st.session_state.setdefault("expression", "")
st.session_state.setdefault("result", "0")
st.session_state.setdefault("angle_mode", "DEG")
st.session_state.setdefault("inverse", False)

# ---------- Safe evaluator ----------
BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv,
}
UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

def evaluate(expression: str, angle_mode: str):
    expression = expression.replace("×", "*").replace("÷", "/").replace("^", "**")
    expression = expression.replace("π", "pi").replace("√", "sqrt")

    def sin(x):
        return math.sin(math.radians(x)) if angle_mode == "DEG" else math.sin(x)

    def cos(x):
        return math.cos(math.radians(x)) if angle_mode == "DEG" else math.cos(x)

    def tan(x):
        return math.tan(math.radians(x)) if angle_mode == "DEG" else math.tan(x)

    def asin(x):
        value = math.asin(x)
        return math.degrees(value) if angle_mode == "DEG" else value

    def acos(x):
        value = math.acos(x)
        return math.degrees(value) if angle_mode == "DEG" else value

    def atan(x):
        value = math.atan(x)
        return math.degrees(value) if angle_mode == "DEG" else value

    functions = {
        "sin": sin, "cos": cos, "tan": tan,
        "asin": asin, "acos": acos, "atan": atan,
        "sqrt": math.sqrt,
        "log": math.log10,
        "ln": math.log,
        "abs": abs,
        "exp": math.exp,
        "factorial": math.factorial,
    }
    constants = {"pi": math.pi, "e": math.e}

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp) and type(node.op) in BIN_OPS:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent too large")
            return BIN_OPS[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPS:
            return UNARY_OPS[type(node.op)](walk(node.operand))

        if isinstance(node, ast.Name):
            if node.id in constants:
                return constants[node.id]
            raise ValueError("Unknown name")

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in functions or len(node.args) != 1:
                raise ValueError("Invalid function")
            return functions[name](walk(node.args[0]))

        raise ValueError("Invalid expression")

    tree = ast.parse(expression, mode="eval")
    value = walk(tree)

    if not math.isfinite(value):
        raise ValueError("Result is not finite")

    if abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    return f"{value:.12g}"

def add_token(token):
    st.session_state.expression += token

def clear_all():
    st.session_state.expression = ""
    st.session_state.result = "0"

def backspace():
    st.session_state.expression = st.session_state.expression[:-1]

def toggle_angle():
    st.session_state.angle_mode = "RAD" if st.session_state.angle_mode == "DEG" else "DEG"

def toggle_inverse():
    st.session_state.inverse = not st.session_state.inverse

def toggle_sign():
    e = st.session_state.expression.strip()
    if not e:
        return
    if e.startswith("-(") and e.endswith(")"):
        st.session_state.expression = e[2:-1]
    else:
        st.session_state.expression = f"-({e})"

def add_paren():
    e = st.session_state.expression
    st.session_state.expression += ")" if e.count("(") > e.count(")") and e[-1:] not in "(+-×÷*/^%" else "("

def calculate():
    expr = st.session_state.expression
    if not expr.strip():
        return
    try:
        result = evaluate(expr, st.session_state.angle_mode)
        st.session_state.result = result
    except Exception as exc:
        st.session_state.result = "Error"

# ---------- Screen: keyboard input + result output ----------
# The input is bound to session_state.expression, so typing on the laptop
# keyboard and pressing the on-screen keys edit the same value. Enter = calculate.
with st.container(key="screen"):
    st.text_input(
        "Input",
        key="expression",
        placeholder="0",
        on_change=calculate,
        label_visibility="collapsed",
    )
    result_text = html.escape(st.session_state.result)
    st.markdown(f'<div class="display-result">{result_text}</div>', unsafe_allow_html=True)

# ---------- Keys (same layout as the reference UI) ----------
inv = st.session_state.inverse
T = lambda t: (add_token, (t,))
sci = [
    [("⇆", toggle_inverse, ()),
     (st.session_state.angle_mode.title(), toggle_angle, ()),
     ("√", *T("sqrt(")), ("|x|", *T("abs("))],
    [("sin⁻¹" if inv else "sin", *T("asin(" if inv else "sin(")),
     ("cos⁻¹" if inv else "cos", *T("acos(" if inv else "cos(")),
     ("tan⁻¹" if inv else "tan", *T("atan(" if inv else "tan(")),
     ("π", *T("π"))],
    [("ln", *T("ln(")), ("log", *T("log(")), ("1/x", *T("1/(")), ("e", *T("e"))],
    [("eˣ", *T("exp(")), ("x²", *T("^2")), ("xʸ", *T("^")), ("+/−", toggle_sign, ())],
]
pad = [
    [("C", clear_all, (), "clr"), ("⌫", backspace, (), "clr"), ("%", add_token, ("%",), "fn"), ("÷", add_token, ("÷",), "op")],
    [("7", add_token, ("7",), "num"), ("8", add_token, ("8",), "num"), ("9", add_token, ("9",), "num"), ("×", add_token, ("×",), "op")],
    [("4", add_token, ("4",), "num"), ("5", add_token, ("5",), "num"), ("6", add_token, ("6",), "num"), ("−", add_token, ("-",), "op")],
    [("1", add_token, ("1",), "num"), ("2", add_token, ("2",), "num"), ("3", add_token, ("3",), "num"), ("+", add_token, ("+",), "op")],
    [("( )", add_paren, (), "fn"), ("0", add_token, ("0",), "num"), (".", add_token, (".",), "num"), ("=", calculate, (), "eq")],
]

left, right = st.columns(2, gap="medium")
with left:
    for r, row in enumerate(sci):
        cols = st.columns(4, gap="small")
        for col, (label, fn, args) in zip(cols, row):
            with col:
                st.button(label, key=f"sci_{r}_{label}", use_container_width=True,
                          on_click=fn, args=args)
with right:
    for r, row in enumerate(pad):
        cols = st.columns(4, gap="small")
        for col, (label, fn, args, kind) in zip(cols, row):
            with col:
                st.button(label, key=f"{kind}_{r}_{label}", use_container_width=True,
                          on_click=fn, args=args)

