#!/usr/bin/env python3
import json
import logging
import os
from pathlib import Path

import boto3
from aws_cdk import core

from aws_gatk_stack.compute_substack import NfCompute
from aws_gatk_stack.docker_substack import DockerStack
from aws_gatk_stack.iam_substack import IamStack
from aws_gatk_stack.storage_substack import StorageStack
from aws_gatk_stack.vpc_substack import VpcStack

client = boto3.client("sts")
caller_identity = client.get_caller_identity()

log = logging.getLogger("stack")
log.setLevel(logging.DEBUG)

app = core.App()

with open(Path(__file__).parent / "props.json") as f:
    props = json.load(f)

nf_gatk = core.Stack(
    app,
    "nf-gatk",
    env=core.Environment(
        account=caller_identity["Account"],
        region=os.environ["AWS_DEFAULT_REGION"],
    ),
)

vpc_substack = VpcStack(nf_gatk, "vpc-stack", props=props)

docker_substack = DockerStack(nf_gatk, "docker-stack", props=props)

storage_substack = StorageStack(
    nf_gatk, "storage-stack", vpc=vpc_substack.vpc, props=props
)

iam_substack = IamStack(
    nf_gatk,
    "iam-stack",
    work_bucket=storage_substack.work_bucket,
    data_bucket=storage_substack.data_bucket,
)

compute_substack = NfCompute(
    nf_gatk,
    "compute-stack",
    vpc=vpc_substack.vpc,
    nf_batch_role=iam_substack.nf_batch_role,
    nf_spotfleet_role=iam_substack.nf_spotfleet_role,
    nf_batch_instance_role=iam_substack.nf_batch_instance_role,
    nf_instance_profile=iam_substack.nf_instance_profile,
    container_image=docker_substack.container_image,
    work_bucket=storage_substack.work_bucket,
)


app.synth()
