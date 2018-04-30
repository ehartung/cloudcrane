#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import boto3
import calendar
import clickclick.console

from abc import ABCMeta

from cloudcrane.controllers.base_cf_template import BASE_CF_TEMPLATE

STYLES = {
    'DELETE_COMPLETE': {'fg': 'red'},
    'DELETE_FAILED': {'fg': 'red'},
    'ROLLBACK_COMPLETE': {'fg': 'red'},
    'CREATE_COMPLETE': {'fg': 'green'},
    'CREATE_FAILED': {'fg': 'red'},
    'CREATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'DELETE_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'ROLLBACK_FAILED': {'fg': 'red'},
    'UPDATE_COMPLETE': {'fg': 'green'},
    'UPDATE_ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_FAILED': {'fg': 'red'},
    'UPDATE_ROLLBACK_COMPLETE': {'fg': 'red'},
}

TITLES = {}


class ClusterController(metaclass=ABCMeta):

    __cf = None
    __ecs = None

    def __init__(self):
        self.__cf = boto3.client('cloudformation')
        self.__ecs = boto3.client('ecs')

    def create(self, cluster_name, ami, instance_type, max_instances):
        """
        Create AWS ECS cluster from an AWS CloudFormation template.
        """
        self.__ecs.create_cluster(clusterName=cluster_name)

        cf_parameters = dict()
        cf_parameters['EcsClusterName'] = cluster_name
        cf_parameters['EcsAmiId'] = ami
        cf_parameters['EcsInstanceType'] = instance_type
        cf_parameters['AsgMaxSize'] = max_instances

        cf_template = BASE_CF_TEMPLATE

        cf_parameters_list = list()
        for key, value in cf_parameters.items():
            cf_parameters_list.append({'ParameterKey': key, 'ParameterValue': value})

        self.__cf.create_stack(
            StackName=cluster_name,
            TemplateBody=cf_template,
            Parameters=cf_parameters_list,
            DisableRollback=False,
            NotificationARNs=[],
            Capabilities=[
                'CAPABILITY_IAM',
            ],
            Tags=[
                {
                    'Key': 'name',
                    'Value': cluster_name
                }
            ]
        )

    def delete(self, cluster_name):
        """
        Delete AWS ECS cluster including the corresponding AWS CloudFormation stack.
        """
        self.__cf.delete_stack(StackName=cluster_name)
        self.__ecs.delete_cluster(cluster=cluster_name)

    def list(self, all):
        """
        List active ECS clusters (AWS CloudFormation stacks).
        """

        if all:
            stack_status_filter = []
        else:
            stack_status_filter = [
                'CREATE_IN_PROGRESS',
                'CREATE_FAILED',
                'CREATE_COMPLETE',
                'ROLLBACK_IN_PROGRESS',
                'ROLLBACK_FAILED',
                'ROLLBACK_COMPLETE',
                'DELETE_IN_PROGRESS',
                'DELETE_FAILED',
                # 'DELETE_COMPLETE',
                'UPDATE_IN_PROGRESS',
                'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_COMPLETE',
                'UPDATE_ROLLBACK_IN_PROGRESS',
                'UPDATE_ROLLBACK_FAILED',
                'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_ROLLBACK_COMPLETE',
                'REVIEW_IN_PROGRESS'
            ]

        response = self.__cf.list_stacks(StackStatusFilter=stack_status_filter)
        rows = []

        for stack in response['StackSummaries']:
            rows.append({'cluster_name': stack['StackName'],
                         'status': stack['StackStatus'],
                         'creation_time': calendar.timegm(stack['CreationTime'].timetuple()),
                         'description': stack['TemplateDescription']})

        rows.sort(key=lambda x: x['cluster_name'])

        columns = ['cluster_name', 'status', 'creation_time', 'description']
        clickclick.console.print_table(columns, rows, styles=STYLES, titles=TITLES)
