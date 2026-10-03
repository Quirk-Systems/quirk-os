import { createHash } from "node:crypto";
export function canonicalize(value){if(value===null||typeof value!=="object")return JSON.stringify(value);if(Array.isArray(value))return `[${value.map(canonicalize).join(",")}]`;const entries=Object.entries(value).filter(([,item])=>item!==undefined).sort(([left],[right])=>left.localeCompare(right));return `{${entries.map(([key,item])=>`${JSON.stringify(key)}:${canonicalize(item)}`).join(",")}}`;}
export function digest(value){return `sha256:${createHash("sha256").update(canonicalize(value)).digest("hex")}`;}
