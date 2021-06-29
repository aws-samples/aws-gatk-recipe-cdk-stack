from pathlib import Path
from typing import Dict

from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets as assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import core


class DockerStack(cfn.NestedStack):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        *,
        props: Dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.docker_image = assets.DockerImageAsset(
            self,
            "nextflow-asset",
            directory=(str(Path(__file__).parent.parent / "docker")),
            repository_name="nextflow",
        )
        self.container_image = ecs.ContainerImage.from_docker_image_asset(
            self.docker_image
        )

        self.gatk_docker = assets.DockerImageAsset(
            self,
            "gatk-asset",
            directory=(str(Path(__file__).parent.parent / "docker_gatk")),
            repository_name="gatk",
        )
        self.gatk_container_image = ecs.ContainerImage.from_docker_image_asset(
            self.gatk_docker
        )

        self.gatk_4110_docker = assets.DockerImageAsset(
            self,
            "gatk-4110-asset",
            directory=(str(Path(__file__).parent.parent / "docker_gatk4110")),
            repository_name="gatk-4.1.1.0",
        )
        self.gatk_4110_container_image = ecs.ContainerImage.from_docker_image_asset(
            self.gatk_4110_docker
        )

        self.gotc_docker = assets.DockerImageAsset(
            self,
            "gotc-asset",
            directory=(str(Path(__file__).parent.parent / "docker_gotc")),
            repository_name="gotc",
        )
        self.gotc_container_image = ecs.ContainerImage.from_docker_image_asset(
            self.gotc_docker
        )

        self.gatk_joint_docker = assets.DockerImageAsset(
            self,
            "gatk-joint-asset",
            directory=(str(Path(__file__).parent.parent / "docker_gatk_joint")),
            repository_name="gatk-joint",
        )
        self.gatk_joint_container_image = ecs.ContainerImage.from_docker_image_asset(
            self.gatk_joint_docker
        )
