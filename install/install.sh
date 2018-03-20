#!/bin/sh


InstallDir="/usr/local/clearcrane/kekong/bin"


echo "install into $InstallDir..."

mkdir -p $InstallDir
mkdir -p /var/log/clearkekong

cp clearkekong /etc/init.d/clearkekong
cp -a ../src $InstallDir/
cp clearkekong_daemon $InstallDir/
cp uninstall.sh $InstallDir/
cp -f logrotate_kekong /etc/logrotate.d/logrotate_kekong

ln -s /etc/init.d/clearkekong /etc/rc2.d/S50clearkekong
ln -s /etc/init.d/clearkekong /etc/rc3.d/S50clearkekong
ln -s /etc/init.d/clearkekong /etc/rc4.d/S50clearkekong
ln -s /etc/init.d/clearkekong /etc/rc5.d/S50clearkekong

/etc/init.d/clearkekong start




