const modules = new Map();

export function registerModule(moduleDefinition) {
  if (!moduleDefinition?.id) {
    throw new Error(
      "Module registration requires a unique module id.",
    );
  }

  if (modules.has(moduleDefinition.id)) {
    throw new Error(
      `Module '${moduleDefinition.id}' is already registered.`,
    );
  }

  modules.set(moduleDefinition.id, moduleDefinition);

  return moduleDefinition;
}

export function getModule(moduleId) {
  return modules.get(moduleId);
}

export function getRegisteredModules() {
  return Array.from(modules.values());
}

export function clearModuleRegistry() {
  modules.clear();
}