import os
import argparse
import yaml
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

# ── Environment Configurations ─────────────────────────────────
CONFIGS = {
    "dev": {
        "environment":       "DEV",
        "warehouse":         "DOW30_WAREHOUSE",
        "database":          "DOW30_DB",
        "raw_schema":        "RAW",
        "harmonized_schema": "HARMONIZED",
        "analytics_schema":  "ANALYTICS",
        "batch_size":        "100",
        "s3_prefix":         "dev/dow30",
        "aws_bucket":        os.getenv("AWS_BUCKET_NAME", "dow30-pipeline"),
        "aws_region":        os.getenv("AWS_REGION", "us-east-2"),
        "snowflake_account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "snowflake_user":    os.getenv("SNOWFLAKE_USER"),
        "snowflake_password": os.getenv("SNOWFLAKE_PASSWORD"),
        "snowflake_role":    "ACCOUNTADMIN",
        "fred_api_key":      os.getenv("FRED_API_KEY"),
    },
    "prod": {
        "environment":       "PROD",
        "warehouse":         "DOW30_WAREHOUSE",
        "database":          "DOW30_DB",
        "raw_schema":        "RAW",
        "harmonized_schema": "HARMONIZED",
        "analytics_schema":  "ANALYTICS",
        "batch_size":        "1000",
        "s3_prefix":         "prod/dow30",
        "aws_bucket":        os.getenv("AWS_BUCKET_NAME", "dow30-pipeline"),
        "aws_region":        os.getenv("AWS_REGION", "us-east-2"),
        "snowflake_account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "snowflake_user":    os.getenv("SNOWFLAKE_USER"),
        "snowflake_password": os.getenv("SNOWFLAKE_PASSWORD"),
        "snowflake_role":    "ACCOUNTADMIN",
        "fred_api_key":      os.getenv("FRED_API_KEY"),
    }
}


def render_config(env: str):
    if env not in CONFIGS:
        raise ValueError(f"Environment must be 'dev' or 'prod', got: {env}")

    # Load Jinja template
    jinja_env = Environment(loader=FileSystemLoader("jinja"))
    template  = jinja_env.get_template("config.yml.j2")

    # Render with environment values
    rendered = template.render(**CONFIGS[env])

    # Save rendered config
    output_path = f"jinja/config_{env}.yml"
    with open(output_path, "w") as f:
        f.write(rendered)

    print(f"Rendered {env.upper()} config saved to {output_path}")

    # Print summary
    config = CONFIGS[env]
    print(f"\nEnvironment : {config['environment']}")
    print(f"Database    : {config['database']}")
    print(f"Warehouse   : {config['warehouse']}")
    print(f"Batch Size  : {config['batch_size']}")
    print(f"S3 Prefix   : {config['s3_prefix']}")

    return rendered


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env",
        choices=["dev", "prod"],
        default="dev",
        help="Environment to render config for"
    )
    args = parser.parse_args()
    render_config(args.env)