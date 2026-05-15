"""Run each page through Streamlit's AppTest to catch runtime errors."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

PAGES = ["app.py"] + sorted(str(p) for p in Path("pages").glob("*.py"))

failed = 0
for page in PAGES:
    try:
        at = AppTest.from_file(page, default_timeout=60)
        at.run()
        if at.exception:
            print(f"FAIL  {page}")
            for e in at.exception:
                print("       ", repr(e))
            failed += 1
        else:
            print(f"OK    {page}")
    except Exception as e:
        print(f"CRASH {page}: {e}")
        failed += 1

print()
print(f"{'PASS' if failed == 0 else 'FAIL'} — {failed} page(s) with errors")
