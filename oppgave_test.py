"""Automatisk retting av FY2-07-iss-og-planetbaner.

Hver sjekk i SJEKKER er én deltest, og poengene fordeles likt på dem.
De samme sjekkene ligger i "Test løsningen din"-cellen nederst i notebooken.
"""
import pytest

from notebook_loader import last_notebook

def naer(a, b, rel=1e-3):
    """Sant hvis tallet a er innenfor rel (relativt) av b."""
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    if b == 0:
        return abs(a) < 1e-9
    return abs(a - b) <= rel * abs(b)


def S(tekst):
    """Gjør tekst om til et sympy-uttrykk, f.eks. S("x**2 - 1")."""
    import sympy
    return sympy.sympify(tekst, locals={n: sympy.Symbol(n) for n in ("N", "O", "Q", "S")})


def lik(a, b):
    """Sant hvis a og b er matematisk like.

    Lister og mengder sammenlignes uten hensyn til rekkefølge, tupler (koordinater) i rekkefølge.
    """
    import sympy
    if a is None:
        return False
    if isinstance(b, tuple):
        if not isinstance(a, (tuple, list, sympy.Tuple)) or len(a) != len(b):
            return False
        return all(lik(x, y) for x, y in zip(a, b))
    if isinstance(b, (list, set)):
        if isinstance(a, sympy.FiniteSet):
            a = list(a)
        if not isinstance(a, (list, tuple, set)) or len(a) != len(b):
            return False
        rest = list(a)
        for y in b:
            for i, x in enumerate(rest):
                if lik(x, y):
                    del rest[i]
                    break
            else:
                return False
        return True
    if isinstance(b, dict):
        if not isinstance(a, dict) or len(a) != len(b):
            return False
        a = {str(k): v for k, v in a.items()}
        return all(str(k) in a and lik(a[str(k)], v) for k, v in b.items())
    try:
        a, b = sympy.sympify(a), sympy.sympify(b)
    except (sympy.SympifyError, TypeError):
        return False
    vanlige = lambda u: u.subs({s: sympy.Symbol(s.name) for s in u.free_symbols})
    a, b = vanlige(a), vanlige(b)
    if isinstance(a, sympy.Set) or isinstance(b, sympy.Set):
        return a == b
    if getattr(b, "is_Relational", False):
        return a == b
    try:
        return sympy.simplify(a - b) == 0
    except TypeError:
        return a == b

oppgave = last_notebook("oppgave")

SJEKKER = [
    ('1_fart', 'iss_fart_ms skal gjøre om fra km/h til m/s', "naer(iss_fart_ms({'name': 'iss', 'id': 25544, 'latitude': -4.42, 'longitude': -139.27, 'altitude': 423.7186731319, 'velocity': 27563.405897618, 'visibility': 'daylight', 'timestamp': 1793043901, 'units': 'kilometers'}), 27563.405897618 / 3.6)"),
    ('1_teori', 'banefart_teori(420) skal gi ca. 7660 m/s', 'naer(banefart_teori(420), (6.674e-11 * 5.972e24 / (6.371e6 + 420e3))**0.5)'),
    ('3_A', "les_verdi(tekst, 'A =') skal gi store halvakse til Mars", "naer(les_verdi('$$SOE\\n2461041.500000000 = A.D. 2026-Jan-01 00:00:00.0000 TDB \\n EC= 9.348461380205672E-02 QR= 2.066324058757786E+08 IN= 1.847490422989131E+00\\n OM= 4.948317173608726E+01 W = 2.866231771776422E+02 Tp=  2461125.804267437197\\n N = 6.065179252175027E-06 MA= 3.158219093418334E+02 TA= 3.077038423539357E+02\\n A = 2.279414216480371E+08 AD= 2.492504374202957E+08 PR= 5.935521194545087E+07\\n$$EOE\\n', 'A ='), 2.279414216480371E+08, rel=1e-9)"),
    ('3_PR', "les_verdi(tekst, 'PR=') skal gi omløpstiden til Mars", "naer(les_verdi('$$SOE\\n2461041.500000000 = A.D. 2026-Jan-01 00:00:00.0000 TDB \\n EC= 9.348461380205672E-02 QR= 2.066324058757786E+08 IN= 1.847490422989131E+00\\n OM= 4.948317173608726E+01 W = 2.866231771776422E+02 Tp=  2461125.804267437197\\n N = 6.065179252175027E-06 MA= 3.158219093418334E+02 TA= 3.077038423539357E+02\\n A = 2.279414216480371E+08 AD= 2.492504374202957E+08 PR= 5.935521194545087E+07\\n$$EOE\\n', 'PR='), 5.935521194545087E+07, rel=1e-9)"),
    ('4_jorda', 'solmasse fra jordbanen skal gi ca. 1.989e30 kg', 'naer(solmasse(1.496e11, 3.15581e7), 1.989e30, rel=5e-3)'),
    ('4_formel', 'solmasse skal bruke 4π²a³/(GT²)', 'naer(solmasse(2e11, 5e7), 4 * 3.141592653589793**2 * (2e11)**3 / (6.674e-11 * (5e7)**2))'),
]


@pytest.mark.parametrize(
    "beskrivelse,uttrykk", [s[1:] for s in SJEKKER], ids=[s[0] for s in SJEKKER]
)
def test_sjekk(beskrivelse, uttrykk):
    navnerom = {**vars(oppgave), "naer": naer, "lik": lik, "S": S}
    assert eval(uttrykk, navnerom), beskrivelse
