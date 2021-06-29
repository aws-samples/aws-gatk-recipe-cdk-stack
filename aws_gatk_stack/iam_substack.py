from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import core


class IamStack(cfn.NestedStack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        work_bucket: s3.Bucket,
        data_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # noinspection PyTypeChecker
        self.nf_batch_role = iam.Role(
            self,
            "nf-batch-role",
            assumed_by=iam.ServicePrincipal("batch.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSBatchServiceRole"
                )
            ],
        )

        # noinspection PyTypeChecker
        self.nf_spotfleet_role = iam.Role(
            self,
            "nf-spotfleet-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2SpotFleetTaggingRole"
                )
            ],
        )

        # noinspection PyTypeChecker
        self.nf_batch_instance_role = iam.Role(
            self,
            "nf-batch-instance-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ServicePrincipal("ecs.amazonaws.com"),
                iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            ),
            inline_policies={
                "nf-autoscale-ebs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ec2:AttachVolume",
                                "ec2:Describe*",
                                "ec2:ModifyInstanceAttribute",
                                "ec2:CreateVolume",
                                "ec2:DeleteVolume",
                                "ec2:CreateTags",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ],
                ),
                "nextflow-jobs": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "batch:DescribeJobQueues",
                                "batch:CancelJob",
                                "batch:SubmitJob",
                                "batch:ListJobs",
                                "batch:DescribeComputeEnvironments",
                                "batch:TerminateJob",
                                "batch:DescribeJobs",
                                "batch:RegisterJobDefinition",
                                "batch:DescribeJobDefinitions",
                                "ecs:DescribeContainerInstances",
                                "ecs:DescribeTasks",
                                "ec2:DescribeInstances",
                                "ec2:DescribeInstanceAttribute",
                                "ec2:DescribeInstanceTypes",
                                "ec2:DescribeInstanceStatus",
                            ],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        )
                    ],
                ),
                "nf-s3-public-data": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                "arn:aws:s3:::gatk-test-data",
                                "arn:aws:s3:::gatk-test-data/*",
                                "arn:aws:s3:::broad-references",
                                "arn:aws:s3:::broad-references/*",
                            ],
                        ),
                    ],
                ),
                "nf-bucket-access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:*"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                work_bucket.bucket_arn,
                                f"{work_bucket.bucket_arn}/*",
                            ],
                        )
                    ]
                ),
                "nf-s3-data": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                "arn:aws:s3:::gatk-test-data",
                                "arn:aws:s3:::gatk-test-data/*",
                                "arn:aws:s3:::broad-references",
                                "arn:aws:s3:::broad-references/*",
                                data_bucket.bucket_arn,
                            ],
                        ),
                    ],
                ),
            },
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2ContainerServiceforEC2Role"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonEC2RoleforSSM"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3ReadOnlyAccess"
                ),
            ],
        )

        self.nf_instance_profile = iam.CfnInstanceProfile(
            self,
            "Nf-Instance-Profile",
            roles=[self.nf_batch_instance_role.role_name],
            instance_profile_name=f"Nf-Instance-Profile-{self.region}",
        )

        # noinspection PyTypeChecker
        self.nf_job_role = iam.Role(
            self,
            "nf_job_role",
            role_name=f"nf_job_role-{self.region}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ecs-tasks.amazonaws.com")
            ),
            inline_policies={
                "nf-batch": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["batch:*"],
                            effect=iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ],
                ),
                "nf-bucket-access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:*"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                work_bucket.bucket_arn,
                                f"{work_bucket.bucket_arn}/*",
                            ],
                        )
                    ]
                ),
                "nf-s3-data": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=["s3:GetObject", "s3:ListBucket"],
                            effect=iam.Effect.ALLOW,
                            resources=[
                                "arn:aws:s3:::gatk-test-data",
                                "arn:aws:s3:::gatk-test-data/*",
                                "arn:aws:s3:::broad-references",
                                "arn:aws:s3:::broad-references/*",
                                data_bucket.bucket_arn,
                            ],
                        ),
                    ],
                ),
            },
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3ReadOnlyAccess"
                ),
            ],
        )
