[![Build Status](https://travis-ci.org/ehartung/cloudcrane.svg?branch=master)](https://travis-ci.org/ehartung/cloudcrane?branch=master)
[![Coverage Status](https://codecov.io/github/ehartung/cloudcrane/coverage.svg?branch=master)](https://codecov.io/github/ehartung/cloudcrane?branch=master)

# Cloudcrane
Deploy application stacks with AWS CloudFormation and Elastic Container Service (ECS)

## How to use Cloudcrane

1. Deploy Docker image of your application to AWS ECR
2. Clone this repository and install Cloudcrane on your machine

        $ sudo python3 setup.py install

3. Create SSH key pair for your ECS cluster
 
        $ aws ec2 create-key-pair --key-name ecs-ssh
 
4. Create ECS cluster in your AWS account

        $ cloudcrane cluster --ami='<AMI_ID>' create

5. Create a Cloudcrane configuration file for your application (see example.yaml)
6. Deploy your application to your AWS account

        $ cloudcrane service --application=my-app --version=1 --parameters=example.yaml deploy
        
## Delete CloudFormation stack

        $ cloudcrane cluster delete
        
## Connect to your Docker container
For connecting via SSH, add port 22 to security group first, then:

        $ ssh -i "my-app-ssh.pem" ec2-user@EC2_INSTANCE_URL
        $ docker exec -it CONTAINER_ID bash
