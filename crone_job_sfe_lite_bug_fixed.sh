echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 sfe_lite_bug_fixed.py $* >> a.txt

echo "END $(date)" >> a.txt