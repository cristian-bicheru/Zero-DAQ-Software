./fix_perms.sh
cd Controller
taskset -c 3 python3.11 main.py "$@" --dest ${SSH_CLIENT%% *} &
sudo renice -n -20 -p $!
sudo cpufreq-set -r --governor performance
wait
