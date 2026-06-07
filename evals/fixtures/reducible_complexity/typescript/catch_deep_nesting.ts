// suppressions.ts
function applySuppressions(groups: Group[], existing: Suppression[]) {
  const created: Suppression[] = [];
  for (const group of groups) {
    if (group.enabled) {
      if (group.rules.length > 0) {
        for (const rule of group.rules) {
          if (!existing.some((e) => e.ruleId === rule.id)) {
            created.push({ ruleId: rule.id, groupId: group.id, reason: rule.reason });
          }
        }
      }
    }
  }
  return created;
}
