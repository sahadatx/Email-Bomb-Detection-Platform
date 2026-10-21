import { moduleRegistry } from "../../core/registry/moduleRegistry";

export const EMAIL_MODULE_NAME = "emails";

export const EMAIL_MODULE_NAVIGATION = {
  section: "EMAIL SECURITY",

  items: [
    {
      label: "Emails",
      path: "/emails",
      icon: "▤",
      order: 1,
    },
  ],
};

export const EMAIL_MODULE_ROUTES = {
  emails: "/emails",
  detail: "/emails/:emailId",
};

export function registerEmailModule() {
  const existingModule =
    moduleRegistry.get(
      EMAIL_MODULE_NAME,
    );

  if (existingModule) {
    return existingModule;
  }

  return moduleRegistry.register({
    name: EMAIL_MODULE_NAME,

    navigation:
      EMAIL_MODULE_NAVIGATION,

    routes:
      EMAIL_MODULE_ROUTES,
  });
}