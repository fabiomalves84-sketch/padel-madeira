#!/bin/bash
# Atualiza a disponibilidade e publica, se houver mudanças.
# Corre sozinho de hora a hora pelo launchd. Não faz nada se nada mudou.

set -u
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
cd /Users/fabioalves/Sites/padel-madeira || exit 1

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

python3 atualizar.py || { echo "atualizar.py falhou"; exit 1; }

if git diff --quiet -- dados.js dados.json; then
  echo "sem alterações, nada a publicar"
  exit 0
fi

git add dados.js dados.json
git commit -q -m "Disponibilidade atualizada automaticamente $(date '+%Y-%m-%d %H:%M')"

if git push -q origin main; then
  echo "publicado"
else
  echo "push falhou (autenticação do gh expirada?)"
  exit 1
fi
