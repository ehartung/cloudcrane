import io

from unittest.mock import patch
from unittest import TestCase

from cloudcrane.cli import cli


class TestCLI(TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_help_page(self, out):
        with self.assertRaises(SystemExit) as ex:
            cli(['--help'])
        output = out.getvalue()

        self.assertEqual(ex.exception.code, 0)
        self.assertIn('Cloudcrane', output)
        self.assertIn('Usage:', output)
        self.assertIn('Options:', output)
        self.assertIn('Commands:', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_help_page_for_cluster_group(self, out):
        with self.assertRaises(SystemExit) as ex:
            cli(['cluster', '--help'])
        output = out.getvalue()

        self.assertEqual(ex.exception.code, 0)
        self.assertIn('Usage:', output)
        self.assertIn('Manage ECS clusters.', output)
        self.assertIn('Possible commands: create, list, delete', output)
        self.assertIn('Options:', output)

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_execute_cluster_creation(self, boto3):
        with self.assertRaises(SystemExit) as ex:
            cli(['cluster', "--ami='ami-12345678'", 'create'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().create_stack.assert_called()

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_execute_cluster_deletion(self, boto3):
        with self.assertRaises(SystemExit) as ex:
            cli(['cluster', 'delete'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().delete_cluster.assert_called()

    @patch('cloudcrane.controllers.cluster_controller.boto3')
    def test_should_execute_cluster_list(self, boto3):
        with self.assertRaises(SystemExit) as ex:
            cli(['cluster', 'list'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().list_stacks.assert_called()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_should_return_help_page_for_service_group(self, out):
        with self.assertRaises(SystemExit) as ex:
            cli(['service', '--help'])
        output = out.getvalue()

        self.assertEqual(ex.exception.code, 0)
        self.assertIn('Usage:', output)
        self.assertIn('Manage services in ECS cluster.', output)
        self.assertIn('Possible commands: deploy, delete, list', output)
        self.assertIn('Options:', output)

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_execute_service_deployment_using_example_yaml(self, boto3):
        with self.assertRaises(SystemExit) as ex:
            cli(['service', '--application=test', '--version=1', '--parameters=example.yaml', 'deploy'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().create_service.assert_called()

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_execute_service_deletion(self, boto3):
        boto3.client().list_services.return_value = {'serviceArns': ['test-1-ARN']}
        boto3.client().describe_services.return_value = {'services': [{'serviceName': 'test-1', 'runningCount': 0}]}

        with self.assertRaises(SystemExit) as ex:
            cli(['service', '--application=test', '--version=1', 'delete'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().delete_service.assert_called()

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_execute_service_list(self, boto3):
        with self.assertRaises(SystemExit) as ex:
            cli(['service', 'list'])

        self.assertEqual(ex.exception.code, 0)
        boto3.client().list_services.assert_called()

