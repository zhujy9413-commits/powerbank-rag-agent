#!/bin/zsh
set -eu
cd "${0:A:h}"
exec python3 -m app.knowledge_assistant.server --open
