import random
import string

from unittest.mock import ANY
from unittest.mock import patch
from unittest import TestCase
from cloudcrane.controllers.service_controller import ServiceController


class TestServiceController(TestCase):

    def setUp(self):
        pass

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_deploy_ecs_service(self, boto3):
        controller = ServiceController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))
        service_name = ''.join(random.choices(string.ascii_letters, k=10))
        load_balancer_scheme = 'internet-facing'
        container_port = random.randint(1, 10000)
        desired_count = random.randint(1, 100)
        target_group_arn = ''.join(random.choices(string.ascii_letters, k=10))

        parameters = {
            'containerDefinition': {
                'name': service_name,
                'image': 'example.org/repositories/' + service_name + ':latest',
                'cpu': random.randint(1, 1000),
                'memory': random.randint(1, 1000),
                'portMappings': [
                    {
                        'containerPort': container_port,
                        'hostPort': random.randint(1, 10000),
                        'protocol': 'tcp'
                    }
                ]
            },
            'desiredCount': desired_count,
            'loadBalancer': load_balancer_scheme
        }

        boto3.client().describe_target_groups.return_value = {
            'TargetGroups': [{'TargetGroupArn': target_group_arn}]
        }

        controller.deploy(cluster_name=cluster_name, service_name=service_name, region=None, parameters=parameters)

        boto3.client().register_task_definition.assert_called_with(
            family=service_name,
            taskRoleArn='',
            volumes=[],
            containerDefinitions=[parameters['containerDefinition']]
        )

        boto3.client().describe_target_groups.assert_called_with(
            Names=[cluster_name + '-' + load_balancer_scheme + '-tg']
        )

        boto3.client().create_service.assert_called_with(
            cluster=cluster_name,
            serviceName=service_name,
            taskDefinition=service_name,
            loadBalancers=[
                {
                    'targetGroupArn': target_group_arn,
                    'containerName': service_name,
                    'containerPort': container_port
                }
            ],
            desiredCount=desired_count,
            launchType='EC2'
        )

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_delete_ecs_service(self, boto3):
        controller = ServiceController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))
        service_name = ''.join(random.choices(string.ascii_letters, k=10))
        service_arn = ''.join(random.choices(string.ascii_letters, k=10))

        boto3.client().list_services.return_value = {'serviceArns': [service_arn]}
        boto3.client().describe_services.return_value = {
            'services': [{'serviceName': service_name, 'runningCount': 0}]
        }

        controller.delete(cluster_name=cluster_name, service_name=service_name)

        boto3.client().update_service.assert_called_with(
            cluster=cluster_name,
            service=service_name,
            desiredCount=0
        )

        boto3.client().delete_service.assert_called_with(
            cluster=cluster_name,
            service=service_name
        )

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_raise_exception_when_service_to_delete_is_unknown(self, boto3):
        controller = ServiceController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))
        service_name = ''.join(random.choices(string.ascii_letters, k=10))

        boto3.client().list_services.return_value = {'serviceArns': []}

        with self.assertRaisesRegex(Exception, 'Unknown service: \[{0}\]'.format(service_name)):
            controller.delete(cluster_name=cluster_name, service_name=service_name)

    @patch('cloudcrane.controllers.cluster_controller.clickclick.console')
    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_list_deployed_services_sorted_by_name(self, boto3, console):
        controller = ServiceController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))
        service1_name = ''.join(random.choices(string.ascii_letters, k=10))
        service1_arn = ''.join(random.choices(string.ascii_letters, k=10))
        service2_name = ''.join(random.choices(string.ascii_letters, k=10))
        service2_arn = ''.join(random.choices(string.ascii_letters, k=10))
        service3_name = ''.join(random.choices(string.ascii_letters, k=10))
        service3_arn = ''.join(random.choices(string.ascii_letters, k=10))

        boto3.client().list_services.return_value = {'serviceArns': [service1_arn, service2_arn, service3_arn]}
        boto3.client().describe_services.return_value = {
            'services': [
                {
                    'serviceName': service1_name,
                    'status': 'ACTIVE',
                    'runningCount': 1,
                    'desiredCount': 2
                },
                {
                    'serviceName': service2_name,
                    'status': 'PENDING',
                    'runningCount': 3,
                    'desiredCount': 4
                },
                {
                    'serviceName': service3_name,
                    'status': 'STOPPED',
                    'runningCount': 5,
                    'desiredCount': 6
                }
            ]
        }

        controller.list(cluster_name=cluster_name)

        boto3.client().list_services.assert_called_with(cluster=cluster_name)

        console.print_table.assert_called_with(
            ['service_name', 'status', 'tasks'],
            [
                {
                    'service_name': service1_name,
                    'status': 'ACTIVE',
                    'tasks': '1/2'
                },
                {
                    'service_name': service2_name,
                    'status': 'PENDING',
                    'tasks': '3/4'
                },
                {
                    'service_name': service3_name,
                    'status': 'STOPPED',
                    'tasks': '5/6'
                }
            ],
            styles=ANY,
            titles={}
        )

    @patch('cloudcrane.controllers.cluster_controller.clickclick.console')
    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_show_empty_list_when_no_services_deployed(self, boto3, console):
        controller = ServiceController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))

        boto3.client().list_services.return_value = {'serviceArns': []}

        controller.list(cluster_name=cluster_name)

        boto3.client().list_services.assert_called_with(cluster=cluster_name)
        console.print_table.assert_called_with(
            ['service_name', 'status', 'tasks'],
            [],
            styles=ANY,
            titles={}
        )
