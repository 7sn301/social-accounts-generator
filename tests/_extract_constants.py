"""
استخراج الثوابت من app.py بدون تنفيذ الكود
معرّف: BSR-V217L-TEST-EXTRACT-AHMAD-20260613
"""
import ast
import os

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app.py')


def extract_constants():
    """استخراج الثوابت العلوية من app.py بتحليل AST"""
    with open(APP_PATH, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    constants = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                name = target.id
                if name.isupper() or name in ('TIKWM_BASE', 'USER_AGENTS', 'PROXY_CHAIN',
                                              'PATTERNS', 'COUNTRY_AR'):
                    try:
                        value = ast.literal_eval(node.value)
                        constants[name] = value
                    except (ValueError, SyntaxError):
                        pass
    return constants


CONSTANTS = extract_constants()
