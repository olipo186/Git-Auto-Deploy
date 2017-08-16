SERVICE_NAME=GitAutoDeploy
PID_PATH_NAME=tmp/.gitautodeploy.pid
LOG_PATH_NAME=tmp/gitautodeploy.log
DATE=`date +%Y%m%d_%H%M%S`
case $1 in
    start)
        echo "Starting $SERVICE_NAME ..."
        if [ ! -f $PID_PATH_NAME ]; then
            python -m gitautodeploy --allow-root-user --daemon-mode --config config.json
            echo "$SERVICE_NAME started ..."
        else
            echo "$SERVICE_NAME is already running ..."
        fi
    ;;
    stop)
        if [ -f $PID_PATH_NAME ]; then
            PID=$(cat $PID_PATH_NAME);
            echo "$SERVICE_NAME stoping ..."
            kill $PID;
            echo "$SERVICE_NAME stopped ..."
            cp $LOG_PATH_NAME $LOG_PATH_NAME"_"$DATE
            rm $PID_PATH_NAME
            rm $LOG_PATH_NAME
        else
            echo "$SERVICE_NAME is not running ..."
        fi
    ;;
    restart)
        if [ -f $PID_PATH_NAME ]; then
            PID=$(cat $PID_PATH_NAME);
            echo "$SERVICE_NAME stopping ...";
            kill $PID;
            echo "$SERVICE_NAME stopped ...";
            cp $LOG_PATH_NAME $LOG_PATH_NAME"_"$DATE
            rm $PID_PATH_NAME
            rm $LOG_PATH_NAME
            echo "$SERVICE_NAME starting ..."
            python -m gitautodeploy --allow-root-user --daemon-mode --config config.json
            echo "$SERVICE_NAME started ..."
        else
            echo "$SERVICE_NAME is not running ..."
        fi
    ;;
esac 
