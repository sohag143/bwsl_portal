@echo off
git add .
set /p msg="Enter Commit Message: "
git commit -m "%msg%"
git push origin main
echo.
echo ================================
echo DONE! Your code is now on GitHub.
echo ================================
pause