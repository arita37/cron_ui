#!/bin/bash

LINE_SEP="##############################################################################"
LINE_SEP2="######################################################"
LINE_SEP3="###########################"

LINE_END="\n\n\n#######################################################################"


function echo2 () {   
  if [[  $2 == ''  ]]; then
    echo -e $1  2>&1 | tee -a "${LOGFILE}"

  else :  ### Not append
    echo -e $1  2>&1 | tee   "${LOGFILE}"
  fi;

}


function echo3 () {   
  echo -e  $LINE_END  2>&1 | tee -a "${LOGFILE}"
  if [[  $2 == ''  ]]; then
    echo -e $1  2>&1 | tee -a "${LOGFILE}"

  else :  ### Not append
    echo -e $1  2>&1 | tee   "${LOGFILE}"
  fi;

}



function list_error() {
   ### Find Error msg in log file
   ## list_error ztmp/log//_log1.py    
   echo -e  "\n\n$LINE_END"  
   echo -e  "###### List of err-ors: ############" 
   echo -e  $1
   grep -Ehnr "error|Error" "$1"  | grep -ve "from_error"
   #grep -Ehnr "error|Error" "$1"  

}


function list_warning() {
   ### Find Error msg in log file
   ## list_error ztmp/log//_log1.py    
   echo -e  "\n\n$LINE_END"  
   echo -e  "###### List of warni-nings: ############" 
   echo -e  $1
   grep -Ehnr "warning|Warning" "$1"  | grep -ve "from_error"
   #grep -Ehnr "error|Error" "$1"  

}



function path_abs() {
  # $1 : relative filename
  if [ -d "$(dirname "$1")" ]; then
    echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  fi
}


function git_push_bot() {
    git config user.name github-actions[bot]
    git config user.email 41898282+github-actions[bot]@users.noreply.github.com
    git add --all &&  git commit -m "${1}" 
    git pull --all     
    git push --all -f  
}



function timeout2() {
    # First argument: PID
    # Second argument: Timeout
    # Get process start time (Field 22) to check for PID recycling
    start_time="$(cut -d ' ' -f 22 /proc/$1/stat)"

    sleep "$2"

    # Make sure that the PID was not reused by another process
    # that started at a later time
    if [ "$(cut -d ' ' -f 22 /proc/$1/stat)" = "$start_time" ]; then
        # Kill process with SIGTERM
        kill -9 "$1"
    fi
}


function kill_sub_process() {
    local pid="$1"
    local and_self="${2:-false}"
    if children="$(pgrep -P "$pid")"; then
        for child in $children; do
            kill_sub_process "$child" true
        done
    fi
    if [[ "$and_self" == true ]]; then
        kill -9 "$pid"
    fi
}


eexport() {
    ### Export variable to disk for later reload
    # my_var="Hello, World!"
    # export_var my_var  file.sh
    # source file.sh
    eval "echo export $1=$2 " > $3
    #source $2
}


export_allenv() {
  # Export all environment variables to a file in a format that can be sourced
  # export_allenv "env2.txt"
  while IFS='=' read -r name value; do

      if [[ $string1 == *"image_tag"* ]]; then
         printf 'export %s="%q"\n' "$name" "${value}"
      else
        echo ""
      fi

      printf 'export %s="%q"\n' "$name" "${value}"
  done < <(printenv) > $1
}



function print_envars(){ 
  python -c "import os, pprint; pprint.pprint(dict(os.environ))"  
}




####################### Cache  #############################################################
function cacheon() {

  export CACHE_ENABLE="1"
  export CACHE_DIR="ztmp/zcache/"
  export CACHE_TTL="600"
  export CACHE_SIZE="1000000000"
  export CACHE_DEBUG="0"

  echo  "####CACHE_ENABLE $CACHE_ENABLE"
  echo  "####CACHE_TTL $CACHE_TTL"
}



function cacheoff() {

  export CACHE_ENABLE= ""
}




####################### String #############################################################
function str_exists_infile {
    ### exist_str "error"  myfile.py 
    if grep -iq "$1" $2; then
        echo "$1 exists !"
        return 1
    else
        echo "$1 not exists !"
        return 0
    fi
}






