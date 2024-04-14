CHCP 65001
@echo off
setlocal


echo Set the local repo path
set REPO_PATH=../

echo cd to the local repo path
cd /d %REPO_PATH%

echo setting the PortableGit path
set GIT_PATH=PortableGit/bin



echo git reset --hard
"%GIT_PATH%\git.exe" fetch https://github.com/X-T-E-R/GPT-SoVITS-Inference.git stable
"%GIT_PATH%\git.exe" reset --hard FETCH_HEAD

echo.
pause