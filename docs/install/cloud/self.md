# Generic Linux VM - cold-agent playbook

Status: unmeasured

Spine: [CLOUD.md](../CLOUD.md). Use this playbook for any Ubuntu LTS VM that is not AWS, Azure, or GCP (a VPS, a home server, a VM the human already has). There is no provider CLI. The human, or the agent over SSH, is the only operator. Mill never stores host passwords or private keys.

This file is a skeleton. Each phase heading is the contract. Commands are not here yet. Until the status line is `measured <date>, <mill version>`, do not invent host commands. Stop and say this playbook is unmeasured.

## Account and login

Skeleton. How the human logs into the VM host. Commands are not written yet.

## Region and size

Skeleton. Pick a small Ubuntu LTS size where the host offers one. Commands are not written yet.

## Network

Skeleton. Host firewall: 443 open, 22 from the operator's current public IP only, 3306 closed. Commands are not written yet.

## VM

Skeleton. Ubuntu LTS, SSH key auth. Commands are not written yet.

## Static IP

Skeleton. Public IP that survives reboot. DNS optional. Commands are not written yet.

## Harden

Skeleton. Commands for this phase are not written yet.

## Install over SSH

Skeleton. From the workstation: `mill install cloud --ssh <user>@<host>`. The flag is the contract in [CLOUD.md](../CLOUD.md).

## Join

Skeleton. Workstation joins with the invite URL from the done-report, then `mill connect`.

## Cost and tear-down

Skeleton. Rough monthly cost and how to delete the VM and release the public IP. Commands are not written yet.

## Errors a first-timer will hit

Skeleton. Not written yet.
