# Publicar en GitHub (solo git)

Guía para subir el repo **sin compilar, sin GUI y sin ejecutar el nodo**. Útil cuando la máquina ya tiene otro nodo minando (ej. AsusArch).

## Prerrequisitos

1. Repo con historial git en `~/oracle-knots` (la carpeta `.git` debe existir).
2. SSH a GitHub funcionando:
   ```bash
   ssh -T git@github.com
   # Debe responder: Hi MarcanoFilms!
   ```
3. Repositorio vacío en GitHub (sin README inicial):
   https://github.com/MarcanoFilms/oracle-knots

## Problema común: `depends/` aparece borrado

Si el repo llegó por tarball **sin** la carpeta `depends/`, git muestra miles de archivos como eliminados. Restáuralos antes del push:

```bash
cd ~/oracle-knots
git restore depends/
```

## Pasos manuales

```bash
cd ~/oracle-knots

# Remote obsoleto (opcional)
git remote remove dathonohm 2>/dev/null || true

# Verificar remotes
git remote -v
# origin   → git@github.com:MarcanoFilms/oracle-knots.git
# upstream → https://github.com/bitcoinknots/bitcoin.git

# Asegurar URL SSH en origin
git remote set-url origin git@github.com:MarcanoFilms/oracle-knots.git

# Arreglar working tree si hace falta
git restore depends/

# Revisar estado (debe estar limpio o solo con cambios intencionales)
git status

# Subir
git push -u origin main
```

## Script automático (sin prompts)

```bash
cd ~/oracle-knots
./scripts/push-to-github.sh
```

## Instrucciones para Claude / asistente IA

**Objetivo:** `git push -u origin main` desde AsusArch. **No** ejecutar `setup-gui.sh`, `build.sh`, `launch.sh`, `bitcoind` ni instalar dependencias de compilación.

| Dato | Valor |
|------|-------|
| Máquina | AsusArch (`192.168.1.168`) |
| Directorio | `~/oracle-knots` |
| Branch | `main` |
| Remote origin | `git@github.com:MarcanoFilms/oracle-knots.git` |
| GitHub SSH | Ya configurado en esa máquina |

**Secuencia:**

1. `cd ~/oracle-knots`
2. `git restore depends/` si `git status` muestra borrados en `depends/`
3. `git remote remove dathonohm` si existe
4. `git status` — confirmar árbol limpio
5. `git push -u origin main`

**Si falla el push:** verificar que el repo en GitHub existe y está vacío; verificar `ssh -T git@github.com`.

**Si no hay `.git`:** el tarball no incluyó historial. Volver a transferir desde la PC de desarrollo con `.git` incluido (ver `scripts/transfer-with-git.sh`).