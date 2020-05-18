echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 rtc_test_ci.py $* >> a.txt

echo "END $(date)" >> a.txt