###########################################################################################
####################### Dates #############################################################
function date_add() {
      #    date_add  "+1 day"
      #    date_add  "+1 hour"
      #    date_add  "+1 hour" "%Y%m%d"
      #    date_add  "+0 hour" unix
      #    date_add  "+1 hour" unix  
      local addtime="$1"  && [ -z "$1" ] &&  addtime="+1 hour"  
      local fmt="$2"      && [ -z "$2" ] &&  fmt="%Y-%m-%d %H:%M:%S"  
      local tzone="$2"    && [ -z "$3" ] &&  tzone="Asia/Tokyo"  

      if [[ "$fmt" == *"unix"* ]]; then 
          echo $(date -d "$addtime" +%s)
          return 
      fi 

      if [[ "$OSTYPE" == "darwin"* ]]; then
              dt="$(TZ=$tzone date -v+"${addtime}" +"$fmt")"  

      else
              dt="$(TZ=$tzone date -d "${addtime}" +"${fmt}")"     
      fi

      echo $dt
}



function date_now() {
      #    date_now   
      #    date_now   "%Y%m%d"
      #    date_now   unix  
      local fmt="$1"      && [ -z "$1" ] &&  fmt="%Y-%m-%d %H:%M:%S"  
      local tzone="$2"    && [ -z "$2" ] &&  tzone="Asia/Tokyo"  

      if [[ "$fmt" == *"unix"* ]]; then 
             echo $(date  +%s)
             return 
      fi 

      if [[ "$OSTYPE" == "darwin"* ]]; then
              dt="$(TZ=$tzone date  +"$fmt")"  

      else
              dt="$(TZ=$tzone date  +"${fmt}")"     
      fi

      echo $dt

}





function date_get_next_hour_ts() {
    local minute=$1  && [ -z $1 ] &&  minute="00"  

    if [[ "$OSTYPE" == "darwin"* ]]; then 
        #local date1=$(date -v+1H       '+%Y-%m-%d %H')

        local date1=$(date -v+1H '+%Y-%m-%d %H')
        local date_and_next_hour="$date1:$minute:00"
        local unix_timestamp=$(date -j -f "%Y-%m-%d %H:%M:%S" "$date_and_next_hour" +%s)


    else 
        # local date1=$(date -d '+1 hour' '+%Y-%m-%d %H')

        local date1=$(date -d '+1 hour' '+%Y-%m-%d %H')
        local date_and_next_hour="$date1:$minute:00"
        local unix_timestamp=$(date -d "$date_and_next_hour" +%s)


    fi 

    # Concatenate the date and the next hour with 00 minutes and seconds
    #local date_and_next_hour="$date1:$minute:00"

    #local unix_timestamp=$(date -d "$date_and_next_hour" +%s)

    echo $unix_timestamp
}





function date_get_next_day_ts() {
    # dd=$(date_get_next_day_ts  09 15 ) && date_unix_todate $dd 

    local hour=$1    && [ -z $1 ] &&  hour="09"  
    local minute=$2  && [ -z $2 ] &&  minute="00"  
    local tzone=$3   && [ -z $3 ] &&  tzone="Asia/Tokyo"  


    if [[ "$OSTYPE" == "darwin"* ]]; then 
          local date1=$(TZ=$tzone date -v+1d       '+%Y-%m-%d ')

          local date_and_next_hour="$date1 $hour:$minute:00"

          local unix_timestamp=$(TZ=$tzone date -j -f "%Y-%m-%d %H:%M:%S" "$date_and_next_hour" +%s)


    else 
          local date1=$(TZ=$tzone date -d '+1 day' '+%Y-%m-%d ')

          # Concatenate the date and the next hour with 00 minutes and seconds
          local date_and_next_hour="$date1 $hour:$minute:00"

          local unix_timestamp=$(TZ=$tzone date -d "$date_and_next_hour" +%s)

    fi 

    echo $unix_timestamp
}




function date_unix_todate() {
  local ts=$1 # The timestamp to convert

  if [[ "$OSTYPE" == "darwin"* ]]; then 

     TZ="Asia/Tokyo" date -r $ts '+%Y%m%d %H:%M:%S'

  else 

     TZ="Asia/Tokyo" date -d "@$ts" '+%Y%m%d %H:%M:%S' 

  fi


}










####################################################################################
function cpu_get_num_cores() {
  # Check if the system is macOS or Linux
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS: Use the sysctl command to get the number of CPU cores
    num_cores=$(sysctl -n hw.ncpu)
  else
    # Linux: Use the nproc command to get the number of CPU cores
    num_cores=$(nproc)
  fi

  # Return the result
  echo "$num_cores"
}


function cpu_get_avg_usage() {
    # Get the total CPU usage from the ps command
    cpu_total_usage=$(ps -A -o %cpu | awk '{s+=$1} END {print s}')
    num_cores=$(cpu_get_num_cores)
    cpu_total_usage=$(echo  "scale=4; $cpu_total_usage / $num_cores"  | bc -l )

    echo "Total CPU usage per core: $cpu_total_usage%"
}


