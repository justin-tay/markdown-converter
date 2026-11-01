"""A stand-in for LibreOffice's soffice: writes the text in $FAKE_SOFFICE_TEXT as
`<outdir>/<stem>.txt`, encoded cp1252 as older Windows builds do."""

import os
import sys
from pathlib import Path

arguments = sys.argv[1:]
outdir = Path(arguments[arguments.index("--outdir") + 1])
source = Path(arguments[-1])
text = Path(os.environ["FAKE_SOFFICE_TEXT"]).read_text(encoding="utf-8")
(outdir / f"{source.stem}.txt").write_bytes(text.encode("cp1252"))
