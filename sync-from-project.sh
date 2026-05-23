#!/bin/bash
set -euo pipefail

# Colors
GREEN='\033[0;32m' YELLOW='\033[0;33m' BLUE='\033[0;34m'
RED='\033[0;31m' CYAN='\033[0;36m' BOLD='\033[1m'
DIM='\033[2m' NC='\033[0m'

SKILL_CLOUD_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  echo -e "${BOLD}🔄 AI Skill Sync${NC}"
  echo -e "${DIM}Sync skills from project .kiro/skills → ai-skill-cloud${NC}"
  echo ""
  echo -e "Usage: ${CYAN}$0${NC} [--auto-approve] <project-path> [skill-name]"
  echo ""
  echo -e "Examples:"
  echo -e "  $0 ~/iac-miniapps              ${DIM}# sync all${NC}"
  echo -e "  $0 ~/iac-miniapps coding-cdk-ts ${DIM}# sync one${NC}"
  echo -e "  $0 --auto-approve ~/iac-miniapps ${DIM}# sync all without prompt${NC}"
  exit 1
}

AUTO_APPROVE=false
[[ "${1:-}" == "--auto-approve" ]] && { AUTO_APPROVE=true; shift; }

[[ $# -lt 1 ]] && usage

PROJECT_DIR="$(realpath "$1")"
SKILL_FILTER="${2:-}"
KIRO_SKILLS_DIR="$PROJECT_DIR/.kiro/skills"

if [[ ! -d "$KIRO_SKILLS_DIR" ]]; then
  echo -e "${RED}✗ Error:${NC} $KIRO_SKILLS_DIR not found"
  exit 1
fi

PROJECT_NAME="$(basename "$PROJECT_DIR")"
echo ""
echo -e "${BOLD}🔄 AI Skill Sync${NC}"
echo -e "${DIM}───────────────────────────────────────${NC}"
echo -e "  📂 Source: ${CYAN}$PROJECT_NAME/.kiro/skills${NC}"
echo -e "  ☁️  Target: ${CYAN}ai-skill-cloud${NC}"
echo -e "${DIM}───────────────────────────────────────${NC}"
echo ""

synced=0
for skill_dir in "$KIRO_SKILLS_DIR"/*/; do
  skill_name="$(basename "$skill_dir")"
  [[ -n "$SKILL_FILTER" && "$skill_name" != "$SKILL_FILTER" ]] && continue

  target_dir="$SKILL_CLOUD_DIR/$skill_name"

  if [[ ! -d "$target_dir" ]]; then
    echo -e "  ${BLUE}◆ NEW${NC}    ${BOLD}$skill_name${NC}"
    cp -r "$skill_dir" "$target_dir"
    echo -e "           ${GREEN}✓ Created${NC}"
    synced=$((synced + 1))
    continue
  fi

  if ! diff -rq "$skill_dir" "$target_dir" >/dev/null 2>&1; then
    echo -e "  ${YELLOW}● UPDATE${NC} ${BOLD}$skill_name${NC}"
    while IFS= read -r line; do
      if [[ "$line" == Files* ]]; then
        file="$(echo "$line" | sed "s|.*$skill_name/||;s| and .*||;s| differ$||")"
        echo -e "           ${DIM}~ $file${NC}"
      elif [[ "$line" == Only\ in*:* ]]; then
        dir="$(echo "$line" | sed "s|Only in ||;s|: |/|;s|.*$skill_name/||")"
        echo -e "           ${GREEN}+ $dir${NC}"
      fi
    done < <(diff -rq "$skill_dir" "$target_dir" 2>/dev/null)
    echo ""
    if [[ "$AUTO_APPROVE" == true ]]; then
      confirm="y"
    else
      read -p "           Apply? [y/N] " confirm </dev/tty
    fi
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      rsync -a --delete "$skill_dir" "$target_dir/"
      echo -e "           ${GREEN}✓ Updated${NC}"
      synced=$((synced + 1))
    else
      echo -e "           ${DIM}✗ Skipped${NC}"
    fi
  else
    echo -e "  ${GREEN}✔ OK${NC}     ${DIM}$skill_name${NC}"
  fi
done

echo ""
echo -e "${DIM}───────────────────────────────────────${NC}"
echo -e "  ${BOLD}$synced${NC} skill(s) synced ${GREEN}✓${NC}"
echo ""
