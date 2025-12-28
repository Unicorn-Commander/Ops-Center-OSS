#!/usr/bin/env python3
"""Fix user_analytics.py with proper error handling - correctly this time"""

from pathlib import Path

filepath = Path("/home/muut/Production/UC-Cloud/services/ops-center/backend/user_analytics.py")

# Read the file
with open(filepath, 'r') as f:
    content = f.read()

# Fix 1: Change Redis URL from unicorn-redis to unicorn-lago-redis
content = content.replace(
    'REDIS_URL = "redis://unicorn-redis:6379"',
    'REDIS_URL = "redis://unicorn-lago-redis:6379"'
)

# Fix 2: Add error handling to compute_engagement
# Find the function and wrap the main logic in try/except
import re

# Pattern to match the compute_engagement function
pattern = r'(    async def compute_engagement\(\):\n)(        users = await query_keycloak_users.*?)(        return \{.*?"avg_session_duration": avg_session_duration,?\s*\})'

def replacement(match):
    func_def = match.group(1)
    func_body = match.group(2)
    return_stmt = match.group(3)

    # Add try/except around the body
    fixed = func_def
    fixed += "        try:\n"
    # Indent all body lines by 4 more spaces
    indented_body = "\n".join("    " + line if line.strip() else line
                               for line in func_body.split("\n"))
    fixed += indented_body
    fixed += "\n            "
    fixed += return_stmt.replace("        return {", "return {")
    fixed += "\n        except Exception as e:\n"
    fixed += "            logger.error(f'Error computing engagement metrics: {e}')\n"
    fixed += "            return {\n"
    fixed += "                'dau': 0,\n"
    fixed += "                'wau': 0,\n"
    fixed += "                'mau': 0,\n"
    fixed += "                'dau_mau_ratio': 0.0,\n"
    fixed += "                'wau_mau_ratio': 0.0,\n"
    fixed += "                'avg_session_duration': 0.0\n"
    fixed += "            }\n"

    return fixed

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Fix 3: Add error handling to compute_cohorts similarly
pattern_cohorts = r'(    async def compute_cohorts\(\):\n)(        users = await query_keycloak_users.*?)(        return cohort_data)'

def replacement_cohorts(match):
    func_def = match.group(1)
    func_body = match.group(2)
    return_stmt = match.group(3)

    fixed = func_def
    fixed += "        try:\n"
    indented_body = "\n".join("    " + line if line.strip() else line
                               for line in func_body.split("\n"))
    fixed += indented_body
    fixed += "\n            "
    fixed += return_stmt.replace("        return", "return")
    fixed += "\n        except Exception as e:\n"
    fixed += "            logger.error(f'Error computing cohort analysis: {e}')\n"
    fixed += "            return []\n"

    return fixed

content = re.sub(pattern_cohorts, replacement_cohorts, content, flags=re.DOTALL)

# Write the fixed content
with open(filepath, 'w') as f:
    f.write(content)

print("✅ Fixed user_analytics.py:")
print("   1. Changed Redis URL to unicorn-lago-redis")
print("   2. Added error handling to compute_engagement()")
print("   3. Added error handling to compute_cohorts()")
