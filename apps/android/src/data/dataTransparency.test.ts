// pins the transparency content: the categories mirror the event store's
// per-steward data, the retention rule is the confirmed five-year
// anonymisation with no deletion, and access follows the five-role model with
// the split drawn between current shift and history.
import { describe, expect, it } from "vitest";

import {
  ACCESS_RULES,
  DATA_CATEGORIES,
  RETENTION_RULE,
} from "@/data/dataTransparency";

describe("DATA_CATEGORIES", () => {
  it("lists the per-steward data of the event store in plain language", () => {
    expect(DATA_CATEGORIES.map((category) => category.title)).toEqual([
      "Enheds-id",
      "Beaconforbindelser",
      "Patruljestart og patruljeslut",
    ]);
  });

  it("describes every category without raw field names", () => {
    for (const category of DATA_CATEGORIES) {
      expect(category.description.trim()).not.toBe("");
      expect(category.description).not.toMatch(/android_id|beacon_id|event_type/);
    }
  });
});

describe("RETENTION_RULE", () => {
  it("states anonymisation after five years and that nothing is deleted", () => {
    expect(RETENTION_RULE).toContain("5 år");
    expect(RETENTION_RULE).toContain("aldrig");
  });
});

describe("ACCESS_RULES", () => {
  it("covers the five roles of the access model", () => {
    expect(ACCESS_RULES.map((rule) => rule.role)).toEqual([
      "Dig",
      "Tilsynsførende",
      "Kontrolrummet",
      "Operationsadministrator",
      "IT-administrator",
    ]);
  });

  it("scopes everyone but the Operations Administrator to data that is not history", () => {
    const byRole = new Map(ACCESS_RULES.map((rule) => [rule.role, rule.access]));

    expect(byRole.get("Dig")).toContain("aktuelle vagt");
    expect(byRole.get("Tilsynsførende")).toContain("aktuelle vagt");
    expect(byRole.get("Kontrolrummet")).toContain("aktuelle vagt");
    expect(byRole.get("Operationsadministrator")).toContain("historik");
    expect(byRole.get("IT-administrator")).toContain("Ingen adgang");
  });
});
