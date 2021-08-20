def str_lambda(expr):
    try:
        source = inspect.getsource(expr).strip()
    except:
        return str(expr)
    start = source.find('lambda')
    if start == -1:   # No debería ocurrir
        return expr.__name__
    n_open_par = 1
    start2 = start + 6
    for i, c in enumerate(source[start2:]):
        if c == '(':
            n_open_par += 1
        elif c == ')':
            n_open_par -= 1

        if n_open_par == 0:
            return source[start:start2+i]
    try:
        code = expr.__code__
        return f"{code.co_name}, lineno {code.co_firstline}"
    except:
        return str(expr)
