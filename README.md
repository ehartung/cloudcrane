[![Build Status](https://travis-ci.org/ehartung/cloudcrane.svg?branch=master)](https://travis-ci.org/ehartung/cloudcrane?branch=master)
[![Coverage Status](https://codecov.io/github/ehartung/cloudcrane/coverage.svg?branch=master)](https://codecov.io/github/ehartung/cloudcrane?branch=master)

# Cloudcrane
Deploy application stacks with AWS CloudFormation and Elastic Container Service (ECS)

## How to use Cloudcrane

1. Create ECS cluster in your AWS account
2. Deploy Docker image of your application to AWS ECR
3. Clone this repository and install Cloudcrane on your machine

        $ sudo python3 setup.py install

4. Create a Cloudcrane configuration file for your application (see example.yaml)
5. Create SSH key pair for your application
 
        $ aws ec2 create-key-pair --key-name my-app-ssh
 
6. Deploy your application to your AWS account

        $ cloudcrane create --application=my-app --version=1 --parameters=example.yaml
        
## List active CloudFormation stacks

        $ cloudcrane list
        
## Delete CloudFormation stack

        $ cloudcrane delete --application=my-app --version=1
        
## Connect to your Docker container
For connecting via SSH, add port 22 to security group first, then:

        $ ssh -i "my-app-ssh.pem" ec2-user@EC2_INSTANCE_URL
        $ docker exec -it CONTAINER_ID bash
