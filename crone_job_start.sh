echo "START $(date)" >> a.txt

python3 bellman_jira.py $1 $2 >> a.txt

echo "END $(date)" >> a.txt