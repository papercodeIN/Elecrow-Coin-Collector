@echo off
cd /d "C:\Users\Parrot\Desktop\Elecrow"
"C:\Python313\python.exe" elecrow_checkin.py --scheduled >> checkin_log.txt 2>&1
echo ---------------------------------------- >> checkin_log.txt
echo Run completed at %date% %time% >> checkin_log.txt
echo ======================================== >> checkin_log.txt
