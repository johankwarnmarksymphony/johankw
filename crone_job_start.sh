echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "args: $*"

/usr/local/bin/python3 bellman_jira.py $* >> a.txt

echo "END $(date)" >> a.txt