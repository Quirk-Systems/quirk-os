function typeMatches(value, type) {
  if (type === "null") return value === null;
  if (type === "array") return Array.isArray(value);
  if (type === "object") return value !== null && typeof value === "object" && !Array.isArray(value);
  if (type === "integer") return Number.isInteger(value);
  if (type === "number") return typeof value === "number" && Number.isFinite(value);
  return typeof value === type;
}

function valueKey(value) {
  return typeof value === "object" ? JSON.stringify(value) : `${typeof value}:${String(value)}`;
}

export function validateSchema(schema, value, path = "$") {
  const errors = [];
  const add = (keyword, message) => errors.push({ path, keyword, message });

  if (schema.const !== undefined && !Object.is(value, schema.const)) add("const", `must equal ${JSON.stringify(schema.const)}`);
  if (schema.enum && !schema.enum.some((item) => Object.is(item, value))) add("enum", `must be one of ${schema.enum.map(JSON.stringify).join(", ")}`);

  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => typeMatches(value, type))) {
      add("type", `must be ${types.join(" or ")}`);
      return errors;
    }
  }

  if (typeof value === "string") {
    if (schema.minLength !== undefined && value.length < schema.minLength) add("minLength", `must contain at least ${schema.minLength} characters`);
    if (schema.maxLength !== undefined && value.length > schema.maxLength) add("maxLength", `must contain no more than ${schema.maxLength} characters`);
    if (schema.pattern !== undefined && !(new RegExp(schema.pattern).test(value))) add("pattern", `must match ${schema.pattern}`);
    if (schema.format === "date-time" && !Number.isFinite(Date.parse(value))) add("format", "must be a valid date-time");
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    if (schema.minimum !== undefined && value < schema.minimum) add("minimum", `must be >= ${schema.minimum}`);
    if (schema.exclusiveMinimum !== undefined && value <= schema.exclusiveMinimum) add("exclusiveMinimum", `must be > ${schema.exclusiveMinimum}`);
    if (schema.maximum !== undefined && value > schema.maximum) add("maximum", `must be <= ${schema.maximum}`);
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) add("minItems", `must contain at least ${schema.minItems} items`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) add("maxItems", `must contain no more than ${schema.maxItems} items`);
    if (schema.uniqueItems && new Set(value.map(valueKey)).size !== value.length) add("uniqueItems", "must contain unique items");
    if (schema.items) value.forEach((item, index) => errors.push(...validateSchema(schema.items, item, `${path}[${index}]`)));
  }

  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    const properties = schema.properties ?? {};
    for (const required of schema.required ?? []) {
      if (!Object.prototype.hasOwnProperty.call(value, required)) errors.push({ path: `${path}.${required}`, keyword: "required", message: "is required" });
    }
    for (const [key, child] of Object.entries(value)) {
      if (properties[key]) errors.push(...validateSchema(properties[key], child, `${path}.${key}`));
      else if (schema.additionalProperties === false) errors.push({ path: `${path}.${key}`, keyword: "additionalProperties", message: "is not allowed" });
    }
  }

  return errors;
}

export function assertSchema(schema, value, label = "value") {
  const errors = validateSchema(schema, value);
  if (errors.length > 0) {
    const error = new Error(`${label} failed schema validation: ${errors.map((item) => `${item.path} ${item.message}`).join("; ")}`);
    error.name = "SchemaValidationError";
    error.errors = errors;
    throw error;
  }
  return value;
}
