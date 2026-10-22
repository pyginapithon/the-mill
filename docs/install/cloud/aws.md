# AWS - cold-agent playbook

Status: unmeasured

Spine: [CLOUD.md](../CLOUD.md). The agent uses the human's logged-in `aws` CLI, or the exact console steps this page will carry when it is written. Mill never calls AWS APIs and never stores AWS keys.

This file is a skeleton. Each phase heading is the contract. Commands are not here yet. Until the status line is `measured <date>, <mill version>`, do not invent AWS commands. Stop and say this playbook is unmeasured.

## Account and login

Skeleton. Commands for this phase are not written yet.

## Region and size

Skeleton. Commands for this phase are not written yet.

## Network

Skeleton. VPC, subnet, security group: 443 open, 22 from the operator's current public IP only, 3306 closed. Commands are not written yet.

## VM

Skeleton. Ubuntu LTS, SSH key auth. Commands are not written yet.

## Static IP

Skeleton. Public IP that survives reboot. DNS optional. Commands are not written yet.

## Harden

Skeleton. Commands for this phase are not written yet.

## Install over SSH

Skeleton. From the workstation: `mill install cloud --ssh <user>@<host>` (planned, not in this pack). The flag is the contract in [CLOUD.md](../CLOUD.md).

## Join

Skeleton. Workstation joins with the invite URL from the done-report, then `mill connect`.

## Cost and tear-down

Skeleton. Rough monthly cost and how to delete the VM and the public IP. Commands are not written yet.

## Errors a first-timer will hit

Skeleton. Not written yet.
