MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="==BOUNDARY=="

--==BOUNDARY==
Content-Type: text/cloud-config; charset="us-ascii"

repo_update: true
repo_upgrade: all

packages:
- jq
- btrfs-progs
- sed
- wget
- git
- unzip
- lvm2
- amazon-ssm-agent
- bzip2
- ecs-init

runcmd:
- start amazon-ssm-agent
- export scratchPath=/var/lib/docker
- curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
- unzip -q /tmp/awscliv2.zip -d /tmp
- /tmp/aws/install -b /usr/bin
- mkdir -p /opt/aws-cli/bin
- cp -a $(dirname $(find /usr/local/aws-cli -name 'aws' -type f))/. /opt/aws-cli/bin/

- systemctl stop ecs
- systemctl stop docker
- cp -au /var/lib/docker /var/lib/docker.bk
- rm -rf /var/lib/docker/*
- EBS_AUTOSCALE_VERSION=$(curl --silent "https://api.github.com/repos/awslabs/amazon-ebs-autoscale/releases/latest" | jq -r .tag_name)
- cd /opt && git clone https://github.com/awslabs/amazon-ebs-autoscale.git
- cd /opt/amazon-ebs-autoscale && git checkout $EBS_AUTOSCALE_VERSION
- sh /opt/amazon-ebs-autoscale/install.sh -m $scratchPath -d /dev/sdc 2>&1 > /var/log/ebs-autoscale-install.log
- sed -i 's+OPTIONS=.*+OPTIONS="--storage-driver btrfs"+g' /etc/sysconfig/docker-storage
- cp -au /var/lib/docker.bk/* /var/lib/docker
- systemctl start docker
- systemctl enable --now --no-block ecs


--==BOUNDARY==--