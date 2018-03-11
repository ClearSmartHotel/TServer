#!/bin/sh

InstallDir="/usr/local/clearcrane/kekong/bin"
initFileName=clearkekong

/etc/init.d/$initFileName stop
sleep 1

rm -rf $InstallDir
rm -rf $DataDir 

#update-rc.d -f $initFileName remove


rm /etc/rc2.d/S50$initFileName
rm /etc/rc3.d/S50$initFileName
rm /etc/rc4.d/S50$initFileName
rm /etc/rc5.d/S50$initFileName

rm /etc/init.d/$initFileName
