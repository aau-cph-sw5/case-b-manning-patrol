/**
 * Static content of the data transparency screen, stating what the system
 * records about a steward, how long it is kept, and who can see it.
 *
 * Every fact here is an agreed rule, not data fetched at runtime: the
 * retention rule and the five-role access model are confirmed agreements, and
 * the categories mirror what the append-only event store actually inserts per
 * steward. They are collected in this one module so the screen renders content
 * and nothing else — when a rule changes, it changes here first.
 */

/** One kind of data the system stores about a steward. */
export type DataCategory = {
  /** Plain-language title shown as the card heading. */
  title: string;
  /** What is stored, in plain language rather than field names. */
  description: string;
};

/** What one role is allowed to see, in plain language. */
export type AccessRule = {
  /** Role name shown to the steward. */
  role: string;
  /** The data that role may see. */
  access: string;
};

/**
 * Retention stated for every category: data is anonymised after five years and
 * never deleted.
 */
export const RETENTION_RULE = "Anonymiseres efter 5 år. Slettes aldrig.";

/** The kinds of data stored about a steward, one card each. */
export const DATA_CATEGORIES: DataCategory[] = [
  {
    title: "Enheds-id",
    description:
      "Et unikt id, der identificerer telefonen. Alle registreringer om dig knyttes til dette id.",
  },
  {
    title: "Beaconforbindelser",
    description:
      "Hvilken beacon (perron eller forhal) du forbinder til, og hvornår du forbinder og afbryder. Tidspunkterne gemmes både fra telefonen og fra serveren.",
  },
  {
    title: "Patruljestart og patruljeslut",
    description:
      "Tidspunkterne for, hvornår din patrulje starter og stopper.",
  },
];

/**
 * Access per role, identical for every category: the split is drawn in time
 * (current shift versus history), not per kind of data.
 */
export const ACCESS_RULES: AccessRule[] = [
  {
    role: "Dig",
    access: "Dine egne data for den aktuelle vagt",
  },
  {
    role: "Tilsynsførende",
    access: "Alle data for den aktuelle vagt",
  },
  {
    role: "Kontrolrummet",
    access: "Alle data for den aktuelle vagt, alle linjer",
  },
  {
    role: "Operationsadministrator",
    access: "Alle data, inklusive historik",
  },
  {
    role: "IT-administrator",
    access: "Ingen adgang til nærværsdata",
  },
];
