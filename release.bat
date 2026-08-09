@echo off
setlocal enabledelayedexpansion
set PYTHONUTF8=1
title plagTalk - GitHub Release
cd /d "%~dp0"

echo.
echo  ============================================
echo   plagTalk ^| GitHub Release Script
echo  ============================================
echo.

:: ── Prerequisites ─────────────────────────────────────────────────────────────
git --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: git not found.
    echo  Install from https://git-scm.com then re-run.
    pause & exit /b 1
)

gh --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: gh CLI not found.
    echo  Install from https://cli.github.com then re-run.
    pause & exit /b 1
)

gh auth status >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Not logged into GitHub.
    echo  Run this once in any terminal:  gh auth login
    pause & exit /b 1
)

:: ── Force the plagrizd account for THIS repo ──────────────────────────────────
:: This machine may have multiple GitHub accounts. Pull plagrizd's token into
:: GH_TOKEN for this process only — setlocal keeps it scoped to this script.
set "GH_TOKEN="
for /f "delims=" %%t in ('gh auth token --user plagrizd 2^>nul') do set "GH_TOKEN=%%t"
if not defined GH_TOKEN (
    echo  ERROR: Could not get a token for the 'plagrizd' account.
    echo  Sign that account in once:
    echo      gh auth login   ^(choose GitHub.com, log in as plagrizd^)
    pause & exit /b 1
)
echo  Account : plagrizd ^(forced for this repo^)

:: ── Find the newest plagTalk-*.exe produced by build.bat ─────────────────────
set SRCNAME=
for /f "delims=" %%f in ('dir /b /o-d "dist\plagTalk-*.exe" 2^>nul') do (
    if "!SRCNAME!"=="" set SRCNAME=%%f
)
if "!SRCNAME!"=="" (
    echo  ERROR: No plagTalk-*.exe found in dist\.
    echo  Run build.bat first, then re-run release.bat.
    pause & exit /b 1
)

:: Derive version from filename  e.g.  plagTalk-0.1.0.exe -> 0.1.0
set VERSION=!SRCNAME:plagTalk-=!
set VERSION=!VERSION:.exe=!

:: Stable upload name — keeps Windows Firewall allow-rule across versions
set EXENAME=plagTalk.exe
set EXE=dist\plagTalk.exe
copy /y "dist\!SRCNAME!" "%EXE%" >nul

:: ── Read tag / title / notes from version.json ────────────────────────────────
python -c ^
    "import json,sys; cl=json.load(open('version.json',encoding='utf-8'))['changelog']; v='%VERSION%'; e=next((x for x in cl if x.get('version')==v),cl[0]); sys.stdout.write(e.get('github_tag','v'+v))" > _v.tmp
set /p TAG=<_v.tmp
del _v.tmp

python -c ^
    "import json,sys; cl=json.load(open('version.json',encoding='utf-8'))['changelog']; v='%VERSION%'; e=next((x for x in cl if x.get('version')==v),cl[0]); sys.stdout.write(e.get('github_title','plagTalk v'+v))" > _v.tmp
set /p RELTITLE=<_v.tmp
del _v.tmp

python -c ^
    "import json; cl=json.load(open('version.json',encoding='utf-8'))['changelog']; v='%VERSION%'; e=next((x for x in cl if x.get('version')==v),cl[0]); open('_notes.tmp','w',encoding='utf-8').write('\n'.join('- '+n for n in e.get('notes',[])))"

echo  Version : !VERSION!
echo  Tag     : %TAG%
echo  Title   : "%RELTITLE%"
echo  Exe     : %EXE%
echo.

:: ── Pull git identity from gh (no global git config needed) ───────────────────
for /f "delims=" %%u in ('gh api user --jq .login') do set GH_USER=%%u
for /f "delims=" %%e in ('gh api user --jq .email') do set GH_EMAIL=%%e
if "%GH_EMAIL%"=="null" set GH_EMAIL=%GH_USER%@users.noreply.github.com
if "%GH_EMAIL%"==""     set GH_EMAIL=%GH_USER%@users.noreply.github.com

:: ── Git — init once if needed, then commit + push ────────────────────────────
if not exist ".git" (
    echo  First run — initialising git repository...
    git init
    git checkout -b main 2>nul
    if errorlevel 1 git branch -m main
    git remote add origin https://github.com/plagrizd/plagTalk.git
    echo  Fetching existing GitHub history...
    git fetch origin main
    git reset --soft origin/main 2>nul
    echo  Done.
    echo.
)

git config user.name  "%GH_USER%"
git config user.email "%GH_EMAIL%"
git config core.autocrlf false

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin https://github.com/plagrizd/plagTalk.git
)

:: Stamp the download URL into version.json before committing
python -c "import json; d=json.load(open('version.json',encoding='utf-8')); d['changelog'][0]['asset_url']='https://github.com/plagrizd/plagTalk/releases/download/%TAG%/%EXENAME%'; open('version.json','w',encoding='utf-8').write(json.dumps(d,indent=2,ensure_ascii=False)+'\n')"

echo  Staging source files...
git add app.py updater.py updates_page.py settings.py tts_engine.py event_handler.py ws_client.py version.json build.bat release.bat

:: Only commit when there are staged changes
git diff --cached --quiet
if errorlevel 1 (
    echo  Committing...
    git commit -m "Release %TAG%"
) else (
    echo  No file changes since last release — skipping commit.
)

echo  Pushing to GitHub...
git push -u origin main
if errorlevel 1 (
    echo.
    echo  ERROR: Push failed.
    echo  Make sure the repo exists at https://github.com/plagrizd/plagTalk
    echo  and that your plagrizd account has write access.
    del _notes.tmp 2>nul
    pause & exit /b 1
)

:: ── Create GitHub Release and attach exe ─────────────────────────────────────
echo.
gh release view "%TAG%" --repo plagrizd/plagTalk >nul 2>&1
if not errorlevel 1 (
    echo  Release %TAG% already exists on GitHub.
    set /p OVERWRITE= "  Overwrite it? (y/n): "
    if /i "!OVERWRITE!"=="y" (
        echo  Deleting existing release and tag...
        gh release delete "%TAG%" --repo plagrizd/plagTalk --yes >nul 2>&1
        git tag -d "%TAG%" >nul 2>&1
        git push origin --delete "%TAG%" >nul 2>&1
    ) else (
        echo  Skipped — existing release left as-is.
        del _notes.tmp 2>nul
        echo.
        echo  ============================================
        echo   Files pushed. Release already published:
        echo   https://github.com/plagrizd/plagTalk/releases/tag/%TAG%
        echo  ============================================
        echo.
        pause & exit /b 0
    )
)

echo  Creating GitHub Release %TAG%...
gh release create "%TAG%" "%EXE%" ^
    --repo plagrizd/plagTalk ^
    --title "%RELTITLE%" ^
    --notes-file _notes.tmp

if errorlevel 1 (
    echo.
    echo  ERROR: Release creation failed. Check output above.
    del _notes.tmp 2>nul
    pause & exit /b 1
)

del _notes.tmp 2>nul

echo.
echo  ============================================
echo   Done! Release published:
echo   https://github.com/plagrizd/plagTalk/releases/tag/%TAG%
echo  ============================================
echo.
pause
endlocal
