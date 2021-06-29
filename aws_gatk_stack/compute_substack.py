import base64
from pathlib import Path
from typing import Dict, List

from aws_cdk import aws_batch as batch
from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import core


class NfCompute(cfn.NestedStack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        vpc: ec2.Vpc,
        nf_batch_role: iam.Role,
        nf_spotfleet_role: iam.Role,
        nf_batch_instance_role: iam.Role,
        nf_instance_profile: iam.CfnInstanceProfile,
        container_image: ecs.ContainerImage,
        work_bucket: s3.Bucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        user_data = self.create_user_data()

        nf_ebs_launch_template = self.create_launch_template(user_data)

        self.create_head_compute_env(
            vpc=vpc,
            instance_profile=nf_instance_profile,
            spotfleet_role=nf_spotfleet_role,
            launch_template=nf_ebs_launch_template,
            compute_resource_type=batch.ComputeResourceType.ON_DEMAND,
            instance_types=[ec2.InstanceType("optimal")],
            ce_id="nf_head_env",
            service_role=nf_batch_role,
            batch_instance_role=nf_batch_instance_role,
            work_bucket=work_bucket,
            container_image=container_image,
        )

        for instance_class in ["m5", "c5", "r5"]:
            self.create_compute_envs(
                instance_class=instance_class,
                vpc=vpc,
                instance_profile=nf_instance_profile,
                spotfleet_role=nf_spotfleet_role,
                launch_template=nf_ebs_launch_template,
                service_role=nf_batch_role,
                batch_instance_role=nf_batch_instance_role,
                container_image=container_image,
                work_bucket=work_bucket,
            )

    @staticmethod
    def create_user_data() -> str:
        """
        Create the user_data portion of the launch template

        :return: user data file contents as a string
        """
        user_data_file = (
            Path(__file__).parent.parent / "launch_template" / "userdata_ebs.sh"
        )
        user_data = base64.b64encode(open(user_data_file).read().encode()).decode()
        return user_data

    def create_launch_template(self, user_data: str) -> ec2.CfnLaunchTemplate:
        """
        Creates the launch template for the batch jobs
        :param user_data: the userdata string
        :return: the CfnLaunchTemplate
        """
        return ec2.CfnLaunchTemplate(
            self,
            "nf-ebs-launch-template",
            launch_template_name="NfEbsLaunchTemplate",
            launch_template_data=dict(
                blockDeviceMappings=[
                    dict(
                        deviceName="/dev/xvdcz",
                        ebs=dict(
                            encrypted=True,
                            deleteOnTermination=True,
                            volumeSize=75,
                            volumeType="gp2",
                        ),
                    ),
                    dict(
                        deviceName="/dev/xvda",
                        ebs=dict(
                            deleteOnTermination=True,
                            volumeSize=50,
                            volumeType="gp2",
                        ),
                    ),
                    dict(
                        deviceName="/dev/sdc",
                        ebs=dict(
                            encrypted=True,
                            deleteOnTermination=True,
                            volumeSize=100,
                            volumeType="gp2",
                        ),
                    ),
                ],
                userData=user_data,
            ),
        )

    @staticmethod
    def create_compute_resources(
        maxv_cpus: int = 1024,
        minv_cpus: int = 0,
        desiredv_cpus: int = 0,
        *,
        vpc: ec2.Vpc,
        instance_profile: iam.CfnInstanceProfile,
        spotfleet_role: iam.Role,
        launch_template: ec2.CfnLaunchTemplate,
        compute_resource_type: batch.ComputeResourceType,
        instance_types: List[ec2.InstanceType],
    ) -> batch.ComputeResources:
        """
        Create the compute rescources for a compute environment

        :param maxv_cpus:the max number of vcpus
        :param minv_cpus: the min number of vcpus
        :param desiredv_cpus: the number of desired vcpus
        :param vpc: the VPC
        :param instance_profile: the instance profile
        :param spotfleet_role: the spotfleet role
        :param launch_template: the launch template
        :param compute_resource_type: the compute resourcce type
        :param instance_types: the list of isntance types
        :return: the batch ComputeResources
        """
        return batch.ComputeResources(
            instance_role=instance_profile.instance_profile_name,
            type=compute_resource_type,
            maxv_cpus=maxv_cpus,
            minv_cpus=minv_cpus,
            desiredv_cpus=desiredv_cpus,
            instance_types=instance_types,
            spot_fleet_role=spotfleet_role,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            launch_template=batch.LaunchTemplateSpecification(
                launch_template_name=launch_template.launch_template_name
            ),
        )

    def create_compute_environment(
        self,
        *,
        id: str,
        service_role: iam.Role,
        compute_resources: batch.ComputeResources,
    ):
        """
        Create the batch compute environment proper. We have other names in this
        code for compute environment to describe the general infrastructure for
        running batch jobs, of which this compute environment here is a part.
        :param id: the id of the CE
        :param service_role: the service role
        :param compute_resources: the batch ComputeReources
        :return: the batch ComputeEnvironment
        """
        return batch.ComputeEnvironment(
            self,
            id,
            service_role=service_role,
            compute_resources=compute_resources,
        )

    def create_head_compute_env(
        self,
        *,
        ce_id: str,
        vpc: ec2.Vpc,
        instance_profile: iam.CfnInstanceProfile,
        spotfleet_role: iam.Role,
        service_role: iam.Role,
        launch_template: ec2.CfnLaunchTemplate,
        compute_resource_type: batch.ComputeResourceType,
        instance_types: List[ec2.InstanceType],
        container_image: ecs.ContainerImage,
        work_bucket: s3.Bucket,
        batch_instance_role: iam.Role,
    ):
        """
        Creates the batch environment for the head of the nextflow deployment. This
        is the CE from which jobs are distributed
        :param ce_id: the id of the compute environment
        :param vpc: the VPC
        :param instance_profile: the instance profile
        :param spotfleet_role: the spotfleet role
        :param service_role: the service role
        :param launch_template: the launch template
        :param compute_resource_type: the type of compute resource being created
        :param instance_types: the instance types
        :param container_image: the container image used by ecs
        :param work_bucket: the bucket where work products will be stored
        :param batch_instance_role: the instance role for the batch instances
        :return:
        """
        cr = self.create_compute_resources(
            vpc=vpc,
            instance_profile=instance_profile,
            spotfleet_role=spotfleet_role,
            launch_template=launch_template,
            compute_resource_type=compute_resource_type,
            instance_types=instance_types,
        )

        ce = self.create_compute_environment(
            id=ce_id,
            service_role=service_role,
            compute_resources=cr,
        )

        jq = self.create_queue(
            instance_class="head", cr_type=compute_resource_type, ce=ce
        )
        self.create_job_definition(
            instance_class="head",
            cr_type=compute_resource_type,
            job_queue=jq,
            container_image=container_image,
            work_bucket=work_bucket,
            batch_instance_role=batch_instance_role,
        )
        return ce

    def create_queue(
        self,
        *,
        instance_class: str,
        cr_type: batch.ComputeResourceType,
        ce: batch.ComputeEnvironment,
    ) -> batch.JobQueue:
        """
        Creates a batch job queue
        :param instance_class: the name of the instance class (e.g., m5)
        :param cr_type: the type of batch compute resrouce (e.g., SPOT, ON_DEMAND)
        :param ce: the compute environment
        (e.g., spot, ondemand)
        :return: JobQueue
        """
        cr_type_name = cr_type.name.lower()
        priority = 1
        if cr_type == batch.ComputeResourceType.ON_DEMAND:
            priority = 100
        return batch.JobQueue(
            self,
            f"nf-{cr_type_name}-{instance_class}-queue",
            job_queue_name=f"Nf{cr_type_name}{instance_class}Queue",
            compute_environments=[
                batch.JobQueueComputeEnvironment(compute_environment=ce, order=0)
            ],
            priority=priority,
        )

    def create_job_definition(
        self,
        *,
        instance_class: str,
        cr_type: batch.ComputeResourceType,
        job_queue: batch.JobQueue,
        container_image: ecs.ContainerImage,
        work_bucket: s3.Bucket,
        batch_instance_role: iam.Role,
    ) -> batch.JobDefinition:
        cr_type_name = cr_type.name.lower()
        jobdef = batch.JobDefinition(
            self,
            f"nf-{cr_type_name}-{instance_class}-job",
            job_definition_name=f"Nf{cr_type_name}{instance_class}Job",
            container=batch.JobDefinitionContainer(
                image=container_image,
                vcpus=2,
                job_role=batch_instance_role,
                memory_limit_mib=1024,
                environment=dict(
                    NF_JOB_QUEUE=job_queue.job_queue_arn,
                    NF_LOGSDIR=work_bucket.s3_url_for_object(key="logs"),
                    NF_WORKDIR=work_bucket.s3_url_for_object(key="work"),
                ),
                mount_points=[
                    ecs.MountPoint(
                        container_path="/opt/aws-cli",
                        read_only=True,
                        source_volume="aws-cli",
                    ),
                ],
                volumes=[
                    ecs.Volume(
                        name="aws-cli", host=ecs.Host(source_path="/opt/aws-cli")
                    ),
                ],
            ),
        )

        return jobdef

    def create_nf_compute_env(
        self,
        *,
        vpc: ec2.Vpc,
        instance_class: str,
        instance_profile: iam.CfnInstanceProfile,
        spotfleet_role: iam.Role,
        service_role: iam.Role,
        launch_template: ec2.CfnLaunchTemplate,
        compute_resource_type: batch.ComputeResourceType,
        batch_instance_role: iam.Role,
        work_bucket: s3.Bucket,
        container_image: ecs.ContainerImage,
    ) -> batch.ComputeEnvironment:
        """
        Create the computing environment necessary for an instance class and compute
        resource type

        :param vpc: the VPC
        :param instance_class: the name of the instance class (e.g., m5)
        :param instance_profile: the instance profile
        :param spotfleet_role: the spotfleet role
        :param service_role: the service role
        :param launch_template: the launch template
        :param compute_resource_type: the compute resource type
        :param batch_instance_role: the batch instance role
        :param work_bucket: the bucke where work artifacts are stored
        :param container_image: tehe container image
        :return: the batch ComputeEnvironment
        """
        cr_type_name = compute_resource_type.name.lower()
        instance_suffixes = ["large", "xlarge", "2xlarge", "4xlarge", "8xlarge"]
        if instance_class == "c5":
            instance_suffixes = ["large", "xlarge", "2xlarge", "4xlarge", "9xlarge"]
        cr = self.create_compute_resources(
            vpc=vpc,
            instance_profile=instance_profile,
            spotfleet_role=spotfleet_role,
            launch_template=launch_template,
            compute_resource_type=compute_resource_type,
            instance_types=[
                ec2.InstanceType(f"{instance_class}.{x}") for x in instance_suffixes
            ],
        )
        ce = self.create_compute_environment(
            id=f"{instance_class}-nf-{cr_type_name}-env",
            service_role=service_role,
            compute_resources=cr,
        )
        jq = self.create_queue(
            instance_class=instance_class, cr_type=compute_resource_type, ce=ce
        )
        self.create_job_definition(
            instance_class=instance_class,
            cr_type=compute_resource_type,
            batch_instance_role=batch_instance_role,
            container_image=container_image,
            work_bucket=work_bucket,
            job_queue=jq,
        )
        return ce

    def create_compute_envs(
        self,
        *,
        vpc: ec2.Vpc,
        instance_class: str,
        instance_profile: iam.CfnInstanceProfile,
        spotfleet_role: iam.Role,
        service_role: iam.Role,
        launch_template: ec2.CfnLaunchTemplate,
        container_image: ecs.ContainerImage,
        work_bucket: s3.Bucket,
        batch_instance_role: iam.Role,
    ) -> Dict[str, batch.ComputeEnvironment]:
        """
        Create the compute environments for an instance class. This method creates
        both spot and on-demand environments, and associated infrastructure

        :param vpc: the VPC
        :param instance_class: the name of the instance class  (e.g., m5)
        :param instance_profile: the instance profile
        :param spotfleet_role: the spotfleet role
        :param service_role: the service role
        :param launch_template: the launch template
        :param container_image: the container image
        :param work_bucket: the bucket for work artificats
        :param batch_instance_role: the batch instance role
        :return: a dictionary of batch.ComputeEnvironment keyed by name of compute
        resource type (e.g., spot, demand)
        """
        envs = {}
        for k, v in dict(
            spot=batch.ComputeResourceType.SPOT,
            demand=batch.ComputeResourceType.ON_DEMAND,
        ).items():
            envs[k] = self.create_nf_compute_env(
                vpc=vpc,
                instance_class=instance_class,
                instance_profile=instance_profile,
                spotfleet_role=spotfleet_role,
                service_role=service_role,
                launch_template=launch_template,
                compute_resource_type=v,
                container_image=container_image,
                work_bucket=work_bucket,
                batch_instance_role=batch_instance_role,
            )
        return envs
