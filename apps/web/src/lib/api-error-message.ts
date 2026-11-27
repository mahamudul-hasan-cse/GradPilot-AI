type ValidationIssue = { loc?: unknown[]; msg?: string };

/**
 * Turn a FastAPI error body into text a user can act on.
 * HTTP errors send `detail` as a string; validation (422) errors send a list of issues.
 */
export function apiErrorMessage(errorBody: { detail?: unknown }, status: number): string {
  const { detail } = errorBody;

  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const issueMessages = (detail as ValidationIssue[])
      .filter((issue) => typeof issue.msg === "string")
      .map((issue) => {
        const fieldName = issue.loc?.at(-1);
        return typeof fieldName === "string" ? `${fieldName}: ${issue.msg}` : issue.msg;
      });
    if (issueMessages.length > 0) {
      return issueMessages.join("\n");
    }
  }

  return `Request failed with status ${status}`;
}
