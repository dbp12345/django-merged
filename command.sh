#!/bin/bash


echo "Commands:"
options=(
"repeatSyncParametersLogsCommand"
"updateLastModifiedContactsPrivserCommand"
"updateRecordsFromFireRunCommand"
"preheatThumbnailsCommand"
"runUpdateFromExchangeCommand --ignore_diff_properties --update_all"
"checkPossibilityFirecrewCommand"
"runUpdateFromPrivserCommand --ignore_diff_properties"
"--run-syncdb"
"Exit"
)
select opt in "${options[@]}"
do
    case $opt in
        "repeatSyncParametersLogsCommand")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py repeatSyncParametersLogsCommand
            break
            ;;
        "updateLastModifiedContactsPrivserCommand")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py updateLastModifiedContactsPrivserCommand
            break
            ;;
        "updateRecordsFromFireRunCommand")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py updateRecordsFromFireRunCommand
            break
            ;;
        "preheatThumbnailsCommand")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py thumbnail clear_delete_referenced && python manage.py thumbnail clear_delete_all && python manage.py preheatThumbnailsCommand
            break
            ;;
        "runUpdateFromExchangeCommand --ignore_diff_properties --update_all")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py runUpdateFromExchangeCommand --ignore_diff_properties --update_all
            break
            ;;
        "checkPossibilityFirecrewCommand")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py checkPossibilityFirecrewCommand
            break
            ;;
        "runUpdateFromPrivserCommand --ignore_diff_properties")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py runUpdateFromPrivserCommand --ignore_diff_properties
            break
            ;;
        "--run-syncdb")
            source /home/ubuntu/Project/venv/bin/activate && cd /home/ubuntu/Project/app && python manage.py migrate --run-syncdb
            break
            ;;
        "Exit")
            echo "Exit"
            break
            ;;
        *) echo "Error: $REPLY";;
    esac
done
