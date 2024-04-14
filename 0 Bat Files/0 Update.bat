CHCP 65001
@echo off
setlocal


echo set the local repo path
set REPO_PATH=../

echo cd to the local repo path
cd /d %REPO_PATH%

echo setting the PortableGit path
set GIT_PATH=PortableGit/bin

echo git pull
"%GIT_PATH%\git.exe" stash
"%GIT_PATH%\git.exe" pull https://github.com/X-T-E-R/GPT-SoVITS-Inference.git stable

echo.
pause
