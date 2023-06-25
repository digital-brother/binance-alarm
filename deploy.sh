git push origin master

# Construct SSH commands invoked by release user
SSH_COMMANDS=$(cat << EOF
echo '===== stopping processes';
sudo systemctl stop gunicorn gunicorn.socket telegram_bot threshold_break_monitor;
echo;
echo '==== updating git master branch';
cd /home/ubuntu/binance_alarm;
git checkout master;
git pull origin master;
/home/ubuntu/.pyenv/versions/binance_alarm/bin/python manage.py migrate;
echo;
echo '===== restarting processes';
sudo systemctl start gunicorn gunicorn.socket telegram_bot threshold_break_monitor;
echo;
echo '===== DONE';
EOF
)

ssh -t ubuntu@binance-alarm $SSH_COMMANDS
