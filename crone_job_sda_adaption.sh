echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 sda_adaption.py $* >> a.txt

echo "END $(date)" >> a.txt