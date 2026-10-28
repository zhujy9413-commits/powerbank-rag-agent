#!/bin/zsh
set -eu
cd "${0:A:h}"
task_python="$(command -v python3)"
if ! "$task_python" -c 'import pypdf' >/dev/null 2>&1; then
  bundled_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [[ -x "$bundled_python" ]]; then
    task_python="$bundled_python"
  fi
fi
exec "$task_python" -m app.knowledge_assistant.server --open
