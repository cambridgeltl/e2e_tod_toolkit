#!/bin/bash

options=$(getopt -o c:e:n:t: --long component:,env:,name:,type: -n "$0" -- "$@")
if [ $? != 0 ]; then
    echo "Incorrect options provided"
    exit 1
fi
eval set -- "$options"

# Default values
component=""
env=""
name=""
type=""

while true; do
    case $1 in
        -c|--component)
            shift
            component=$1
            ;;
        -e|--env)
            shift
            env=$1
            ;;
        -n|--name)
            shift
            name=$1
            ;;
        -t|--type)
            shift
            type=$1
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Option -$1 requires an argument." >&2
            exit 1
            ;;
    esac
    shift
done

export MODEL_NAME=$name
export MODEL_TYPE=$type

if [[ -n $name ]]; then
    if [[ $env == "dev" && $component == "tools" ]]; then
        docker-compose -f docker-compose_het_dev.yml -p ${MODEL_NAME}_dev down && docker-compose -f docker-compose_het_dev.yml -p ${MODEL_NAME}_dev rm -f
    elif [[ $env == "prod" && $component == "tools" ]]; then
        docker-compose -f docker-compose_het_prod.yml -p ${MODEL_NAME} down && docker-compose -f docker-compose_het_prod.yml -p ${MODEL_NAME} rm -f
    elif [[ $env == "prod" && $component == "tod" && -n $type ]]; then
        docker-compose -f docker-compose_tod_prod.yml -p ${MODEL_NAME}_${MODEL_TYPE} down && docker-compose -f docker-compose_tod_prod.yml -p ${MODEL_NAME}_${MODEL_TYPE} rm -f
    else
        echo "Invalid combination of arguments. Please provide valid values for 'env' and 'component', also check your 'name' and 'type'."
    fi
else
    if [[ $component == "redis" ]]; then
        docker-compose -f docker-compose_redis.yml down
    elif [[ $component == "mongodb" ]]; then
        docker-compose -f docker-compose_mongodb.yml down
    elif [[ $component == "clean" ]]; then
        docker system prune -a -f
    else
        echo "Invalid combination of arguments. Please provide redis or mongodb."
    fi
fi