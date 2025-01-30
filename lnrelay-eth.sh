#!/bin/bash

###############################################
## LN ETHERNET RELAY CONTROL FOR             ##
## DIGITAL-LOGGERS WEB POWER SWITCH PRO      ##
##                                           ##
## ORNL March 2022                           ##
## J.M. Allmond -- allmondjm@ornl.gov        ##
##              -- jmallmond@gmail.com       ##
##                                           ##
## Use: (5 relay boxes, 40 ids)              ##
## ./"$0" id ON                              ##
## ./"$0" id OFF                             ##
## ./"$0" ALL ON                             ##
## ./"$0" ALL OFF                            ##
##                                           ##
## (prevent direct err checking -- faster)   ##           
## ./"$0" id ON NODCHK                       ##
##                                           ##
## (can change id OFFSET ; see below)        ##
## (can make "use" QUITE ; see below)        ##
##                                           ##
## Output (to stdout and file; >0 is err):   ##
## 00000     --> all 5 relay boxes worked    ##
## 01111     --> 1st worked, rest failed     ##
##                                           ##
###############################################
##                                           ##
###############################################
#individual test: for ((i = 1 ; i < 41 ; i++ )); do ./"$0" "$i" ON; done

#older model 6
#fundamental command --> curl --stderr curl.err --connect-timeout 2 admin:lz=724h@192.168.2.103/script?run100=run

#new pro model
#fundamental command --> curl --stderr curl.err --connect-timeout 2 admin:lz=724h@192.168.2.103/outlet?8=ON
#fundamental command --> curl --stderr curl.err --connect-timeout 2 admin:lz=724h@192.168.2.103/outlet?8=OFF
#fundamental command --> curl --stderr curl.err --connect-timeout 2 admin:lz=724h@192.168.2.103/status


#new pro model setup
#default user = admin 
#default pass = 1234
#default ip = 192.168.0.100
#change password, ip address, disable wifi, select "turn all outlets off" on power recovery
#change control and host names, and enable "Allow legacy plaintext login methods" and Allow plaintext URL logins


#####################
# CONFIG & ALIASES  #
#####################
OFFSET=1     #--> valid id input range (0-39), which gets mapped to (1-40)
LNERROR="/tmp/lnrelay.err" # and on stdout as 00000 ; i.e., box1box2box3box4box5, 0=ok and >0=err
QUIET=0      #0 for off or 1 for on


#box x (Old webpower switch 6 method + see end of this file)
# LN1="--stderr lnrelay1.err --connect-timeout 2 admin:lz=724h@192.168.2.101/"
# LNR1="$LN1""script?run"
# options1="lnrelay1.log"
# LNRCK1="$LN1""index.htm"
# err1=0


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

r="=run"

use="Usage (5 relay boxes, ids "$((1-OFFSET))"-"$((40-OFFSET))"):\n
   "$0" "$((1-OFFSET))" ON         \t\t\t#turn socket "$((1-OFFSET))" on\n
   "$0" "$((1-OFFSET))" OFF        \t\t#turn socket "$((1-OFFSET))" off\n
   "$0" ALL ON       \t\t#turn all sockets on\n
   "$0" ALL OFF      \t\t#turn all sockets off\n
   "$0" "$((1-OFFSET))" ON NODCHK  \t\t#no direct err chk (faster)\n          

   \nOutput (stdout and "$LNERROR", >=1 is err):\n
   00000      \t\t #all 5 relay boxes worked    \n
   01111      \t\t #1st worked, rest failed  \n

   \n*can change id OFFSET(="$OFFSET") in code, e.g.,\n
   OFFSET=-31 will change valid id input range to 32-72\n
   \n*can make this 'Use' output QUIET(="$QUIET") in code 1/0\n
   "

################################
# CHECK COMMAND LINE ARGUMENTS #
################################
if [[ -z $1 ]] || [[ -z $2 ]]; then
   echo 11111 ; echo
   echo 11111 > $LNERROR
   if [ "$QUIET" -eq "0" ]; then 
      echo -e $use
   fi
   exit
fi

id=$1
status=$2

if [[ $id != [0-9]* ]] && [ $id != "ALL" ]; then
   echo 11111 ; echo
   echo 11111 > $LNERROR   
   if [ "$QUIET" -eq "0" ]; then 
      echo -e $use
   fi
   exit
fi

if [ $id != "ALL" ]; then
   id=$((id+OFFSET))
   if [ "$id" -lt "1" ] || [ "$id" -gt "40" ]; then
      echo 11111 ; echo
      echo 11111 > $LNERROR      
      if [ "$QUIET" -eq "0" ]; then 
      echo -e $use
      fi
      exit      
   fi
fi

if [ $status != "ON" -a $status != "OFF" ]; then
   echo 11111 ; echo
   echo 11111 > $LNERROR
   if [ "$QUIET" -eq "0" ]; then 
      echo -e $use
   fi
   exit
