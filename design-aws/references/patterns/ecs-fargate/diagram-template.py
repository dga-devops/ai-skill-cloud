# ECS Fargate Pattern — mingrammer/diagrams Template
# Install: pip install diagrams
# Render:  python diagram.py
#
# ============================================================
# DIAGRAM BEST PRACTICES (follow these when generating)
# ============================================================
#
# 1. USE NESTED CLUSTERS for layout hierarchy:
#    - Outer cluster = VPC (include name + CIDR)
#    - Inner clusters = subnet tiers (Public, Container/Private, DB)
#    - Use Cluster as SG boundary with label "sg-name\nInbound: rules"
#    - Innermost cluster = logical group (ECS Cluster)
#    This prevents overlapping text — Graphviz allocates space per cluster.
#
# 2. KEEP NODE LABELS SHORT (max 2 lines):
#    - Good: ECS("api\n:3000")
#    - Bad:  ECS("api service port 3000 path /base/api/*")
#
# 3. PUT DETAIL ON EDGE LABELS instead of node labels:
#    - Path patterns, cache policies, protocols go on Edge(label="...")
#    - Example: alb >> Edge(label="/api/*\ncaching-disabled") >> api
#
# 4. INCLUDE REAL INFRA CONTEXT in cluster labels:
#    - VPC name + CIDR: "VPC: my-shared-vpc\n10.0.0.0/16"
#    - Subnet CIDR range + AZs: "Public Subnets (10.10.0-32.0/20)\nAZ-a / AZ-b / AZ-c"
#
# 5. USE direction="TB" (top-to-bottom) for request flow diagrams.
#
# 6. ONE SERVICE PER NODE — don't combine multiple services into one icon.
#
# 7. SHOW SG AS CLUSTER BOUNDARY wrapping resources:
#    - with Cluster("sg-alb\nInbound: 443 from 0.0.0.0/0"):
#    - with Cluster("sg-ecs\nInbound: 3000,4200 from sg-alb"):
#
# 8. SHOW IAM ROLES outside VPC with dashed edges:
#    - Execution Role: all services point to it (green dashed)
#    - Task Role: only services that need AWS access (orange dashed)
#
# ============================================================

from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import ECS
from diagrams.aws.network import CloudFront, ELB, Route53
from diagrams.aws.security import WAF, IAMRole
# {{#DATABASE_ENABLED}}
from diagrams.aws.database import Aurora, RDS
# {{/DATABASE_ENABLED}}
# {{#CACHE_ENABLED}}
from diagrams.aws.database import ElastiCache
# {{/CACHE_ENABLED}}
# {{#QUEUE_ENABLED}}
from diagrams.aws.integration import SQS
# {{/QUEUE_ENABLED}}
# {{#STORAGE_ENABLED}}
from diagrams.aws.storage import S3
# {{/STORAGE_ENABLED}}

# --- Config (replace with actual values) ---
APP_NAME = "{{APP_NAME}}"
ENV = "{{ENV}}"
DOMAIN = "{{DOMAIN}}"
VPC_NAME = "{{VPC_NAME}}"
VPC_CIDR = "{{VPC_CIDR}}"
PUBLIC_SUBNET_CIDR = "{{PUBLIC_SUBNET_CIDR}}"
CONTAINER_SUBNET_CIDR = "{{CONTAINER_SUBNET_CIDR}}"
BASE_PATH = "{{BASE_PATH}}"

with Diagram(
    f"{APP_NAME} Architecture",
    show=False,
    direction="TB",
    filename=f"{APP_NAME}-architecture",
    outformat="png",
):
    # --- Edge services ---
    dns = Route53(f"Route53\n{DOMAIN}")
    cdn = CloudFront("CloudFront")
    waf = WAF("WAF\n(pre-prod/prod)")

    dns >> cdn >> waf

    # --- VPC with nested clusters + SG boundaries ---
    with Cluster(f"VPC: {VPC_NAME}\n{VPC_CIDR}"):

        with Cluster(f"Public Subnets ({PUBLIC_SUBNET_CIDR})\nAZ-a / AZ-b / AZ-c"):
            with Cluster("sg-alb\nInbound: 443 from 0.0.0.0/0"):
                alb = ELB(f"ALB\npath: {BASE_PATH}")

        with Cluster(f"Container Subnets ({CONTAINER_SUBNET_CIDR})\nAZ-a / AZ-b / AZ-c"):
            with Cluster("sg-ecs\nInbound: {{PORTS}} from sg-alb"):
                with Cluster("ECS Cluster"):
                    # {{#SERVICES}} — one node per service
                    api = ECS("{{SERVICE_1_NAME}}\n:{{SERVICE_1_PORT}}")
                    frontend = ECS("{{SERVICE_2_NAME}}\n:{{SERVICE_2_PORT}}")
                    # {{/SERVICES}}

            # {{#CACHE_ENABLED}}
            # redis = ElastiCache("Redis")
            # {{/CACHE_ENABLED}}

        # {{#DATABASE_ENABLED}}
        # with Cluster("DB Subnets"):
        #     db = Aurora("Aurora\nWriter")
        # {{/DATABASE_ENABLED}}

    # --- IAM Roles (outside VPC) ---
    exec_role = IAMRole("ecs-execution-role\nECR Pull + CW Logs")
    task_role = IAMRole("ecs-task-role\n(TBD)")

    # --- Connections (detail on edges, not nodes) ---
    waf >> alb
    alb >> Edge(label="{{SERVICE_1_PATH}}\ncaching-disabled") >> api
    alb >> Edge(label="{{SERVICE_2_PATH}}\ncaching-optimized") >> frontend

    # --- IAM Role associations ---
    api >> Edge(style="dashed", color="darkgreen", label="assumes") >> exec_role
    api >> Edge(style="dashed", color="orange", label="assumes") >> task_role
    frontend >> Edge(style="dashed", color="darkgreen") >> exec_role

    # {{#DATABASE_ENABLED}}
    # api >> Edge(color="brown", style="dashed") >> db
    # {{/DATABASE_ENABLED}}

    # {{#CACHE_ENABLED}}
    # api >> Edge(color="red", style="dashed") >> redis
    # {{/CACHE_ENABLED}}
