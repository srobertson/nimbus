# copy this file to a directory and rename it to 
# nimbusfile.py

from os.path import dirname, join
import json

from  nimbus import *


with StackTemplate("CoreOS Stack"):
  Description('Launches a CoreOS cluster')

  Mapping("AWSInstanceType2Arch", {
    "t1.micro"    : { "Arch" : "64" },
    "m1.small"    : { "Arch" : "64" },
    "m1.medium"   : { "Arch" : "64" },
    "m1.large"    : { "Arch" : "64" },
    "m1.xlarge"   : { "Arch" : "64" },
    "m2.xlarge"   : { "Arch" : "64" },
    "m2.2xlarge"  : { "Arch" : "64" },
    "m2.4xlarge"  : { "Arch" : "64" },
    "c1.medium"   : { "Arch" : "64" },
    "c1.xlarge"   : { "Arch" : "64" }
  })

  Mapping("RegionMap",  {
    "ap-northeast-1" : { "AMI" : "ami-2dadfd2c" },
    "sa-east-1" : { "AMI" : "ami-0b389616" },
    "ap-southeast-2" : { "AMI" : "ami-dd83e4e7" },
    "ap-southeast-1" : { "AMI" : "ami-ac9dc4fe" },
    "us-east-1" : { "AMI" : "ami-8c4e83e4" },
    "us-west-2" : { "AMI" : "ami-2d4e371d" },
    "us-west-1" : { "AMI" : "ami-ebb9b9ae" },
    "eu-west-1" : { "AMI" : "ami-c75b8cb0" }
  })


  Parameter("InstanceType",
    Description = "EC2 instance type (m1.small, etc).",
    Type = "String",
    Default = "t1.micro",
    ConstraintDescription = "must be a valid EC2 instance type."
  )
  Parameter("ClusterSize",
    Default = "3",
    MinValue = "3",
    MaxValue = "12",
    Description = "Number of nodes in cluster (3-12).",
    Type = "Number"
  )
  Parameter("DiscoveryURL",
    Description = "An unique etcd cluster discovery URL. Grab a new token from https://discovery.etcd.io/new",
    Type = "String"
  )
  Parameter("AdvertisedIPAddress",
    Description = "Use 'private' if your etcd cluster is within one region or 'public' if it spans regions or cloud providers.",
    Default = "private",
    AllowedValues = ["private", "public"],
    Type = "String"
  )
  Parameter("AllowSSHFrom",
    Description = "The net block (CIDR) that SSH is available to.",
    Default = "0.0.0.0/0",
    Type = "String"
  )
  Parameter("KeyPair",
    Description = "The name of an EC2 Key Pair to allow SSH access to the instance.",
    Type = "String"
  )
  Parameter("VpcId",
    Type = "String",
    Description = "VpcId of your existing Virtual Private Cloud (VPC).",
    Default = "vpc-e5120087"
  )
  Parameter("Subnets",
    Type = "CommaDelimitedList",
    Description = "The list of SubnetIds where the stack will be launched"
  )



  Resource("CoreOSSecurityGroup",
    Type = "AWS::EC2::SecurityGroup",
    Properties = {
      "GroupDescription": "CoreOS SecurityGroup",
      "VpcId" : { "Ref" : "VpcId" },
      "SecurityGroupIngress": [
        {"IpProtocol": "tcp", "FromPort": "22", "ToPort": "22", "CidrIp": {"Ref": "AllowSSHFrom"}}
      ]
    }
  )
  Resource("Ingress4001",
    Type = "AWS::EC2::SecurityGroupIngress",
    Properties = {
      "GroupId": {
        "Fn::GetAtt": [
          "CoreOSSecurityGroup",
          "GroupId"
        ]
      },

      "IpProtocol": "tcp", "FromPort": "4001", "ToPort": "4001", "SourceSecurityGroupId": {
        "Fn::GetAtt" : [ "CoreOSSecurityGroup", "GroupId" ] 
      }
    }
  )
  Resource("Ingress7001",
    Type = "AWS::EC2::SecurityGroupIngress",
    Properties = {

      "GroupId": {
        "Fn::GetAtt": [
          "CoreOSSecurityGroup",
          "GroupId"
        ]
      },

      "IpProtocol": "tcp", "FromPort": "7001",
     "ToPort": "7001", "SourceSecurityGroupId": {
        "Fn::GetAtt" : [ "CoreOSSecurityGroup", "GroupId" ] 
      } 
    }
  )
  Resource("CoreOSServerAutoScale",
    Type = "AWS::AutoScaling::AutoScalingGroup",
    Properties = {
      "AvailabilityZones": {"Fn::GetAZs": "AZs"},
      "VPCZoneIdentifier" : { "Ref" : "Subnets" }, 
      "LaunchConfigurationName": {"Ref": "CoreOSServerLaunchConfig"},
      "MinSize": "3",
      "MaxSize": "12",
      "DesiredCapacity": {"Ref": "ClusterSize"},
      "Tags": [
          {"Key": "Name", "Value": { "Ref" : "AWS::StackName" }, "PropagateAtLaunch": True}
      ]
    }
  )
  Resource("CoreOSServerLaunchConfig",
    Type = "AWS::AutoScaling::LaunchConfiguration",
    Properties = {
      "ImageId" : { "Fn::FindInMap" : [ "RegionMap", { "Ref" : "AWS::Region" }, "AMI" ]},
      "InstanceType": {"Ref": "InstanceType"},
      "KeyName": {"Ref": "KeyPair"},
      "SecurityGroups": [{"Ref": "CoreOSSecurityGroup"}],
      "UserData" : "" #json.dumps(open(join(dirname(__file__),'cloud_config.yml')).read())
    }
  )