function cpu_get_avg_usage2() {
    period=$1 && [ -z $1 ] && period=600      ###  print folder size
    local avg_cpu_usage=$(sar -u 1 $period | grep "Average" | awk '{print 100-$8}')
    echo "Average CPU usage over $period : $avg_cpu_usage%"
}


function ram_get_usage() {

  if [[ "$OSTYPE" == "darwin"* ]]; then
    pages_free=$(vm_stat | grep 'Pages free:' | awk '{print $3}' | tr -d '.')
    pages_active=$(vm_stat | grep 'Pages active:' | awk '{print $3}' | tr -d '.')
    pages_inactive=$(vm_stat | grep 'Pages inactive:' | awk '{print $3}' | tr -d '.')
    pages_speculative=$(vm_stat | grep 'Pages speculative:' | awk '{print $3}' | tr -d '.')
    pages_wired_down=$(vm_stat | grep 'Pages wired down:' | awk '{print $4}' | tr -d '.')
    pages_purgeable=$(vm_stat | grep 'Pages purgeable:' | awk '{print $3}' | tr -d '.')

    # total_used=$((pages_active + pages_inactive + pages_speculative + pages_wired_down))
    total_used=$((pages_active ))
    total_free=$((pages_free + pages_purgeable))
    total_memory=$((total_used + total_free))

    ram_total_usage=$(echo "scale=2; $total_used / $total_memory * 100" | bc)

  else

    ram_total_usage=$(free | grep Mem | awk '{print $3/$2 * 100.0}')

  fi  
  
  echo "Ram usage: $ram_total_usage"

}


function docker_dockerid() {
   ### Find dockerid through mount   
   cat /proc/self/mountinfo | grep docker/overlay2 | sed -n 's/.*upperdir=\(.*\)\/diff.*/\1/p' | sed -n 's/.*-\(.*\)/\1/p'
}



function monitor_purge_tempfs() {

     
     while true; do
          echo "####Monitor purge_tempfs "

          echo $(du -sh /tmp)

          find /tmp -type f -atime +0.1 -delete
          find /tmp -type d -empty -delete
          echo "#### Deleted files and empty directories in /tmp not accessed in over 3 hours"

          echo $(du -sh /tmp)
          sleep $1      

    done 

}


function clean_tempfs() {

      echo "####M Clean_tempfs tmp/ "

      echo $(du -sh /tmp)

      find /tmp -mindepth 1 -delete

      # find /tmp -type f -atime +0.1 -delete ### unaccessed for over 3 hours
      # find /tmp -type d -empty -delete
      echo "#### Deleted files and empty directories in /tmp not accessed in over 3 hours"

      echo $(du -sh /tmp)

}




function monitor_python() {

     # List Python processes
     # echo $(ps aux | grep '[p]ython' | awk '{print $2, $11}')

     while true; do
        echo "####Monitor python "
        echo $(pgrep -af python)
        sleep 240

    done 

}



function monitor_topc() {

    while true; do

        echo "####Monitor topc "
        text=$(top -b -n 1 | head -n 12 | tail -n 20)
        echo $text
        sleep 180
   done 

}

function monitor_cpu_ram() {

    echo "####### Background Print of RAM/CPU usage "  
    local pid1=$$
    while true; do
        echo "### Monitor RAM/CPU, $(date '+%Y-%m-%d %H:%M:%S'), $pid1,  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')% RAM: $(free -m | awk '/Mem:/ {print $3 "/" $2 "MB"}'))"
        sleep 60
    done
}




##########################################################################
function sqlite_repair() {
        local DATABASE_LOCATION="$1" 
        local DB_NAME="$2"
        cd $DATABASE_LOCATION
        echo '.dump'|sqlite3 $DB_NAME|sqlite3 repaired_$DB_NAME
        mv $DB_NAME corrupt_$DB_NAME
        mv repaired_$DB_NAME $DB_NAME

}





###########################################################################################
###########################################################################################
function str_replace_jumpline() {
      local x="$1"
      x_no_newlines=$(echo "$x" | tr '\n' ' ')
      echo "$x_no_newlines"
}


function wait_until_python_finish() {


      local tsleep="$1"  && [ -z $1 ] &&  local tsleep="60"
      python -c "import time; time.sleep(22)" &    ###check

      while true; do
      
            local flag="$(pgrep -x 'python')"    
            echo "proc: $flag"
            if  [ -z "$flag" ];  then
                  echo "No Python processes found. Exiting."
                  break
            fi

            echo "Waiting for Python processes to finish..."
            echo $flag
            sleep $tsleep
      done

}







############################################################
echo "bin/utils.sh loaded"



