#!/usr/bin/env bash
# Start MarketScope.
# On macOS, XGBoost needs the OpenMP library (libomp). If Homebrew's libomp is
# not installed, reuse the copy that ships inside scikit-learn.
cd "$(dirname "$0")"
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

if [[ "$(uname)" == "Darwin" && ! -f /opt/homebrew/opt/libomp/lib/libomp.dylib && ! -f /usr/local/opt/libomp/lib/libomp.dylib ]]; then
  SK_LIBS="$("$PY" -c 'import os, sklearn; print(os.path.join(os.path.dirname(sklearn.__file__), ".dylibs"))' 2>/dev/null)"
  [ -d "$SK_LIBS" ] && export DYLD_LIBRARY_PATH="$SK_LIBS${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
fi

exec "$PY" -m streamlit run app.py "$@"
