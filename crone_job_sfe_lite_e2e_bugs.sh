echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 sfe_lite_e2e_bugs.py $* >> a.txt

echo "END $(date)" >> a.txt