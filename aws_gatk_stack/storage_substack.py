from pathlib import Path
from typing import Dict

from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_s3 as s3
from aws_cdk import core


class StorageStack(cfn.NestedStack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        vpc: ec2.Vpc,
        props: Dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        if props["work_bucket"]["exists"] is True:
            self.work_bucket = s3.Bucket.from_bucket_name(
                self, "work", bucket_name=props["work_bucket"]["Name"]
            )
        else:
            self.work_bucket = s3.Bucket(
                self,
                f"{props['work_bucket']['Name']}",
                bucket_name=f"{props['work_bucket']['Name']}-{self.region}",
                access_control=s3.BucketAccessControl.PRIVATE,
                block_public_access=s3.BlockPublicAccess(
                    block_public_acls=True,
                    block_public_policy=True,
                    ignore_public_acls=True,
                    restrict_public_buckets=True,
                ),
                encryption=s3.BucketEncryption.S3_MANAGED,
            )

        if props["data_bucket"]["exists"] is True:
            self.data_bucket = s3.Bucket.from_bucket_name(
                self, "data", bucket_name=props["data_bucket"]["Name"]
            )
        else:
            self.data_bucket = s3.Bucket(
                self,
                f"{props['data_bucket']['Name']}",
                bucket_name=f"{props['data_bucket']['Name']}-{self.region}",
                access_control=s3.BucketAccessControl.PRIVATE,
                block_public_access=s3.BlockPublicAccess(
                    block_public_acls=True,
                    block_public_policy=True,
                    ignore_public_acls=True,
                    restrict_public_buckets=True,
                ),
                encryption=s3.BucketEncryption.S3_MANAGED,
            )

        if props["ref_bucket"]["exists"] is True:
            self.ref_bucket = s3.Bucket.from_bucket_name(
                self, "ref", bucket_name=props["ref_bucket"]["Name"]
            )
        else:
            self.ref_bucket = s3.Bucket(
                self,
                f"{props['ref_bucket']['Name']}",
                bucket_name=f"{props['ref_bucket']['Name']}-{self.region}",
                access_control=s3.BucketAccessControl.PRIVATE,
                block_public_access=s3.BlockPublicAccess(
                    block_public_acls=True,
                    block_public_policy=True,
                    ignore_public_acls=True,
                    restrict_public_buckets=True,
                ),
                encryption=s3.BucketEncryption.S3_MANAGED,
            )

        self.nf_batch_security_group = ec2.SecurityGroup(
            self,
            "NfBatchSecurityGroup",
            security_group_name="NfBatchSecurityGroup",
            vpc=vpc,
        )
