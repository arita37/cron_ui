

### prefix for task 


function date_get_ymdhms() {
  # Get current date by default, or use provided date
  local date_str=${1:-$(date +"%Y-%m-%d")}
  
  # Extract components using date command with BSD syntax
  year1=$(date -jf "%Y-%m-%d" "$date_str" +"%Y")
  month1=$(date -jf "%Y-%m-%d" "$date_str" +"%m")
  day1=$(date -jf "%Y-%m-%d" "$date_str" +"%d")
  hour1=$(date -jf "%Y-%m-%d" "$date_str" +"%H")
  minute1=$(date -jf "%Y-%m-%d" "$date_str" +"%M")
  second1=$(date -jf "%Y-%m-%d" "$date_str" +"%S")

  echo "$year1 $month1 $day1 $hour1 $minute1 $second1"
}


# Call the function and read the values into local variables
read year1 month1 day1 hour1 minute1 second1 <<< "$(date_get_ymdhms)"

dirlog="ztmp/log/year=$year1/month=$month1/day=$day1"
mkdir -p  $dirlog
logfile237="$dirlog/task_${year1}${month1}${day1}_${hour1}${minute1}${second1}.log"

echo " logfile : $logfile237"








