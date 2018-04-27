import random
import string

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

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_list_ecs_clusters(self, boto3):
        pass
