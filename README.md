
# AWS GATK Stack

Here we present a nested AWS CDK stack for deploying the necessary infrastructure 
to run [GATK](https://gatk.broadinstitute.org/hc/en-us) workflows on AWS Batch. These 
stacks provision the following components:

## Development

The following are required for developing this stack

* AWS CDK
* AWS CLIv2
* Node and npm (v12.x)
* Python 3.7
* Poetry

Requirements are handled with [poetry](https://python-poetry.org) and
[pre-commit](https://pre-commit.com/). After cloning this repo, use `poetry install` to 
set up the virtualenv, then `poetry shell` to acivate it. With the environment active, 
you can then `pre-commit install` to install the git hooks.

To install the CDK components, run `npm install` in the directory containing the 
`package.json` file. 

## Deployment

### IAM User

Deployment should be run using an IAM account with sufficient permission to perform 
the actions of this stack. To get up and running quickly this account will need 
rights to perform 

* Creation of AWS batch components (CE, Queue, etc)
* Creation of IAM roles
* VPC components (e.g., )

### Environment variables

The following environment variables are required for deployment. More info on these 
variables can be found at https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html and 
https://docs.aws.amazon.com/cdk/latest/guide/environments.html.

* `AWS_PROFILE`
* `AWS_DEFAULT_REGION`

The app will use these variables to derive CDK specific environment values needed 
for deployment.

### Bootstrap

The first time you deploy a CDK stack to your AWS account, you need to bootstrap it. 
This can be done using `npx cdk bootstrap`

### Configuration
The stack can take advantage of pre-existing VPCs or buckets if desired - configuration of these resources can be found in `props.json` 


* VPC 
  * To use an existing VPC `setvpc_exists` to `true` and provide the VPC name 
  * Otherwise set `vpc_exists` to false 
* S3 Buckets: **Bucket names must be provided**
  *This stack creates 3 buckets for use with the batch runs:
    * `work_bucket`: nextflow work bucket
    * `data_bucket`: for storage of data to be used with nextflow GATK workflows
    * `ref_bucket`: for storing common reference files
  * To use existing buckets simply set `exists` to `true` for the bucket and provide the name and ARN 
  * To create new buckets set `exists` to `false` and provide a name for the bucket. This name must be a unique name not used by any other S3 buckets.

### Deploy

It's always best to test the synthesis of the cloudformation before deployment, and 
you can do that with `npx cdk synth`. After you're satisfied with the changes, 
deployment can be executed using `npx cdk deploy`.
