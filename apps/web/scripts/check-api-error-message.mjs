// Checks apiErrorMessage against real FastAPI error bodies.
// Run from apps/web: node scripts/check-api-error-message.mjs  (Node 23.6+ runs the .ts import directly)
import assert from "node:assert/strict";

import { apiErrorMessage } from "../src/lib/api-error-message.ts";

const validationErrorBody = {
  detail: [
    {
      type: "value_error",
      loc: ["body", "email"],
      msg: "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.",
    },
    { type: "string_too_short", loc: ["body", "password"], msg: "String should have at least 8 characters" },
  ],
};
assert.equal(
  apiErrorMessage(validationErrorBody, 422),
  "email: value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.\n" +
    "password: String should have at least 8 characters",
);

assert.equal(apiErrorMessage({ detail: "Email already registered" }, 400), "Email already registered");

assert.equal(apiErrorMessage({}, 502), "Request failed with status 502");

console.log("apiErrorMessage: all checks passed");
