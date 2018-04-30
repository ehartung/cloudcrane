import random
import string

from datetime import datetime
from unittest.mock import ANY
from unittest.mock import patch
from unittest import TestCase
from cloudcrane.controllers.cluster_controller import ClusterController


class TestClusterController(TestCase):

    def setUp(self):
        pass

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_create_ecs_cluster(self, boto3):
        controller = ClusterController()

        cluster_name = ''.join(random.choices(string.ascii_letters, k=10))
        ami = ''.join(random.choices(string.ascii_letters, k=10))
        instance_type = ''.join(random.choices(string.ascii_letters, k=10))
        instances = random.randint(1, 100)

        controller.create(cluster_name, ami, instance_type, instances)

        boto3.client().create_cluster.assert_called_with(clusterName=cluster_name)
        boto3.client().create_stack.assert_called_with(
            StackName=cluster_name,
            TemplateBody=ANY,
            Parameters=[
                {'ParameterKey': 'EcsClusterName', 'ParameterValue': cluster_name},
                {'ParameterKey': 'EcsAmiId', 'ParameterValue': ami},
                {'ParameterKey': 'EcsInstanceType', 'ParameterValue': instance_type},
                {'ParameterKey': 'AsgMaxSize', 'ParameterValue': instances}
            ],
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

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_delete_ecs_cluster(self, boto3):
        controller = ClusterController()

        controller.delete('test')

        boto3.client().delete_stack.assert_called_with(StackName='test')
        boto3.client().delete_cluster.assert_called_with(cluster='test')

    @patch('cloudcrane.controllers.cluster_controller.clickclick.console')
    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_list_all_ecs_clusters_sorted_by_name(self, boto3, console):
        controller = ClusterController()

        boto3.client().list_stacks.return_value = {
            'StackSummaries': [
                {
                    'StackName': 'deleted-stack',
                    'TemplateDescription': ''.join(random.choices(string.ascii_letters, k=10)),
                    'CreationTime': datetime(1970, 1, 1),
                    'StackStatus': 'DELETE_COMPLETE'
                },
                {
                    'StackName': 'active-stack',
                    'TemplateDescription': ''.join(random.choices(string.ascii_letters, k=10)),
                    'CreationTime': datetime(1970, 1, 1),
                    'StackStatus': 'CREATE_COMPLETE'
                }
            ]
        }

        controller.list(all=True)

        boto3.client().list_stacks.assert_called_with(StackStatusFilter=[])
        console.print_table.assert_called_with(
            ['cluster_name', 'status', 'creation_time', 'description'],
            [
                {
                    'cluster_name': 'active-stack',
                    'status': 'CREATE_COMPLETE',
                    'creation_time': 0,
                    'description': ANY
                },
                {
                    'cluster_name': 'deleted-stack',
                    'status': 'DELETE_COMPLETE',
                    'creation_time': 0,
                    'description': ANY
                }
            ],
            styles=ANY,
            titles={}
        )

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_filter_deleted_ecs_clusters(self, boto3):
        controller = ClusterController()

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

        controller.list(all=False)

        boto3.client().list_stacks.assert_called_with(StackStatusFilter=stack_status_filter)