fi

CHECKRELAY=1 
if [ "$3" = "NODCHK" ]; then
   CHECKRELAY=0
fi


##############
# All ON/OFF #
##############
if [ $id = "ALL" ]; then
 if [ $status = "ON" ]; then   
    #box x (Old webpower switch 6 method + see end of this file)
    #curl $LNR1"100""$r" > $options1
    curl $LNR1"a=ON" > $options1
    curl $LNR2"a=ON" > $options2
    curl $LNR3"a=ON" > $options3
    curl $LNR4"a=ON" > $options4
    curl $LNR5"a=ON" > $options5

    if [ "$CHECKRELAY" -eq "1" ]; then
       sleep 12
       
       #box x (Old webpower switch 6 method + see end of this file)
       ##if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
       ##   err1=$((err1+1))
       ##fi
       if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
          err1=$((err1+1))
       fi
       if [ `curl $LNRCK2 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
         err2=$((err2+1))
       fi
       if [ `curl $LNRCK3 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
         err3=$((err3+1))
       fi
       if [ `curl $LNRCK4 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
         err4=$((err4+1))
       fi
      if [ `curl $LNRCK5 | grep -A 2 "<td>Outlet" | grep "ON" | wc -l` -ne "8" ]; then
         err5=$((err5+1))
       fi
    fi
 fi
 if [ $status = "OFF" ]; then
    #box x (Old webpower switch 6 method + see end of this file)
    #curl $LNR1""103"$r" > $options1
    curl $LNR1"a=OFF" > $options1
    curl $LNR2"a=OFF" > $options2
    curl $LNR3"a=OFF" > $options3
    curl $LNR4"a=OFF" > $options4
    curl $LNR5"a=OFF" > $options5

    if [ "$CHECKRELAY" -eq "1" ]; then
       sleep 1
       #box x (Old webpower switch 6 method + see end of this file)
       #if [ `curl $LNRCK1 | grep -A 1 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
       #   err1=$((err1+1))
       #fi
       if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
          err1=$((err1+1))
       fi
       if [ `curl $LNRCK2 | grep -A 2 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
          err2=$((err2+1))
       fi
       if [ `curl $LNRCK3 | grep -A 2 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
          err3=$((err3+1))
       fi
       if [ `curl $LNRCK4 | grep -A 2 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
          err4=$((err4+1))
       fi
       if [ `curl $LNRCK5 | grep -A 2 "<td>Outlet" | grep "OFF" | wc -l` -ne "8" ]; then
          err5=$((err5+1))
       fi
    fi
 fi 
fi


###########################################
# CONVERT IDS TO SPECIFIC RELAY BOX (5*8) #
###########################################
if [ $id != "ALL" ]; then

#box x (Old webpower switch 6 method + see end of this file)
# #box LNR1
# if [ "$id" -ge "1" -a "$id" -le "8" ]; then
#    outlet=$(($id-0))
#    if [ $status = "ON" ]; then
#       curl $LNR1"0""$outlet"0"$r" > $options1
#       if [ "$CHECKRELAY" -eq "1" ]; then
#          sleep 2.5
#          if [ `curl $LNRCK1 | grep -A 1 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
#             err1=$((err1+1))
#          fi
#       fi     
#    fi

#    if [ $status = "OFF" ]; then
#       curl $LNR1"0""$outlet"3"$r" > $options1
#       if [ "$CHECKRELAY" -eq "1" ]; then
#          sleep .25
#          if [ `curl $LNRCK1 | grep -A 1 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
#             err1=$((err1+1))
#          fi
#       fi
#    fi
# fi

#box LNR1
if [ "$id" -ge "1" -a "$id" -le "8" ]; then
   outlet=$(($id-0))
   if [ $status = "ON" ]; then
      curl $LNR1"$outlet""=ON" > $options1
      if [ "$CHECKRELAY" -eq "1" ]; then  
         sleep 1
         if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
            err1=$((err1+1))
         fi
      fi
   fi

   if [ $status = "OFF" ]; then
      curl $LNR1"$outlet""=OFF" > $options1
      if [ "$CHECKRELAY" -eq "1" ]; then
         sleep .25
         if [ `curl $LNRCK1 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
            err1=$((err1+1))
         fi
      fi
   fi
fi

#box LNR2
if [ "$id" -ge "9" -a "$id" -le "16" ]; then
   outlet=$(($id-8))
   if [ $status = "ON" ]; then
      curl $LNR2"$outlet""=ON" > $options2
      if [ "$CHECKRELAY" -eq "1" ]; then  
         sleep 1
         if [ `curl $LNRCK2 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
            err2=$((err2+1))
         fi
      fi
   fi

   if [ $status = "OFF" ]; then
      curl $LNR2"$outlet""=OFF" > $options2
      if [ "$CHECKRELAY" -eq "1" ]; then
         sleep .25
         if [ `curl $LNRCK2 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
            err2=$((err2+1))
         fi
      fi
   fi
fi

#box LNR3
if [ "$id" -ge "17" -a "$id" -le "24" ]; then
   outlet=$(($id-16))
   if [ $status = "ON" ]; then
      curl $LNR3"$outlet""=ON" > $options3
      if [ "$CHECKRELAY" -eq "1" ]; then  
         sleep 1
         if [ `curl $LNRCK3 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
            err3=$((err3+1))
         fi
      fi
   fi

   if [ $status = "OFF" ]; then
      curl $LNR3"$outlet""=OFF" > $options3
      if [ "$CHECKRELAY" -eq "1" ]; then
         sleep .25
         if [ `curl $LNRCK3 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
            err3=$((err3+1))
         fi
      fi
   fi
fi

#box LNR4
if [ "$id" -ge "25" -a "$id" -le "32" ]; then
   outlet=$(($id-24))
   if [ $status = "ON" ]; then
      curl $LNR4"$outlet""=ON" > $options4
      if [ "$CHECKRELAY" -eq "1" ]; then  
         sleep 1
         if [ `curl $LNRCK4 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
            err4=$((err4+1))
         fi
      fi
   fi

   if [ $status = "OFF" ]; then
      curl $LNR4"$outlet""=OFF" > $options4
      if [ "$CHECKRELAY" -eq "1" ]; then
         sleep .25
         if [ `curl $LNRCK4 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
            err4=$((err4+1))
         fi
      fi
   fi
fi

#box LNR5
if [ "$id" -ge "33" -a "$id" -le "40" ]; then
   outlet=$(($id-32))
   if [ $status = "ON" ]; then
      curl $LNR5"$outlet""=ON" > $options5
      if [ "$CHECKRELAY" -eq "1" ]; then  
         sleep 1
         if [ `curl $LNRCK5 | grep -A 2 "<td>Outlet "$outlet"" | grep "ON" | wc -l` -ne "1" ]; then
            err5=$((err5+1))
         fi
      fi
   fi

   if [ $status = "OFF" ]; then
      curl $LNR5"$outlet""=OFF" > $options5
      if [ "$CHECKRELAY" -eq "1" ]; then
         sleep .25
         if [ `curl $LNRCK5 | grep -A 2 "<td>Outlet "$outlet"" | grep "OFF" | wc -l` -ne "1" ]; then
            err5=$((err5+1))
         fi
      fi
   fi
fi

fi #end of individual ids

##########################################
# CHECK FOR ADDITIONAL ERRORS / TIMEOUTS #
##########################################
err1=$((err1 + `grep -si "connect" lnrelay1.err | wc -l` + `grep -si "forbidden" lnrelay1.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay1.log | wc -l`))
err2=$((err2 + `grep -si "connect" lnrelay2.err | wc -l` + `grep -si "forbidden" lnrelay2.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay2.log | wc -l`))
err3=$((err3 + `grep -si "connect" lnrelay3.err | wc -l` + `grep -si "forbidden" lnrelay3.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay3.log | wc -l`))
err4=$((err4 + `grep -si "connect" lnrelay4.err | wc -l` + `grep -si "forbidden" lnrelay4.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay4.log | wc -l`))
err5=0 #$((err5 + `grep -si "connect" lnrelay5.err | wc -l` + `grep -si "forbidden" lnrelay5.log | wc -l` + `grep -si "<!-- 404 Not Found" lnrelay5.log | wc -l`))

echo $err1$err2$err3$err4$err5
echo $err1$err2$err3$err4$err5 > $LNERROR


###########
# CLEANUP #
###########
rm -f lnrelay1.err lnrelay2.err lnrelay3.err lnrelay4.err lnrelay5.err lnrelay1.log lnrelay2.log lnrelay3.log lnrelay4.log lnrelay5.log






###############################################
#NOTES ON WEB POWER SWITCH BOXES (old ver 6)  #
###############################################
#fundamental command --> curl user:pass@ip/script?run100=run #this starts a new thread on power switch box (63 simultaneous max)
#where 100 is the execution line number on ethernet-controlled power switch, programmed in BASIC. 
#After the box is turned on, it executes line 1 as thread 1. Each call by curl (see above) starts a new thread so you must 
#point it to an execution line number that leads to an "end".
#Each Box was programmed with the following (not exact code, just symbolic):
#(1)\v \1 print %i
#(2)\v \2 print %O
#(3)goto 1
#(4)end
#(5)end
#(6)end
#(7)end
#(8)end
#(9)end
#(10)on 1
#(11)end
#(12)end
#(13)off 1
#(14)end
#...and.so.on.....where 20/23 are outlet 2 on/off, 30/33 are outlet 3 on/off, ... to 80/83.
#(99)end
#(100)on 12345678
#(101)end
#(102)end
#(103)off 12345678
#(104)end 
###################################
