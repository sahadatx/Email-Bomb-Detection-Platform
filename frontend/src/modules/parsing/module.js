/**
 * Email Parsing & Normalization
 * Module 03
 *
 * Frontend module definition.
 *
 * This file provides the module metadata used by the frontend
 * application to discover and integrate the parsing feature.
 */

export const PARSING_MODULE_NAME = "parsing";

export const PARSING_MODULE_PREFIX = "/parsing";

export const PARSING_MODULE_VERSION = "1.0.0";

export const parsingModule = Object.freeze({
  name: PARSING_MODULE_NAME,

  prefix: PARSING_MODULE_PREFIX,

  version: PARSING_MODULE_VERSION,

  title: "Email Parsing & Normalization",

  description:
    "Parse, normalize and validate collected email messages.",

  routes: Object.freeze({
    workspace: "/parsing",
    email: "/parsing/emails/:emailId",
  }),

  permissions: Object.freeze({
    read: "emails:read",
    ingest: "emails:ingest",
  }),

  capabilities: Object.freeze([
    "email-listing",
    "email-parsing",
    "batch-parsing",
    "mime-analysis",
    "header-analysis",
    "address-analysis",
    "attachment-analysis",
    "validation",
  ]),
});

export default parsingModule;