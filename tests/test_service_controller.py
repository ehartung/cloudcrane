from unittest.mock import patch
from unittest import TestCase
from cloudcrane.controllers.service_controller import ServiceController


class TestServiceController(TestCase):

    def setUp(self):
        pass

    @patch('cloudcrane.controllers.service_controller.boto3')
    def test_should_deploy_ecs_service(self, boto3):
        controller = ServiceController()
        pass

