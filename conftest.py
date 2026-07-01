import pathlib
import sys

_LIQUIDITY_AUDIT_ROOT = pathlib.Path(__file__).resolve().parent
if str(_LIQUIDITY_AUDIT_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIQUIDITY_AUDIT_ROOT))
