#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import time
import yaml

from abc import ABCMeta
from clickclick.console import print_table

STYLES = {
    'ACTIVE': {'fg': 'green'},
    'PENDING': {'fg': 'yellow', 'bold': True},
    'STOPPED': {'fg': 'red'},
}

TITLES = {}


class ServiceController(metaclass=ABCMeta):

    __ecs = None
    __elb = None

    def __init__(self):
        self.__ecs = boto3.client('ecs')
        self.__elb = boto3.client('elbv2')

    def deploy(self, cluster_name, service_name, region, parameters):
        """
        Deploy
        """
        with open(parameters, 'rb') as f:
            parameters = yaml.load(f)

        container_definitions = list()
        container_definitions.append(parameters['containerDefinition'])

        self.__ecs.register_task_definition(
            family=service_name,
            taskRoleArn='',
            volumes=[],
            containerDefinitions=container_definitions
        )

        target_groups = self.__elb.describe_target_groups(
            Names=[cluster_name + '-' + parameters['loadBalancer'] + '-tg']
        )['TargetGroups']

        self.__ecs.create_service(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=service_name,
            loadBalancers=[
                {
                    'targetGroupArn': target_groups[0]['TargetGroupArn'],
                    'containerName': parameters['containerDefinition']['name'],
                    'containerPort': parameters['containerDefinition']['portMappings'][0]['containerPort']
                }
            ],
            desiredCount=parameters['desiredCount'],
            launchType='EC2'
        )

    def delete(self, cluster_name, service_name):
        """
        Delete
        """
        service_description = self.__get_service_description(cluster_name=cluster_name, service_name=service_name)
        if not service_description:
            raise Exception('Unknown service: [{0}]'.format(service_name))

        self.__ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=0
        )

        running_count = 1
        while running_count > 0:
            service_description = self.__get_service_description(cluster_name=cluster_name, service_name=service_name)
            running_count = service_description['runningCount']
            time.sleep(1)

        self.__ecs.delete_service(
            cluster=cluster_name,
            service=service_name
        )

    def list(self, cluster_name):
        """
        List active ECS services.
        """
        rows = []

        for service in self.__get_services_in_cluster(cluster_name=cluster_name):
            rows.append({
                'service_name': service['serviceName'],
                'status': service['status'],
                'tasks': str(service['runningCount']) + '/' + str(service['desiredCount'])
            })

        rows.sort(key=lambda x: x['status'])

        columns = ['service_name', 'status', 'tasks']
        print_table(columns, rows, styles=STYLES, titles=TITLES)

    def __get_service_description(self, cluster_name, service_name):
        """
        Get description of a service in a cluster.
        """
        services = self.__ecs.list_services(cluster=cluster_name)
        if len(services['serviceArns']) > 0:
            services_with_description = self.__ecs.describe_services(
                cluster=cluster_name,
                services=services['serviceArns']
            )
            return next(i for i in services_with_description['services'] if i['serviceName'] == service_name)
        else:
            return None

    def __get_services_in_cluster(self, cluster_name):
        """
        Get services with description of a given cluster.
        """
        services = self.__ecs.list_services(cluster=cluster_name)
        if len(services['serviceArns']) > 0:
            services_with_description = self.__ecs.describe_services(
                cluster=cluster_name,
                services=services['serviceArns']
            )
            return services_with_description['services']
        else:
            return []
