Trying to read fan RPM and write pwn on linux ubuntu 25.04
sudo apt install ectools
sudo modprobe ec_sys write_support=1
then run the script 
sudo python3 ec_fan_monitor.py
