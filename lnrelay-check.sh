#!/bin/bash

###############################################
## On/OFF status of id                       ##
## Use: (5 relay boxes, 40 ids)              ##
## ./"$0" id                                 ##
##                                           ##
##                                           ##
###############################################


#####################
# CONFIG & ALIASES  #
#####################
OFFSET=1     #--> valid id input range (0-39), which gets mapped to (1-40)
LNERROR="/tmp/lnrelay.err" # and on stdout as 00000 ; i.e., box1box2box3box4box5, 0=ok and >0=err


#box 1
LN1="--stderr lnrelay1.err --connect-timeout 2 admin:lz=724h@192.168.0.101/"
LNR1="$LN1""outlet?"
options1="lnrelay1.log"
LNRCK1="$LN1""index.htm"
err1=0

#box 2
LN2="--stderr lnrelay2.err --connect-timeout 2 admin:lz=724h@192.168.0.102/"
LNR2="$LN2""outlet?"
options2="lnrelay2.log"
LNRCK2="$LN2""index.htm"
err2=0

#box 3
LN3="--stderr lnrelay3.err --connect-timeout 2 admin:lz=724h@192.168.0.103/"
LNR3="$LN3""outlet?"
options3="lnrelay3.log"
LNRCK3="$LN3""index.htm"
err3=0

#box 4
LN4="--stderr lnrelay4.err --connect-timeout 2 admin:lz=724h@192.168.0.104/"
LNR4="$LN4""outlet?"
options4="lnrelay4.log"
LNRCK4="$LN4""index.htm"
err4=0

#box 5
LN5="--stderr lnrelay5.err --connect-timeout 2 admin:lz=724h@192.168.0.105/"
LNR5="$LN5""outlet?"
options5="lnrelay5.log"
LNRCK5="$LN5""index.htm"
err5=0


if [[ -z $1 ]]; then
   echo 11111 ; echo
   echo 11111 > $LNERROR
   exit
fi

id=$1
id=$((id+OFFSET))

if [ "$id" -lt "1" ] || [ "$id" -gt "40" ]; then
   echo 11111 ; echo
   echo 11111 > $LNERROR      
   exit      
fi



###########################################
# CONVERT IDS TO SPECIFIC RELAY BOX (5*8) #
###########################################


#box LNR1
if [ "$id" -ge "1" -a "$id" -le "8" ]; then
   outlet=$(($id-0))
         if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -eq "1" ]; then
            echo ON
         elif [ `curl $LNRCK1 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -eq "1" ]; then
            echo OFF
         else
            err1=$((err1+1))         
         fi
fi
#box LNR2
if [ "$id" -ge "9" -a "$id" -le "16" ]; then
   outlet=$(($id-8))
         if [ `curl $LNRCK2 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -eq "1" ]; then
            echo ON
         elif [ `curl $LNRCK2 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -eq "1" ]; then
            echo OFF
         else
            err2=$((err2+1))         
         fi
fi
#box LNR3
if [ "$id" -ge "17" -a "$id" -le "24" ]; then
   outlet=$(($id-16))
         if [ `curl $LNRCK3 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -eq "1" ]; then
            echo ON
         elif [ `curl $LNRCK3 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -eq "1" ]; then
            echo OFF
         else
            err3=$((err3+1))         
         fi
fi
#box LNR4
if [ "$id" -ge "25" -a "$id" -le "32" ]; then
   outlet=$(($id-24))
         if [ `curl $LNRCK4 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -eq "1" ]; then
            echo ON
         elif [ `curl $LNRCK4 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -eq "1" ]; then
            echo OFF
         else
            err4=$((err4+1))         
         fi
fi
#box LNR5
if [ "$id" -ge "33" -a "$id" -le "40" ]; then
   outlet=$(($id-32))
         if [ `curl $LNRCK5 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -eq "1" ]; then
            echo ON
         elif [ `curl $LNRCK5 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -eq "1" ]; then
            echo OFF
         else
            err5=$((err5+1))         
         fi
fi


##########################################
# CHECK FOR ADDITIONAL ERRORS / TIMEOUTS #
##########################################
err1=$((err1 + `grep -si "connect" lnrelay1.err | wc -l` + `grep -si "forbidden" lnrelay1.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay1.log | wc -l`))
err2=$((err2 + `grep -si "connect" lnrelay2.err | wc -l` + `grep -si "forbidden" lnrelay2.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay2.log | wc -l`))
err3=$((err3 + `grep -si "connect" lnrelay3.err | wc -l` + `grep -si "forbidden" lnrelay3.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay3.log | wc -l`))
err4=$((err4 + `grep -si "connect" lnrelay4.err | wc -l` + `grep -si "forbidden" lnrelay4.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay4.log | wc -l`))
err5=$((err5 + `grep -si "connect" lnrelay5.err | wc -l` + `grep -si "forbidden" lnrelay5.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay5.log | wc -l`))

echo $err1$err2$err3$err4$err5
echo $err1$err2$err3$err4$err5 > $LNERROR


###########
# CLEANUP #
###########
rm -f lnrelay1.err lnrelay2.err lnrelay3.err lnrelay4.err lnrelay5.err lnrelay1.log lnrelay2.log lnrelay3.log lnrelay4.log lnrelay5.log

