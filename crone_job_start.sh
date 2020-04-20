echo "START $(date)" >> a.txt

echo "pwd : $(pwd)"
echo "arg1: $1"

python3 bellman_jira.py $1 $2 >> a.txt

echo "END $(date)" >> a.txt