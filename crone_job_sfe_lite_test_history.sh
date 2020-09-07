echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 sfe_lite_test_history.py $* >> a.txt

echo "END $(date)" >> a.txt