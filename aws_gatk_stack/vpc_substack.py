import logging
from typing import Dict

from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_ec2 as ec2
from aws_cdk import core

log = logging.getLogger("stack")


class VpcStack(cfn.NestedStack):
    def __init__(self, scope: core.Construct, id: str, props: Dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.vpc = self.create_or_get_vpc(props)
        self.create_endpoints()

    def add_s3_gateway_endpoint(self):
        """
        Add an S3 gateway endpoint to the VPC to localize traffic
        :return:
        """
        # noinspection PyTypeChecker
        self.vpc.add_gateway_endpoint(
            "S3EndPoint", service=ec2.GatewayVpcEndpointAwsService("s3")
        )

    def add_ecr_interface_endpoint(self):
        """
        Adds an interface endpoint to ECR to keep traffic localized to the VPC
        :return:
        """
        self.vpc.add_interface_endpoint(
            "ECREndPoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

    def create_endpoints(self):
        """
        Add S3 and ECR endpoints to the VPC
        :return:
        """
        self.add_s3_gateway_endpoint()
        self.add_ecr_interface_endpoint()

    def create_vpc(self, max_azs: int = 2, nat_gateways: int = 0) -> ec2.Vpc:
        """
        Creates a new VPC in the account
        :param max_azs: The number of availablility zones
        :param nat_gateways: The number of nat gateways
        :return: The VPC
        """
        log.warning("Creating new VPC")
        return ec2.Vpc(self, "nf-batch-vpc", max_azs=max_azs, nat_gateways=nat_gateways)

    def lookup_vpc_by_tag(self, tag: str) -> ec2.Vpc:
        """
        Lookup an existing VPC
        :param tag: The name of the tag
        :return:
        """
        log.warning(f"Looking up existing VPC with tag {tag}")
        return ec2.Vpc.from_lookup(
            self,
            "nf-batch-vpc-existing",
            tags={
                "Name": tag,
            },
        )

    def create_or_get_vpc(self, props: Dict) -> ec2.Vpc:
        """
        Based on information in the props file, either create or
        lookup a VPC
        :param props: the props dicdtionary
        :return: The VPC
        """
        if props["vpc_exists"] is True:
            return self.lookup_vpc_by_tag(props["vpc_tags"]["Name"])
        else:
            return self.create_vpc()
