#!/usr/bin/env python3

import boto3
import calendar
import click
import time
import yaml

from clickclick.console import print_table

from .base_template import BASE_TEMPLATE

STYLES = {
    'DELETE_COMPLETE': {'fg': 'red'},
    'DELETE_FAILED': {'fg': 'red'},
    'ROLLBACK_COMPLETE': {'fg': 'red'},
    'CREATE_COMPLETE': {'fg': 'green'},
    'CREATE_FAILED': {'fg': 'red'},
    'CREATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'DELETE_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'PENDING': {'fg': 'yellow', 'bold': True},
    'ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'ROLLBACK_FAILED': {'fg': 'red'},
    'ACTIVE': {'fg': 'green'},
    'UPDATE_COMPLETE': {'fg': 'green'},
    'UPDATE_ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_FAILED': {'fg': 'red'},
    'UPDATE_ROLLBACK_COMPLETE': {'fg': 'red'},
}

TITLES = {}


@click.group(chain=True)
def cli():
    """
    Cloudcrane's command group.
    """


@cli.command('cluster')
@click.argument('command')
@click.option('--cluster-name', default='default', help='Name of the ECS cluster (default = "default")')
@click.option('--ami', help='ID of AMI to be used for the instances of the cluster')
@click.option('--instance-type', default='t2.micro', help='EC2 instance type (default = t2.micro)')
@click.option('--max-instances', default='1', help='Maximum number of EC2 instances in auto-scaling group')
def cluster(command, cluster_name, ami, instance_type, max_instances):
    """
    Manage ECS clusters.

    Possible commands: create, list, delete
    """
    ecs = boto3.client('ecs')

    if command == 'create':
        ecs.create_cluster(clusterName=cluster_name)

        cf_parameters = dict()
        cf_parameters['EcsClusterName'] = cluster_name
        cf_parameters['EcsAmiId'] = ami
        cf_parameters['EcsInstanceType'] = instance_type
        cf_parameters['AsgMaxSize'] = max_instances
        __create_cf_stack(stack_name=cluster_name, version='1', parameters=cf_parameters)

    elif command == 'list':
        __list_stacks(all=cluster_name == 'all')

    elif command == 'delete':
        __delete_cf_stack(stack_name=cluster_name, version='1')
        ecs.delete_cluster(cluster=cluster_name)


@cli.command('service')
@click.argument('command')
@click.option('--application', help='Name of the application the AWS CloudFormation stack should be created for')
@click.option('--cluster-name', default='default', help='Name of the ECS cluster (default = "default")')
@click.option('--version', help='Version of the application the AWS CloudFormation stack should be created for')
@click.option('--region', default='eu-central-1', help='AWS region to create the new stack in')
@click.option('--parameters', default='cloudcrane.yaml',
              help='YAML file with parameters for deployment of service to ECS')
def service(command, cluster_name, application, version, region, parameters):
    """
    Manage services in ECS cluster.

    Possible commands: deploy
    """
    ecs = boto3.client('ecs')
    elb = boto3.client('elbv2')

    if version:
        service_name = application + '-' + version
    else:
        service_name = application

    if command == 'deploy':

        with open(parameters, 'rb') as f:
            parameters = yaml.load(f)

        container_definitions = list()
        container_definitions.append(parameters['containerDefinition'])

        ecs.register_task_definition(
            family=service_name,
            taskRoleArn='',
            volumes=[],
            containerDefinitions=container_definitions
        )

        target_groups = elb.describe_target_groups(Names=['default'])['TargetGroups']

        ecs.create_service(
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

    elif command == 'delete':

        service_description = __get_service_description(cluster_name=cluster_name, service_name=service_name)
        if not service_description:
            print('ERROR: Unknown service: [{0}]'.format(service_name))
            __print_usage(service)
            exit(1)

        ecs.update_service(
            cluster=cluster_name,
            service=service_name,
            desiredCount=0
        )

        running_count = 1
        while running_count > 0:
            service_description = __get_service_description(cluster_name=cluster_name, service_name=service_name)
            running_count = service_description['runningCount']
            time.sleep(1)

        ecs.delete_service(
            cluster=cluster_name,
            service=service_name
        )

    elif command == 'list':
        __list_tasks(cluster_name=cluster_name)


def __create_cf_stack(stack_name, version, parameters):
    """
    Create AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    cf_template = BASE_TEMPLATE

    cf_parameters_list = list()
    for key, value in parameters.items():
        cf_parameters_list.append({'ParameterKey': key, 'ParameterValue': value})

    cf.create_stack(
        StackName=stack_name + '-' + version,
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
                'Value': stack_name
            },
            {
                'Key': 'version',
                'Value': version
            }
        ]
    )


def __delete_cf_stack(stack_name, version):
    """
    Delete AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    cf.delete_stack(
        StackName=stack_name + '-' + version,
    )


def __list_stacks(all):
    """
    List active AWS CloudFormation stacks.
    """

    cf = boto3.client('cloudformation')

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

    response = cf.list_stacks(StackStatusFilter=stack_status_filter)
    rows = []

    for stack in response['StackSummaries']:
        rows.append({'stack_name': stack['StackName'],
                     'status': stack['StackStatus'],
                     'creation_time': calendar.timegm(stack['CreationTime'].timetuple()),
                     'description': stack['TemplateDescription']})

    rows.sort(key=lambda x: x['stack_name'])

    columns = ['stack_name', 'status', 'creation_time', 'description']
    print_table(columns, rows, styles=STYLES, titles=TITLES)


def __list_tasks(cluster_name):
    """
    List active ECS tasks.
    """
    rows = []

    for service in __get_services_in_cluster(cluster_name=cluster_name):
        rows.append({
            'service_name': service['serviceName'],
            'status': service['status'],
            'tasks': str(service['runningCount']) + '/' + str(service['desiredCount'])
        })

    rows.sort(key=lambda x: x['status'])

    columns = ['service_name', 'status', 'tasks']
    print_table(columns, rows, styles=STYLES, titles=TITLES)


def __get_services_in_cluster(cluster_name):
    """
    Get services with description of a given cluster.
    """
    ecs = boto3.client('ecs')
    services = ecs.list_services(cluster=cluster_name)
    if len(services['serviceArns']) > 0:
        services_with_description = ecs.describe_services(
            cluster=cluster_name,
            services=services['serviceArns']
        )
        return services_with_description['services']
    else:
        return []


def __get_service_description(cluster_name, service_name):
    """
    Get description of a service in a cluster.
    """
    ecs = boto3.client('ecs')
    services = ecs.list_services(cluster=cluster_name)
    if len(services['serviceArns']) > 0:
        services_with_description = ecs.describe_services(
            cluster=cluster_name,
            services=services['serviceArns']
        )
        return next(i for i in services_with_description['services'] if i['serviceName'] == service_name)
    else:
        return None


def __print_usage(command):
    """
    Print usage information (help text) of click command
    """
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def main():
    cli()


if __name__ == "__main__":
    main()
