#!/usr/bin/env python3
# -*- coding: utf-8 -*-

BASE_CF_TEMPLATE = '''
AWSTemplateFormatVersion: 2010-09-09
Description: AWS CloudFormation template
Parameters:
  EcsAmiId:
    Type: String
    Description: ECS AMI Id
  EcsInstanceType:
    Type: String
    Description: ECS EC2 instance type
    Default: t2.micro
    ConstraintDescription: must be a valid EC2 instance type.
  KeyName:
    Type: String
    Description: >-
      Optional - Name of an existing EC2 KeyPair to enable SSH access to the ECS
      instances
    Default: 'ecs-ssh'
  AsgMaxSize:
    Type: Number
    Description: Maximum size and initial Desired Capacity of ECS Auto Scaling Group
    Default: '1'
  IamRoleInstanceProfile:
    Type: String
    Description: >-
      Name or the Amazon Resource Name (ARN) of the instance profile associated
      with the IAM role for the instance
    Default: ecsInstanceRole
  EcsClusterName:
    Type: String
    Description: ECS Cluster Name
    Default: default
  EcsPort:
    Type: String
    Description: >-
      Optional - Security Group port to open on ECS instances - defaults to port 80
    Default: '80'
  ElbPort:
    Type: String
    Description: >-
      Optional - Security Group port to open on ELB - port 80 will be open by
      default
    Default: '80'
  ElbHealthCheckTarget:
    Type: String
    Description: 'Optional - Health Check Target for ELB - defaults to HTTP:80/'
    Default: 'HTTP:80/'
  SourceCidr:
    Type: String
    Description: Optional - CIDR/IP range for EcsPort and ElbPort - defaults to 0.0.0.0/0
    Default: 0.0.0.0/0
  EcsEndpoint:
    Type: String
    Description: 'Optional : ECS Endpoint for the ECS Agent to connect to'
    Default: ''
  VpcAvailabilityZones:
    Type: CommaDelimitedList
    Description: >-
      Optional : Comma-delimited list of two VPC availability zones in which to create subnets
    Default: ''
  VpcCidrBlock:
    Type: String
    Description: Optional - CIDR/IP range for the VPC
    Default: 10.0.0.0/16
  SubnetCidrBlock1:
    Type: String
    Description: Optional - CIDR/IP range for the VPC
    Default: 10.0.0.0/24
  SubnetCidrBlock2:
    Type: String
    Description: Optional - CIDR/IP range for the VPC
    Default: 10.0.1.0/24
Conditions:
  SetEndpointToECSAgent: !Not
    - !Equals
      - !Ref EcsEndpoint
      - ''
  CreateEC2LCWithKeyPair: !Not
    - !Equals
      - !Ref KeyName
      - ''
  UseSpecifiedVpcAvailabilityZones: !Not
    - !Equals
      - !Join
        - ''
        - !Ref VpcAvailabilityZones
      - ''
Resources:
  Vpc:
    Type: 'AWS::EC2::VPC'
    Properties:
      CidrBlock: !Ref VpcCidrBlock
      EnableDnsSupport: 'true'
      EnableDnsHostnames: 'true'
  PubSubnetAz1:
    Type: 'AWS::EC2::Subnet'
    Properties:
      VpcId: !Ref Vpc
      CidrBlock: !Ref SubnetCidrBlock1
      AvailabilityZone: !If
        - UseSpecifiedVpcAvailabilityZones
        - !Select
          - '0'
          - !Ref VpcAvailabilityZones
        - !Select
          - '0'
          - !GetAZs
            Ref: 'AWS::Region'
  PubSubnetAz2:
    Type: 'AWS::EC2::Subnet'
    Properties:
      VpcId: !Ref Vpc
      CidrBlock: !Ref SubnetCidrBlock2
      AvailabilityZone: !If
        - UseSpecifiedVpcAvailabilityZones
        - !Select
          - '1'
          - !Ref VpcAvailabilityZones
        - !Select
          - '1'
          - !GetAZs
            Ref: 'AWS::Region'
  InternetGateway:
    Type: 'AWS::EC2::InternetGateway'
  AttachGateway:
    Type: 'AWS::EC2::VPCGatewayAttachment'
    Properties:
      VpcId: !Ref Vpc
      InternetGatewayId: !Ref InternetGateway
  RouteViaIgw:
    Type: 'AWS::EC2::RouteTable'
    Properties:
      VpcId: !Ref Vpc
  PublicRouteViaIgw:
    Type: 'AWS::EC2::Route'
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref RouteViaIgw
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
  PubSubnet1RouteTableAssociation:
    Type: 'AWS::EC2::SubnetRouteTableAssociation'
    Properties:
      SubnetId: !Ref PubSubnetAz1
      RouteTableId: !Ref RouteViaIgw
  PubSubnet2RouteTableAssociation:
    Type: 'AWS::EC2::SubnetRouteTableAssociation'
    Properties:
      SubnetId: !Ref PubSubnetAz2
      RouteTableId: !Ref RouteViaIgw
  EcsInternalSecurityGroup:
    Type: 'AWS::EC2::SecurityGroup'
    Properties:
      GroupDescription: ECS Allowed Ports
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: '1'
          ToPort: '65535'
          SourceSecurityGroupId: !Ref AlbInternalSecurityGroup
  AlbInternalSecurityGroup:
    Type: 'AWS::EC2::SecurityGroup'
    Properties:
      GroupDescription: ELB Allowed Ports
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: !Ref ElbPort
          ToPort: !Ref ElbPort
          CidrIp: !Ref SourceCidr
  InternalTargetGroup:
    Type: 'AWS::ElasticLoadBalancingV2::TargetGroup'
    Properties:
      Name: !Join
            - ''
            - - !Ref 'AWS::StackName'
              - '-internal-tg'
      VpcId: !Ref Vpc
      Port: !Ref ElbPort
      Protocol: HTTP
  EcsInternalElasticLoadBalancer:
    Type: 'AWS::ElasticLoadBalancingV2::LoadBalancer'
    Properties:
      Name: !Join
            - ''
            - - !Ref 'AWS::StackName'
              - '-internal-alb'
      SecurityGroups:
        - !Ref AlbInternalSecurityGroup
      Subnets:
        - !Ref PubSubnetAz1
        - !Ref PubSubnetAz2
      Scheme: internal
  InternalLoadBalancerListener:
    Type: 'AWS::ElasticLoadBalancingV2::Listener'
    Properties:
      LoadBalancerArn: !Ref EcsInternalElasticLoadBalancer
      Port: !Ref ElbPort
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref InternalTargetGroup
  EcsInternetFacingSecurityGroup:
    Type: 'AWS::EC2::SecurityGroup'
    Properties:
      GroupDescription: ECS Allowed Ports
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: '1'
          ToPort: '65535'
          SourceSecurityGroupId: !Ref AlbInternetFacingSecurityGroup
  AlbInternetFacingSecurityGroup:
    Type: 'AWS::EC2::SecurityGroup'
    Properties:
      GroupDescription: ELB Allowed Ports
      VpcId: !Ref Vpc
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: !Ref ElbPort
          ToPort: !Ref ElbPort
          CidrIp: !Ref SourceCidr
  InternetFacingTargetGroup:
    Type: 'AWS::ElasticLoadBalancingV2::TargetGroup'
    Properties:
      Name: !Join
            - ''
            - - !Ref 'AWS::StackName'
              - '-internet-facing-tg'
      VpcId: !Ref Vpc
      Port: !Ref ElbPort
      Protocol: HTTP
  EcsInternetFacingElasticLoadBalancer:
    Type: 'AWS::ElasticLoadBalancingV2::LoadBalancer'
    Properties:
      Name: !Join
            - ''
            - - !Ref 'AWS::StackName'
              - '-internet-facing-alb'
      SecurityGroups:
        - !Ref AlbInternetFacingSecurityGroup
      Subnets:
        - !Ref PubSubnetAz1
        - !Ref PubSubnetAz2
      Scheme: internet-facing
  InternetFacingLoadBalancerListener:
    Type: 'AWS::ElasticLoadBalancingV2::Listener'
    Properties:
      LoadBalancerArn: !Ref EcsInternetFacingElasticLoadBalancer
      Port: !Ref ElbPort
      Protocol: HTTP
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref InternetFacingTargetGroup
  EcsInstanceLc:
    Type: 'AWS::AutoScaling::LaunchConfiguration'
    Properties:
      ImageId: !Ref EcsAmiId
      InstanceType: !Ref EcsInstanceType
      AssociatePublicIpAddress: true
      IamInstanceProfile: !Ref IamRoleInstanceProfile
      KeyName: !If
        - CreateEC2LCWithKeyPair
        - !Ref KeyName
        - !Ref 'AWS::NoValue'
      SecurityGroups:
        - !Ref EcsInternalSecurityGroup
        - !Ref EcsInternetFacingSecurityGroup
      UserData: !If
        - SetEndpointToECSAgent
        - !Base64
          'Fn::Join':
            - ''
            - - |
                #!/bin/bash
              - echo ECS_CLUSTER=
              - !Ref EcsClusterName
              - ' >> /etc/ecs/ecs.config'
              - |-

                echo ECS_BACKEND_HOST=
              - !Ref EcsEndpoint
              - ' >> /etc/ecs/ecs.config'
        - !Base64
          'Fn::Join':
            - ''
            - - |
                #!/bin/bash
              - echo ECS_CLUSTER=
              - !Ref EcsClusterName
              - ' >> /etc/ecs/ecs.config'
  EcsInstanceAsg:
    Type: 'AWS::AutoScaling::AutoScalingGroup'
    Properties:
      VPCZoneIdentifier:
        - !Join
          - ','
          - - !Ref PubSubnetAz1
            - !Ref PubSubnetAz2
      LaunchConfigurationName: !Ref EcsInstanceLc
      MinSize: '0'
      MaxSize: !Ref AsgMaxSize
      DesiredCapacity: !Ref AsgMaxSize
      Tags:
        - Key: Name
          Value: !Join
            - ''
            - - 'ECS Instance - '
              - !Ref 'AWS::StackName'
          PropagateAtLaunch: 'true'
Outputs:
  EcsInstanceAsgName:
    Description: Auto Scaling Group Name for ECS Instances
    Value: !Ref EcsInstanceAsg
  EcsInternalElbName:
    Description: Internal Load Balancer for ECS Service
    Value: !Ref EcsInternalElasticLoadBalancer
  EcsInternetFacingElbName:
    Description: Internet-facing Load Balancer for ECS Service
    Value: !Ref EcsInternetFacingElasticLoadBalancer
'''
