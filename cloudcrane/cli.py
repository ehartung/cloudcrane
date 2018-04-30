#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import yaml

from .controllers.cluster_controller import ClusterController
from .controllers.service_controller import ServiceController


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
    cluster_controller = ClusterController()

    if command == 'create':
        cluster_controller.create(
            cluster_name=cluster_name,
            ami=ami,
            instance_type=instance_type,
            max_instances=max_instances
        )

    elif command == 'list':
        cluster_controller.list(
            all=cluster_name == 'all'
        )

    elif command == 'delete':
        cluster_controller.delete(
            cluster_name=cluster_name
        )


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

    Possible commands: deploy, delete, list
    """
    service_controller = ServiceController()

    if version:
        service_name = application + '-' + version
    else:
        service_name = application

    if command == 'deploy':

        with open(parameters, 'rb') as f:
            service_parameters = yaml.load(f)

        service_controller.deploy(
            cluster_name=cluster_name,
            service_name=service_name,
            region=region,
            parameters=service_parameters
        )

    elif command == 'delete':
        try:
            service_controller.delete(
                cluster_name=cluster_name,
                service_name=service_name
            )
        except Exception as e:
            print('ERROR: Error deleting service [{}]: {}'.format(service_name, e))
            __print_usage(service)
            exit(1)

    elif command == 'list':
        service_controller.list(
            cluster_name=cluster_name
        )


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
